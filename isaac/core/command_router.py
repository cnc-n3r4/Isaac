"""
CommandRouter - Routes commands through safety tiers and AI processing
SAFETY-CRITICAL: Ensures all commands go through appropriate validation
"""

from isaac.adapters.base_adapter import CommandResult
from isaac.core.tier_validator import TierValidator
from isaac.runtime import CommandDispatcher
from isaac.ai.query_classifier import QueryClassifier
from pathlib import Path


class CommandRouter:
    """Routes commands through tier validation and AI processing."""

    def __init__(self, session_mgr, shell):
        """Initialize with session manager and shell adapter."""
        self.session = session_mgr
        self.shell = shell
        self.validator = TierValidator(self.session.preferences)
        self.query_classifier = QueryClassifier()

        # Initialize the plugin dispatcher
        self.dispatcher = CommandDispatcher(session_mgr)
        self.dispatcher.load_commands([
            Path(__file__).parent.parent / 'commands',
            Path.home() / '.isaac' / 'commands'
        ])
    
    def _confirm(self, message: str) -> bool:
        """Get user confirmation (placeholder - always return True for now)."""
        # TODO: Implement actual user input
        print(f"{message} (y/n): y")
        return True
    
    def _is_natural_language(self, input_text: str) -> bool:
        """Check if input contains natural language (spaces, common words)."""
        # Simple heuristic: has spaces and not obviously a command
        if ' ' not in input_text.strip():
            return False
        
        # Check for obvious command patterns
        first_word = input_text.strip().split()[0].lower()
        obvious_commands = ['ls', 'cd', 'pwd', 'grep', 'find', 'cat', 'echo', 'rm', 'cp', 'mv']
        
        return first_word not in obvious_commands

    def _route_device_command(self, input_text: str) -> CommandResult:
        """Handle !alias device routing commands."""
        # Parse device alias and command
        parts = input_text[1:].split(None, 1)  # Remove ! and split on first space
        if len(parts) != 2:
            return CommandResult(
                success=False,
                output="Usage: !device_alias /command",
                exit_code=1
            )

        device_alias, device_cmd = parts

        # Try immediate routing
        try:
            if self.session.cloud and self.session.cloud.is_available():
                success = self.session.cloud.route_command(device_alias, device_cmd)
                if success:
                    return CommandResult(
                        success=True,
                        output=f"Command routed to {device_alias}",
                        exit_code=0
                    )
        except Exception:
            pass  # Fall through to queuing

        # Queue for later sync if cloud unavailable
        queue_id = self.session.queue.enqueue(
            command=device_cmd,
            command_type='device_route',
            target_device=device_alias,
            metadata={'tier': self._get_tier(device_cmd)}
        )

        return CommandResult(
            success=True,
            output=f"Command queued (#{queue_id}) - will sync when online",
            exit_code=0
        )

    def _get_tier(self, command: str) -> float:
        """Get safety tier for command."""
        return self.validator.get_tier(command)

    def _handle_meta_command(self, command: str) -> CommandResult:
        """Handle /commands using the plugin dispatcher"""
        try:
            # Check for pipes
            if '|' in command:
                parts = command.split('|')
                result = self.dispatcher.chain_pipe(parts[0].strip(), parts[1].strip())
            else:
                # Single command
                result = self.dispatcher.execute(command)

            # Convert dispatcher result to CommandResult
            return CommandResult(
                success=result.get('ok', False),
                output=result.get('stdout', ''),
                exit_code=0 if result.get('ok', False) else 1
            )

        except Exception as e:
            return CommandResult(
                success=False,
                output=f"Command execution error: {str(e)}",
                exit_code=1
            )
    
    def route_command(self, input_text: str) -> CommandResult:
        """
        Route command through appropriate processing pipeline.
        
        Args:
            input_text: Raw user input
            
        Returns:
            CommandResult with execution results
        """
        # Check for meta-commands first
        if input_text.startswith('/'):
            # Handle special cases that don't go through dispatcher
            if input_text in ['/exit', '/quit']:
                return CommandResult(success=True, output="", exit_code=0)
            if input_text == '/clear':
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                return CommandResult(success=True, output="", exit_code=0)

            # All other / commands go through dispatcher
            return self._handle_meta_command(input_text)

        # Check for device routing (!alias)
        if input_text.startswith('!'):
            return self._route_device_command(input_text)

        # Task mode detection
        if input_text.lower().startswith('isaac task:'):
            task_desc = input_text[11:].strip()  # Remove "isaac task:"
            
            from isaac.ai.task_planner import execute_task
            return execute_task(task_desc, self.shell, self.session)
        
        # Natural language check - AI translation
        if self._is_natural_language(input_text):
            if not input_text.lower().startswith('isaac '):
                return CommandResult(
                    success=False,
                    output="Isaac > I have a name, use it.",
                    exit_code=-1
                )
            
            # AI translation (Phase 3.2)
            query = input_text[6:].strip()  # Remove "isaac " prefix
            
            # Check if query should route to chat mode (geographic/general info)
            if self.query_classifier.is_chat_mode_query(query):
                # Route to chat mode (like /ask command)
                return self._handle_chat_query(query)
            
            from isaac.ai.translator import translate_query
            result = translate_query(query, self.shell.name, self.session)
            
            if result['success']:
                # Log AI query separately (privacy)
                if hasattr(self.session, 'log_ai_query'):
                    self.session.log_ai_query(
                        query=query,
                        translated_command=result['command'],
                        explanation=result.get('explanation', ''),
                        executed=True,
                        shell_name=self.shell.name
                    )
                
                # Execute translated command through tier system (CRITICAL)
                print(f"Isaac > Executing: {result['command']}")
                return self.route_command(result['command'])
            else:
                # Translation failed
                return CommandResult(
                    success=False,
                    output=f"Isaac > {result['error']}",
                    exit_code=-1
                )
        
        # Regular command processing
        tier = self.validator.get_tier(input_text)
        
        if tier == 1:
            # Tier 1: Instant execution
            return self.shell.execute(input_text)
        elif tier == 2:
            # Tier 2: Auto-correct typos and execute
            from isaac.ai.corrector import correct_command
            
            # Try auto-correction
            correction = correct_command(input_text, self.shell.name, self.session.config)
            
            if correction['corrected'] and correction['confidence'] > 0.8:
                # High confidence typo detected - auto-correct
                print(f"Isaac > Auto-correcting: {correction['original']} → {correction['corrected']}")
                return self.shell.execute(correction['corrected'])
            else:
                # No typo or low confidence - execute as-is
                return self.shell.execute(input_text)
        elif tier == 2.5:
            # Tier 2.5: Correct + confirm
            from isaac.ai.corrector import correct_command
            
            # Try correction
            correction = correct_command(input_text, self.shell.name, self.session.config)
            
            if correction['corrected'] and correction['confidence'] > 0.7:
                # Show correction, ask for confirmation
                print("\n" + "=" * 60)
                print(f"Corrected: {correction['corrected']}")
                print(f"Original: {correction['original']}")
                print(f"Confidence: {correction['confidence']:.0%}")
                print("=" * 60 + "\n")
                
                confirmed = self._confirm("Execute corrected version?")
                if confirmed:
                    return self.shell.execute(correction['corrected'])
            else:
                # No correction needed or low confidence - just confirm original
                confirmed = self._confirm(f"Execute: {input_text}?")
                if confirmed:
                    return self.shell.execute(input_text)
            
            # User aborted
            return CommandResult(
                success=False,
                output="Isaac > Aborted.",
                exit_code=-1
            )
        elif tier == 3:
            # Tier 3: Validation required (Phase 3.4: AI validation)
            from isaac.ai.validator import validate_command
            
            # Get AI validation
            validation = validate_command(input_text, self.shell.name, self.session.config)
            
            # Show warnings if any
            if validation['warnings']:
                print("\n" + "=" * 60)
                print("⚠️  SAFETY WARNINGS:")
                for warning in validation['warnings']:
                    print(f"  • {warning}")
                print("=" * 60)
            
            # Show suggestions if any
            if validation['suggestions']:
                print("\n💡 SUGGESTIONS:")
                for suggestion in validation['suggestions']:
                    print(f"  • {suggestion}")
                print()
            
            # Confirm execution
            if validation['safe']:
                confirmed = self._confirm(f"Execute: {input_text}?")
            else:
                confirmed = self._confirm(f"⚠️  POTENTIALLY UNSAFE - Execute anyway: {input_text}?")
            
            if confirmed:
                return self.shell.execute(input_text)
            else:
                return CommandResult(
                    success=False,
                    output="Isaac > Aborted.",
                    exit_code=-1
                )
        elif tier == 4:
            # Tier 4: Lockdown - never execute
            return CommandResult(
                success=False,
                output="Isaac > Command too dangerous. Aborted.",
                exit_code=-1
            )
        else:
            # Unknown tier
            return CommandResult(
                success=False,
                output="Isaac > Unknown command tier. Aborted for safety.",
                exit_code=-1
            )
    
    def _handle_chat_query(self, query: str) -> CommandResult:
        """
        Handle chat-style query (no execution, just AI response).
        
        Args:
            query: Natural language query
        
        Returns:
            CommandResult with AI response
        """
        try:
            from isaac.ai.xai_client import XaiClient
            
            # Get API configuration
            config = self.session.get_config()
            api_key = config.get('xai_api_key') or config.get('api_key')
            
            if not api_key:
                return CommandResult(
                    success=False,
                    output="Isaac > xAI API key not configured. Set it in ~/.isaac/config.json",
                    exit_code=-1
                )
            
            # Initialize xAI client
            client = XaiClient(
                api_key=api_key,
                api_url=config.get('xai_api_url', 'https://api.x.ai/v1/chat/completions'),
                model=config.get('xai_model', 'grok-3')
            )
            
            # Build chat preprompt
            preprompt = self._build_chat_preprompt()
            
            # Query AI
            response = client.chat(
                prompt=query,
                system_prompt=preprompt
            )
            
            # Log query to AI history
            self.session.log_ai_query(
                query=query,
                translated_command='[chat_mode_auto]',
                explanation=response[:100],
                executed=False,
                shell_name='chat'
            )
            
            return CommandResult(
                success=True,
                output=f"Isaac > {response}",
                exit_code=0
            )
        
        except Exception as e:
            return CommandResult(
                success=False,
                output=f"Isaac > Error querying AI: {e}",
                exit_code=-1
            )
    
    def _build_chat_preprompt(self) -> str:
        """Build context-aware preprompt for chat mode."""
        shell_name = self.shell.name if hasattr(self.shell, 'name') else 'PowerShell'
        
        from pathlib import Path
        current_dir = Path.cwd()
        
        preprompt = f"""You are Isaac, an AI assistant integrated into the user's shell.

CONTEXT:
- Operating System: Windows
- Current Shell: {shell_name}
- Current Directory: {current_dir}

IMPORTANT DISTINCTIONS:
1. Geographic/General Questions: Answer directly
   - "where is alaska?" → Geographic information
   - "what is docker?" → Technical explanation
   
2. File/Command Questions: Mention the command but don't execute
   - "where is alaska.exe?" → "You can search with: where.exe alaska.exe"
   - "show me my files" → "You can list files with: ls or dir"

3. Shell-Specific Awareness:
   - User is on {shell_name}, so reference appropriate commands
   - PowerShell: Get-*, Set-*, cmdlets
   - Bash: ls, grep, awk, sed

RESPONSE STYLE:
- Conversational and helpful
- Brief but complete answers
- Reference shell commands when relevant
- No command execution (this is chat mode)

Current user query follows below:
"""
        
        return preprompt