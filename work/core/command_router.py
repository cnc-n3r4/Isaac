"""
CommandRouter - Routes commands through safety tiers and AI processing
SAFETY-CRITICAL: Ensures all commands go through appropriate validation
"""

from isaac.adapters.base_adapter import CommandResult
from isaac.core.tier_validator import TierValidator


class CommandRouter:
    """Routes commands through tier validation and AI processing."""
    
    def __init__(self, session_mgr, shell):
        """Initialize with session manager and shell adapter."""
        self.session = session_mgr
        self.shell = shell
        self.validator = TierValidator(self.session.preferences)
    
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
    
    def route_command(self, input_text: str) -> CommandResult:
        """
        Route command through appropriate processing pipeline.
        
        Args:
            input_text: Raw user input
            
        Returns:
            CommandResult with execution results
        """
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