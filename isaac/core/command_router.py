"""
CommandRouter - Routes commands through safety tiers and AI processing
SAFETY-CRITICAL: Ensures all commands go through appropriate validation
"""

from isaac.adapters.base_adapter import CommandResult
from isaac.core.tier_validator import TierValidator
from isaac.core.sandbox_enforcer import SandboxEnforcer
from isaac.core.random_replies import get_reply_generator
from isaac.runtime import CommandDispatcher
from isaac.ai.query_classifier import QueryClassifier
from pathlib import Path
from typing import Optional, Dict, List, Any
import shlex


class CommandRouter:
    """Routes commands through tier validation and AI processing."""

    def __init__(self, session_mgr, shell):
        """Initialize with session manager and shell adapter."""
        self.session = session_mgr
        self.shell = shell
        
        # Initialize security and validation components
        self.validator = TierValidator(self.session.preferences)
        self.query_classifier = QueryClassifier()
        self.sandbox = SandboxEnforcer(self.session)

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
        obvious_commands = [
            'ls', 'cd', 'pwd', 'grep', 'find', 'cat', 'echo', 'rm', 'cp', 'mv',
            'head', 'tail', 'wc', 'ps', 'kill', 'mkdir', 'touch', 'which'
        ]
        
        return first_word not in obvious_commands

    def _is_quoted_pipe(self, cmd: str) -> bool:
        """Check if all pipes are inside quotes."""
        in_quotes = False
        quote_char = None
        
        for char in cmd:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
            elif char == '|' and not in_quotes:
                return False  # Found pipe outside quotes
        
        return True  # All pipes are quoted

    def _is_obviously_invalid_command(self, command: str) -> bool:
        """
        Check if command is obviously invalid and should be rejected immediately.
        
        This catches commands that are clearly not valid shell commands before
        they reach the tier validation system.
        """
        # Extract base command (first word)
        parts = command.strip().split()
        if not parts:
            return True  # Empty command
        
        base_cmd = parts[0]
        base_cmd_lower = base_cmd.lower()
        
        # Two character commands that are repeated letters (like 'ss', 'xx', 'zz')
        if len(base_cmd_lower) == 2 and base_cmd_lower[0] == base_cmd_lower[1]:
            return True  # Commands like 'ss', 'xx', 'zz', 'aa', etc.
        
        # Commands that are clearly keyboard mashing or nonsense
        if len(base_cmd_lower) >= 3:
            invalid_patterns = [
                r'^[qwer]+$',        # Just QWERTY row
                r'^[asdf]+$',        # Just ASDF row  
                r'^[zxcv]+$',        # Just ZXCV row
                r'^[yuiop]+$',       # Just YUIOP row
                r'^[hjkl]+$',        # Just HJKL row
                r'^[nm]+$',          # Just NM
                r'^[1234567890]+$',  # Just numbers
            ]
            
            import re
            for pattern in invalid_patterns:
                if re.match(pattern, base_cmd_lower):
                    return True
            
            # Additional heuristics for obviously invalid commands
            
            # 1. Mixed case patterns that don't follow programming identifier conventions
            if base_cmd != base_cmd_lower and base_cmd != base_cmd_lower.capitalize():
                has_upper = any(c.isupper() for c in base_cmd)
                has_lower = any(c.islower() for c in base_cmd)
                if has_upper and has_lower:
                    # Valid patterns: PascalCase (MyCommand), camelCase (myCommand), kebab-case (my-command), snake_case (my_command)
                    # Invalid: rvcQREc, MyCoMmAnD, mYcOmMaNd
                    
                    # If it has separators, it's probably valid
                    if any(sep in base_cmd for sep in ['-', '_']):
                        pass  # Skip to next check
                    else:
                        # For no separators, check if capitals appear at word boundaries
                        # In valid identifiers, capitals typically follow lowercase letters (word boundaries)
                        valid_capital_pattern = True
                        for i, char in enumerate(base_cmd):
                            if char.isupper():
                                # Capital should be preceded by a lowercase letter (or be at start for PascalCase)
                                if i > 0 and not base_cmd[i-1].islower():
                                    # If preceded by uppercase or non-letter, might be invalid
                                    if base_cmd[i-1].isupper() or not base_cmd[i-1].isalpha():
                                        valid_capital_pattern = False
                                        break
                        
                        if not valid_capital_pattern:
                            return True
            
            # 2. Very long commands that look random
            if len(base_cmd) > 15:
                # Check for high entropy (many different characters)
                unique_chars = len(set(base_cmd_lower))
                entropy_ratio = unique_chars / len(base_cmd)
                if entropy_ratio >= 0.6:  # 60% unique chars in long command
                    return True
            
            # 3. Commands with unusual character distributions
            if len(base_cmd) >= 6:
                vowels = sum(1 for c in base_cmd_lower if c in 'aeiouy')
                consonants = len(base_cmd) - vowels
                # Extremely unbalanced vowel/consonant ratios, but not for short commands
                if len(base_cmd) >= 8 and (consonants > vowels * 3 or vowels > consonants * 3):
                    return True
        
        return False

    def parse_command_flags(self, args: List[str]) -> Dict[str, Any]:
        """Parse command arguments using standardized -/-- flag syntax.
        
        Supports:
        - --flag value
        - --flag=value  
        - -f value
        - -f=value
        - --flag (boolean flags)
        
        Returns dict with parsed flags and remaining positional args.
        """
        parsed = {}
        positional = []
        i = 0
        
        while i < len(args):
            arg = args[i]
            
            # Check if it's a flag (starts with -)
            if arg.startswith('--'):
                # Long flag like --flag or --flag=value
                if '=' in arg:
                    flag, value = arg.split('=', 1)
                    flag = flag[2:]  # Remove --
                    parsed[flag] = value
                else:
                    flag = arg[2:]  # Remove --
                    # Check if next arg is the value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        parsed[flag] = args[i + 1]
                        i += 1  # Skip the value
                    else:
                        parsed[flag] = True  # Boolean flag
                        
            elif arg.startswith('-') and len(arg) > 1:
                # Short flag like -f or -f=value
                if '=' in arg:
                    flag, value = arg.split('=', 1)
                    flag = flag[1:]  # Remove -
                    parsed[flag] = value
                else:
                    flag = arg[1:]  # Remove -
                    # Check if next arg is the value
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        parsed[flag] = args[i + 1]
                        i += 1  # Skip the value
                    else:
                        parsed[flag] = True  # Boolean flag
            else:
                # Positional argument
                positional.append(arg)
                
            i += 1
            
        return {
            'flags': parsed,
            'positional': positional
        }

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

    def _handle_meta_command(self, input_text: str) -> CommandResult:
        """Handle meta-commands through the plugin dispatcher."""
        try:
            # Dispatch command through plugin system
            result_blob = self.dispatcher.execute(input_text)
            
            # Convert dispatcher result to CommandResult
            if result_blob.get('ok', False):
                # Success - extract stdout
                output = result_blob.get('stdout', '')
                result = CommandResult(success=True, output=output, exit_code=0)
                
                # Check if this was a state-changing command that modifies config
                # These commands save to disk but don't update session manager's in-memory config
                state_changing_commands = [
                    '/mine --claim', '/mine claim', '/mine --use', '/mine use',
                    '/mine --nuggets save', '/mine nuggets save'
                ]
                
                if any(input_text.startswith(cmd) for cmd in state_changing_commands):
                    # Reload config to pick up changes made by the command
                    self.session.reload_config()
                
                return result
            else:
                # Error - extract error message
                error_info = result_blob.get('error', {})
                error_msg = error_info.get('message', 'Unknown error')
                return CommandResult(success=False, output=error_msg, exit_code=1)
                
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
        # Check for pipe operator (not in quotes)
        if '|' in input_text and not self._is_quoted_pipe(input_text):
            from isaac.core.pipe_engine import PipeEngine
            engine = PipeEngine(self.session, self.shell)
            result_blob = engine.execute_pipeline(input_text)
            
            # Convert blob to CommandResult
            if result_blob['kind'] == 'error':
                return CommandResult(success=False, output=result_blob['content'], exit_code=1)
            else:
                return CommandResult(success=True, output=result_blob['content'], exit_code=0)
        
        # Enforce / prefix for exit commands
        if input_text.strip().lower() in ['exit', 'quit']:
            return CommandResult(
                success=False,
                output="Isaac > Use /exit or /quit to exit Isaac",
                exit_code=1
            )
        
        # Handle cd (change directory) specially - must change Isaac's working directory
        import os
        if input_text.strip().startswith('cd ') or input_text.strip() == 'cd':
            parts = input_text.strip().split(maxsplit=1)
            if len(parts) == 1:
                # Just 'cd' - go to home directory
                target = str(Path.home())
            else:
                target = parts[1].strip('"').strip("'")  # Remove quotes
                # Expand ~ and environment variables
                target = os.path.expanduser(target)
                target = os.path.expandvars(target)
            
            try:
                os.chdir(target)
                new_dir = os.getcwd()
                return CommandResult(success=True, output=new_dir, exit_code=0)
            except Exception as e:
                return CommandResult(success=False, output=f"cd: {e}", exit_code=1)
        
        # Check for force execution prefix (/f or /force)
        if input_text.startswith('/f ') or input_text.startswith('/force '):
            # Extract actual command (skip /f or /force prefix)
            if input_text.startswith('/f '):
                actual_command = input_text[3:]  # Skip '/f '
            else:
                actual_command = input_text[7:]  # Skip '/force '
            
            # Enforce sandbox rules even for force execution
            sandbox_result = self._enforce_sandbox(actual_command)
            if sandbox_result is None:
                return CommandResult(
                    success=False,
                    output="Isaac > Command blocked by sandbox policy (even in force mode)",
                    exit_code=1
                )
            
            print(f"Isaac > Force executing (bypassing AI validation): {sandbox_result}")
            return self.shell.execute(sandbox_result)
        
        # Check for meta-commands first
        if input_text.startswith('/'):
            # Handle special cases that don't go through dispatcher
            if input_text in ['/exit', '/quit']:
                return CommandResult(success=True, output="", exit_code=0)
            if input_text == '/clear':
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                return CommandResult(success=True, output="", exit_code=0)
            if input_text == '/config console':
                # Launch the config console TUI
                from isaac.ui.config_console import show_config_console
                message = show_config_console(self.session)
                return CommandResult(success=True, output=message, exit_code=0)

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
                reply_gen = get_reply_generator(self.session.config)
                return CommandResult(
                    success=False,
                    output=f"Isaac > {reply_gen.get_prefix_required_reply()}",
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
        # First enforce sandbox rules
        sandbox_result = self._enforce_sandbox(input_text)
        if sandbox_result is None:
            return CommandResult(
                success=False,
                output="Isaac > Command blocked by sandbox policy",
                exit_code=1
            )

        # Pre-validate for obviously invalid commands before execution
        if self._is_obviously_invalid_command(sandbox_result):
            reply_gen = get_reply_generator(self.session.config)
            return CommandResult(
                success=False,
                output=f"Isaac > {reply_gen.get_command_failed_reply()}",
                exit_code=1
            )

        # Execute command (use sandbox-validated command if modified)
        result = self.shell.execute(sandbox_result)
        if result.success:
            return result
        
        # Command not found - check Unix alias table (Windows only)
        if self._is_windows() and self._unix_aliases_enabled():
            translated = self._try_unix_alias_translation(sandbox_result)
            if translated:
                if self._show_translated_command():
                    print(f"[Translated: {translated}]")
                result = self.shell.execute(translated)
                if result.success:
                    return result
        
        # Fall back to tier system for safety validation
        tier = self.validator.get_tier(sandbox_result)
        
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
            
            # Get API configuration - use chat API key
            config = self.session.get_config()
            xai_config = config.get('xai', {})
            chat_config = xai_config.get('chat', {})
            api_key = chat_config.get('api_key') or config.get('xai_api_key') or config.get('api_key')
            
            if not api_key:
                return CommandResult(
                    success=False,
                    output="Isaac > xAI Chat API key not configured. Set it in ~/.isaac/config.json under xai.chat.api_key",
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
            
            # Query AI with streaming
            try:
                response_chunks = client.chat_stream(
                    prompt=query,
                    system_prompt=preprompt
                )
                
                # Collect all chunks into complete response
                response = ""
                for chunk in response_chunks:
                    response += chunk
                
            except Exception as e:
                response = f"Error: {e}"
            
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
    
    def _is_windows(self) -> bool:
        """Check if running on Windows"""
        import platform
        return platform.system() == 'Windows'
    
    def _unix_aliases_enabled(self) -> bool:
        """Check if Unix alias translation is enabled"""
        return self.session.config.get('enable_unix_aliases', True)
    
    def _show_translated_command(self) -> bool:
        """Check if translated commands should be shown"""
        return self.session.config.get('show_translated_command', True)

    def _enforce_sandbox(self, command: str) -> Optional[str]:
        """Enforce sandbox rules on command. Returns validated command or None if blocked."""
        if not self.sandbox.is_sandbox_enabled():
            return command

        # Enforce command validation
        validated_command = self.sandbox.enforce_command(command)
        if validated_command is None:
            return None

        return validated_command
    
    def _try_unix_alias_translation(self, command: str) -> Optional[str]:
        """Try to translate Unix command to PowerShell"""
        from isaac.core.unix_aliases import UnixAliasTranslator
        
        if not hasattr(self, '_unix_translator'):
            self._unix_translator = UnixAliasTranslator()
        
        return self._unix_translator.translate(command)