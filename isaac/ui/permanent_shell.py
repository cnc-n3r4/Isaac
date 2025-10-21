"""
Permanent Shell - Isaac's traditional terminal interface
Implements a traditional terminal experience with status bar
"""

import sys
import signal
import platform
import os
import json
from typing import Optional
from pathlib import Path
from isaac.ui.terminal_control import TerminalControl
from isaac.core.tier_validator import TierValidator
from isaac.core.session_manager import SessionManager
from isaac.adapters.shell_detector import detect_shell
from isaac.models.preferences import Preferences
from isaac.commands.togrok_handler import TogrokHandler
from isaac.ui.advanced_input import AdvancedInputHandler

try:
    import colorama
    colorama.init()
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False


class PermanentShell:
    """Isaac's traditional terminal interface."""

    def __init__(self):
        """Initialize the permanent shell."""
        # Initialize session manager first (it will load config from ~/.isaac/config.json)
        self.session_manager = SessionManager()
        
        # Core components
        self.terminal = TerminalControl(self.session_manager)
        
        # Get the loaded preferences from session manager
        self.preferences = self.session_manager.get_preferences()
        
        # Get the loaded config from session manager
        self.config = self.session_manager.get_config()
        
        self.tier_validator = TierValidator(self.preferences)

        # Initialize advanced input handler for config mode
        self.advanced_input = AdvancedInputHandler(self.tier_validator)

        # Initialize Togrok handler for x.ai collections
        self.togrok_handler = TogrokHandler(self.session_manager)

        # Output buffering for Windows scrolling simulation
        self.output_buffer = []
        self.max_buffer_lines = 100

        # Initialize AI client if configured
        self.ai_client = None
        xai_api_key = self.config.get('xai_api_key')
        xai_api_url = self.config.get('xai_api_url')
        ai_model = self.config.get('ai_model', 'grok-beta')
        if xai_api_key and xai_api_url:
            try:
                from isaac.ai.xai_client import XaiClient
                self.ai_client = XaiClient(
                    api_key=xai_api_key,
                    api_url=xai_api_url,
                    model=ai_model
                )
                self._print_output_line("isaac> AI client initialized successfully")
            except Exception as e:
                self._print_output_line(f"isaac> Failed to initialize AI client: {e}")
        else:
            self._print_output_line("isaac> AI client not configured (missing xai_api_key or xai_api_url in config)")

        # Shell detection
        self.shell_adapter = None

        # State
        self.running = False
        self.current_directory = Path.cwd()

        # Output buffering for Windows scrolling simulation
        self.output_buffer = []
        self.max_buffer_lines = 100

    def start(self) -> None:
        """Start the traditional terminal session."""
        try:
            # Setup signal handlers for graceful exit
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)

            # Setup terminal
            self.terminal.setup_terminal()

            # Detect and setup shell
            self._setup_shell()

            # Start main loop
            self.running = True
            self._main_loop()

        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _setup_shell(self) -> None:
        """Detect and setup the appropriate shell adapter."""
        self.shell_adapter = detect_shell()

    def _main_loop(self) -> None:
        """Main interactive loop - traditional terminal style."""
        while self.running:
            try:
                # Show prompt and get command
                command = self._get_user_input()

                # Handle exit commands
                if command.lower() in ["exit", "quit", "q"]:
                    break

                # Process the command
                self._process_command(command)

            except KeyboardInterrupt:
                # Handle Ctrl+C gracefully - just print newline and continue
                self._print_output_line("")
                continue
            except Exception as e:
                if HAS_COLORAMA:
                    # Red text for errors
                    error_msg = f"\033[31mError: {str(e)}\033[0m"
                else:
                    error_msg = f"Error: {str(e)}"
                self._print_output_line(error_msg)

    def _get_user_input(self) -> str:
        """Get user input, handling config mode specially."""
        if self.terminal.config_mode:
            return self._get_config_input()
        else:
            return self._get_normal_input()

    def _get_normal_input(self) -> str:
        """Get user input with traditional prompt."""
        prompt = self.terminal.get_prompt_string()
        # Position cursor at the fixed prompt line (line 6)
        prompt_line = self.terminal.status_lines + 1  # Line 6
        print(f"\033[{prompt_line};1H", end="", flush=True)
        # Clear the line to remove any previous command
        print(f"\033[2K", end="", flush=True)
        try:
            return input(prompt).strip()
        except EOFError:
            return "exit"

    def _get_config_input(self) -> str:
        """Get input for config mode navigation."""
        while True:
            try:
                # Read single character
                char = self._get_char()
                
                if char == '\t':  # Tab - move to next item
                    self.terminal.navigate_config("next")
                    self.terminal.mark_body_dirty()
                elif char == ' ':  # Space - toggle current item
                    self.terminal.toggle_config_item()
                    self.terminal.mark_body_dirty()
                elif char == '\r' or char == '\n':  # Enter - save and exit
                    self.terminal.exit_config_mode(save=True)
                    return ""  # Return empty to continue main loop
                elif char == '\x1b':  # Escape - cancel and exit
                    self.terminal.exit_config_mode(save=False)
                    return ""  # Return empty to continue main loop
                # Ignore other characters
                
            except KeyboardInterrupt:
                # Handle Ctrl+C - cancel config mode
                self.terminal.exit_config_mode(save=False)
                return ""

    def _get_char(self) -> str:
        """Get a single character from stdin."""
        if os.name == 'nt':  # Windows
            import msvcrt
            return msvcrt.getch().decode('utf-8', errors='ignore')
        else:  # Unix-like
            import tty
            import termios
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                if ch == '\x1b':  # Escape sequence
                    ch += sys.stdin.read(2)
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _process_command(self, command: str) -> None:
        """Process a command in traditional terminal style."""
        if not command:
            return

        # Clear screen for each new command to prevent output overlap
        os.system('cls')
        self.terminal._draw_status_bar()

        # Validate command tier
        tier = self.tier_validator.get_tier(command)

        # Update status bar with current tier
        tier_display = self._format_tier_display(tier)
        self.terminal.update_status(tier=tier_display)

        # Process the command
        self._execute_command_logic(command)

    def _detect_command_prefix(self, command: str) -> tuple[str, str]:
        """
        Detect command prefix and return (prefix_type, stripped_command).
        
        Returns:
            ('/', command) - Local meta-command
            ('!', command) - Distributed command  
            ('', command) - Regular command (no prefix)
        """
        command = command.strip()
        
        if not command:
            return ('', '')
            
        # Check for local commands (/)
        if command.startswith('/'):
            return ('/', command[1:].strip())
            
        # Check for distributed commands (!)
        if command.startswith('!'):
            return ('!', command[1:].strip())
            
        # No prefix - regular command
        return ('', command)

    def _handle_local_command(self, command: str) -> None:
        """Handle local meta-commands starting with /."""
        if not command:
            self._print_output_line("isaac> No command provided after /")
            return
            
        command_lower = command.lower()
        
        if command_lower == 'help':
            self._show_help()
        elif command_lower == 'version':
            self._show_version()
        elif command_lower == 'status':
            self._show_status()
        elif command_lower == 'config':
            self.terminal.enter_config_mode()
        elif command_lower.startswith('ask'):
            # Handle /ask command - extract question after 'ask'
            question = command[3:].strip()  # Remove 'ask' and any spaces
            self._handle_explicit_ai_query(question)
        elif command_lower.startswith('scroll'):
            # Handle scrolling commands
            scroll_cmd = command[6:].strip().lower()
            if scroll_cmd == 'up':
                self.terminal.scroll_output_up()
            elif scroll_cmd == 'down':
                self.terminal.scroll_output_down()
            elif scroll_cmd == 'top':
                self.terminal.scroll_to_top()
            elif scroll_cmd == 'bottom':
                self.terminal.scroll_to_bottom()
            else:
                self._print_output_line("isaac> Usage: /scroll up|down|top|bottom")
        else:
            self._print_output_line(f"isaac> Unknown local command: /{command}")
            self._print_output_line("isaac> Available commands: /help, /version, /status, /config, /ask")

    def _handle_explicit_ai_query(self, question: str) -> None:
        """Handle explicit AI queries from /ask command."""
        if not question:
            self._print_output_line("isaac> Usage: /ask <your question>")
            self._print_output_line("isaac> Example: /ask what is the capital of France?")
            return

        if not self.ai_client:
            self._print_output_line("isaac> AI client not configured. Please set xai_api_key and xai_api_url in config.")
            return

        try:
            # Get recent command history for context
            command_history = self.session_manager.get_recent_commands(10)

            # Build comprehensive system prompt
            system_prompt = self._build_system_prompt(command_history)

            # Create user message with question
            user_message = f"Question: {question}"

            # Use AI client with enhanced prompt
            response = self.ai_client._call_api_with_system_prompt(system_prompt, user_message)

            if response.get('success'):
                ai_response = response.get('text', 'No response from AI')

                # Check if response is JSON (command validation) or text (AI query)
                if ai_response.strip().startswith('{') and ai_response.strip().endswith('}'):
                    # Parse JSON validation response
                    self._handle_validation_response(question, ai_response)
                else:
                    # Handle as regular AI response
                    self._handle_text_response(ai_response)
            else:
                if HAS_COLORAMA:
                    ai_error_msg = f"\033[31misaac> AI error: {response.get('error', 'Unknown error')}\033[0m"
                else:
                    ai_error_msg = f"isaac> AI error: {response.get('error', 'Unknown error')}"
                self._print_output_line(ai_error_msg)
        except Exception as e:
            if HAS_COLORAMA:
                ai_fail_msg = f"\033[31misaac> AI query failed: {e}\033[0m"
            else:
                ai_fail_msg = f"isaac> AI query failed: {e}"
            self._print_output_line(ai_fail_msg)

    def _handle_distributed_command(self, command: str) -> None:
        """Handle distributed commands starting with ! (placeholder implementation)."""
        if not command:
            self._print_output_line("isaac> No command provided after !")
            return
            
        # Placeholder implementation - distributed commands not yet implemented
        self._print_output_line(f"isaac> Distributed commands (!{command}) are not yet implemented")
        self._print_output_line("isaac> This feature will allow remote command execution across machines")

    def _show_help(self) -> None:
        """Show help for available commands."""
        help_text = """
isaac> Available Commands:

Regular Commands (no prefix):
  - Any shell command (ls, dir, cd, etc.)
  - Tier 1-2 commands execute immediately
  - Tier 3+ commands get AI validation for safety and corrections
  - isaac <command> - Direct shell execution (bypasses validation)

Local Meta-Commands (/):
  /help     - Show this help
  /version  - Show Isaac version
  /status   - Show current status
  /config   - Show current configuration
  /ask      - Ask AI questions (e.g., /ask what is the capital of France?)
  /scroll   - Scroll through command output:
             /scroll up     - Scroll up (show older output)
             /scroll down   - Scroll down (show newer output)
             /scroll top    - Jump to top of output
             /scroll bottom - Jump to bottom of output (latest)

AI Integration:
  /togrok create <name> - Create x.ai collection
  /togrok upload <name> <file> - Upload file to collection
  /togrok search <name> <query> - Search collection
  /togrok list - List collections

Distributed Commands (!) - Coming Soon:
  !machine command  - Execute on remote machine
  !list             - List available machines

Type shell commands normally, or use /ask for AI assistance.
"""
        for line in help_text.strip().split('\n'):
            self._print_output_line(line)

    def _show_version(self) -> None:
        """Show Isaac version information."""
        version_info = """
isaac> Isaac 2.0 MVP
isaac> Multi-platform shell assistant with AI integration
isaac> x.ai/Grok collections support
isaac> Distributed command system (coming soon)
"""
        for line in version_info.strip().split('\n'):
            self._print_output_line(line)

    def _show_status(self) -> None:
        """Show current system status."""
        status_lines = [
            "isaac> System Status:",
            f"isaac> Current Directory: {self.current_directory}",
            f"isaac> Shell: {type(self.shell_adapter).__name__ if self.shell_adapter else 'None'}",
            f"isaac> AI Client: {'Configured' if self.ai_client else 'Not configured'}",
            f"isaac> Session Manager: {'Active' if self.session_manager else 'Inactive'}",
            f"isaac> Distributed Mode: {'Enabled' if self.config.get('distributed_mode', False) else 'Disabled (coming soon)'}"
        ]
        
        for line in status_lines:
            self._print_output_line(line)

    def _show_config(self) -> None:
        """Show current configuration (safe, no secrets)."""
        config_lines = [
            "isaac> Current Configuration:",
            f"isaac> AI Model: {self.config.get('ai_model', 'Not set')}",
            f"isaac> Distributed Mode: {self.config.get('distributed_mode', 'false')}",
            f"isaac> API Keys: {'x.ai configured' if self.config.get('xai_api_key') else 'x.ai not configured'}",
            f"isaac> PHP API: {'Configured' if self.config.get('api_key') and self.config.get('api_url') else 'Not configured'}"
        ]
        
        for line in config_lines:
            self._print_output_line(line)

    def _handle_togrok_command(self, command: str) -> None:
        """Handle /togrok commands by delegating to TogrokHandler."""
        # Remove the "/togrok " prefix to get the arguments
        if command.lower().startswith("togrok "):
            args_str = command[7:].strip()  # Remove "togrok "
        else:
            args_str = command.strip()
        
        # Split the arguments
        args = args_str.split() if args_str else []
        
        # Delegate to the TogrokHandler
        try:
            result = self.togrok_handler.handle_command(args)
            self._print_output_line(f"isaac> {result}")
        except Exception as e:
            self._print_output_line(f"isaac> Error handling togrok command: {e}")

    def _execute_command_logic(self, command: str) -> None:
        """Execute the command logic."""
        # First, detect command prefix
        prefix_type, stripped_command = self._detect_command_prefix(command)
        
        # Route based on prefix
        if prefix_type == '/':
            self._handle_local_command(stripped_command)
            return
        elif prefix_type == '!':
            self._handle_distributed_command(stripped_command)
            return
        
        # No prefix - handle as regular command
        # Handle isaac-prefixed commands as direct shell execution
        if stripped_command.lower().startswith("isaac "):
            actual_command = stripped_command[6:].strip()  # Remove "isaac " prefix
            self._handle_isaac_command(actual_command)
            return

        # Validate command tier
        tier = self.tier_validator.get_tier(stripped_command)

        # Validate command tier
        tier = self.tier_validator.get_tier(stripped_command)

        # Handle different command types
        if stripped_command.startswith("/togrok"):
            self._handle_togrok_command(stripped_command)
        elif tier >= 3.0:
            self._handle_tier3_command(stripped_command, tier)
        else:
            # For tier 1-2 commands, execute immediately without AI validation
            self._execute_normal_command(stripped_command)

    def _handle_ai_validated_command(self, command: str) -> None:
        """Handle commands with AI validation for safety and corrections."""
        if not self.ai_client:
            # If no AI client, execute directly
            self._execute_normal_command(command)
            return

        try:
            # Get recent command history for context
            command_history = self.session_manager.get_recent_commands(10)

            # Build system prompt for command validation
            system_prompt = self._build_command_validation_prompt(command_history)

            # Create validation request
            user_message = f"Current directory: {self.current_directory}\nCommand to validate: {command}"

            # Get AI validation
            response = self.ai_client._call_api_with_system_prompt(system_prompt, user_message)

            if response.get('success'):
                ai_response = response.get('text', '')

                # Check if response is JSON validation
                if ai_response.strip().startswith('{') and ai_response.strip().endswith('}'):
                    # Parse JSON validation response
                    self._handle_validation_response(command, ai_response)
                else:
                    # If AI doesn't return JSON, assume command is safe and execute
                    self._print_output_line("isaac> Command validated - executing...")
                    self._execute_normal_command(command)
            else:
                # If AI validation fails, execute anyway but warn
                self._print_output_line("isaac> AI validation unavailable - executing command...")
                self._execute_normal_command(command)

        except Exception as e:
            # If AI validation fails, execute anyway
            self._print_output_line(f"isaac> AI validation failed ({e}) - executing command...")
            self._execute_normal_command(command)

    def _handle_isaac_command(self, command: str) -> None:
        """Handle isaac-prefixed commands as direct shell execution."""
        # Check if command is valid (basic validation)
        if not command:
            self._print_output_line("isaac> No command provided")
            return

        # For now, treat all isaac commands as valid and execute them
        # TODO: Add history-based validation later
        self._print_output_line("isaac> Valid command, executing..")
        self._execute_normal_command(command)

    def _is_ai_query(self, command: str) -> bool:
        """Check if command is an AI query."""
        # Commands starting with "isaac " are shell commands, not AI queries
        if command.lower().startswith("isaac "):
            return False

        command_lower = command.lower().strip()

        # Check for question patterns
        question_words = ["what", "where", "when", "why", "how", "who", "which", "can you", "could you", "would you", "do you", "are you", "is it", "does it"]
        if any(command_lower.startswith(word) for word in question_words):
            return True

        # Check for conversational patterns
        conversational_starts = ["tell me", "explain", "describe", "help me", "i need", "i want", "can i", "should i"]
        if any(phrase in command_lower for phrase in conversational_starts):
            return True

        # Check for AI-specific prefixes
        ai_prefixes = ["ai", "grok", "hey isaac"]
        if any(command_lower.startswith(prefix) for prefix in ai_prefixes):
            return True

        # If it contains question marks or is longer than typical commands, likely AI query
        if "?" in command or len(command.split()) > 3:
            return True

        return False

    def _handle_ai_query(self, command: str) -> None:
        """Handle AI query in traditional style."""
        if not self.ai_client:
            self._print_output_line("isaac> AI client not configured. Please set api_key and api_url in preferences.")
            return

        try:
            # Get recent command history for context
            command_history = self.session_manager.get_recent_commands(10)  # Last 10 commands

            # Build comprehensive system prompt
            system_prompt = self._build_system_prompt(command_history)

            # Create user message with command and context
            user_message = f"Current directory: {self.current_directory}\nCommand/Query: {command}"

            # Use AI client with enhanced prompt
            response = self.ai_client._call_api_with_system_prompt(system_prompt, user_message)

            if response.get('success'):
                ai_response = response.get('text', 'No response from AI')

                # Check if response is JSON (command validation) or text (AI query)
                if ai_response.strip().startswith('{') and ai_response.strip().endswith('}'):
                    # Parse JSON validation response
                    self._handle_validation_response(command, ai_response)
                else:
                    # Handle as regular AI response
                    self._handle_text_response(ai_response)
            else:
                if HAS_COLORAMA:
                    ai_error_msg = f"\033[31misaac> AI error: {response.get('error', 'Unknown error')}\033[0m"
                else:
                    ai_error_msg = f"isaac> AI error: {response.get('error', 'Unknown error')}"
                self._print_output_line(ai_error_msg)
        except Exception as e:
            if HAS_COLORAMA:
                ai_fail_msg = f"\033[31misaac> AI query failed: {e}\033[0m"
            else:
                ai_fail_msg = f"isaac> AI query failed: {e}"
            self._print_output_line(ai_fail_msg)

    def _build_system_prompt(self, command_history: list) -> str:
        """Build comprehensive system prompt with context and history."""
        history_text = "\n".join([f"- {cmd}" for cmd in command_history]) if command_history else "No recent commands"

        return f"""You are Isaac, an intelligent cross-platform command-line assistant. You help users with shell commands and general queries.

CONTEXT:
- User is running commands on their own machine (Windows PowerShell or Linux bash)
- Current working directory: {self.current_directory}
- Recent command history:
{history_text}

YOUR CAPABILITIES:
1. For shell commands: Analyze safety, suggest corrections, provide explanations
2. For general queries: Provide helpful, accurate information
3. For ambiguous inputs: Ask clarifying questions or make reasonable assumptions

COMMAND ANALYSIS RULES:
- Be cautious but not paranoid (user knows what they're doing)
- Flag destructive operations (rm *, del /s, format, etc.)
- Flag operations on system directories (/etc, /sys, C:\\Windows, C:\\Program Files)
- Allow normal development operations (git, npm, pip, file operations in user directories)
- Suggest safer alternatives when appropriate

RESPONSE GUIDELINES:
- For command validation: Return JSON with safety assessment
- For general queries: Return natural language responses
- For incorrect commands: Provide the corrected command in "Suggestion:" format
- When suggesting corrections: Use the exact command syntax for the user's shell
- Keep explanations concise and actionable
- Use the command history to understand context and provide relevant suggestions

COMMAND CORRECTION EXAMPLES:
- User: "list files" → Suggestion: dir (Windows) or ls (Linux)
- User: "delete file.txt" → Suggestion: del file.txt (Windows) or rm file.txt (Linux)
- User: "show directory" → Suggestion: dir (Windows) or pwd (Linux)

Always provide the most helpful response based on the user's intent."""

    def _build_command_validation_prompt(self, command_history: list) -> str:
        """Build system prompt specifically for command validation and safety checking."""
        history_text = "\n".join([f"- {cmd}" for cmd in command_history]) if command_history else "No recent commands"

        return f"""You are Isaac's command safety validator. Your role is to analyze shell commands for safety and provide corrections when needed.

CONTEXT:
- User is running commands on their own machine (Windows PowerShell or Linux bash)
- Current working directory: {self.current_directory}
- Recent command history:
{history_text}

VALIDATION TASK:
Analyze the provided command for safety and correctness. Return a JSON response with this exact structure:
{{
  "safe": true/false,
  "reason": "brief explanation if unsafe",
  "suggestion": "corrected command if needed, empty string if safe"
}}

SAFETY RULES:
- Allow normal file operations in user directories
- Allow development tools (git, npm, pip, python, node, etc.)
- Allow directory navigation and listing
- Flag destructive operations (rm -rf /, del /s /q, format, etc.)
- Flag operations on system directories (/etc, /sys, C:\\Windows, C:\\Program Files)
- Flag operations that could cause data loss or system instability
- Be cautious but not paranoid - users know what they're doing

COMMAND CORRECTION GUIDELINES:
- If command syntax is wrong, provide the corrected version
- Use appropriate syntax for the user's shell environment
- If command is safe but could be improved, suggest the better version
- Only suggest corrections for actual errors or significant improvements

RESPONSE FORMAT:
- Always return valid JSON
- Set "safe": true for commands that are safe to execute
- Set "safe": false for risky or incorrect commands
- Include brief reason for unsafe commands
- Include corrected command in "suggestion" field when applicable
- Leave "suggestion" as empty string for safe commands

EXAMPLES:
Safe command: {{"safe": true, "reason": "", "suggestion": ""}}
Unsafe command: {{"safe": false, "reason": "Deletes all files recursively", "suggestion": "rm specific_file.txt"}}
Corrected command: {{"safe": true, "reason": "", "suggestion": "dir /w"}}"""

    def _handle_validation_response(self, command: str, ai_response: str) -> None:
        """Handle JSON validation response from AI."""
        try:
            validation = json.loads(ai_response)

            if validation.get('safe', False):
                self._print_output_line("isaac> Command validated as safe - executing...")
                self._execute_normal_command(command)
            else:
                reason = validation.get('reason', 'Unknown risk')
                suggestion = validation.get('suggestion', '')

                self._print_output_line(f"isaac> Command flagged: {reason}")
                if suggestion:
                    self._print_output_line(f"isaac> Suggestion: {suggestion}")

                # Ask for confirmation
                self._print_output_line("isaac> Proceed anyway? (y/n)")
                try:
                    response = input().strip().lower()
                    if response in ['y', 'yes']:
                        self._execute_normal_command(command)
                    else:
                        self._print_output_line("isaac> Command cancelled.")
                except (EOFError, KeyboardInterrupt):
                    self._print_output_line("isaac> Command cancelled.")

        except json.JSONDecodeError:
            # Fallback to text response if JSON parsing fails
            self._handle_text_response(f"AI validation response: {ai_response}")

    def _handle_text_response(self, ai_response: str) -> None:
        """Handle regular text response from AI."""
        # Check if AI is suggesting a corrected command
        if "Suggestion:" in ai_response and ("Get-ChildItem" in ai_response or "ls" in ai_response or "dir" in ai_response):
            # Extract the suggested command from the response
            lines = ai_response.split('\n')
            suggested_command = None
            for line in lines:
                if line.strip().startswith("Suggestion:"):
                    # Extract command from suggestion
                    suggestion = line.replace("Suggestion:", "").strip()
                    # Take the first command before any parentheses or additional text
                    if " (" in suggestion:
                        suggested_command = suggestion.split(" (")[0].strip()
                    else:
                        suggested_command = suggestion.strip()
                    break

            if suggested_command:
                self._print_output_line(f"isaac> Executing corrected command: {suggested_command}")
                self._execute_normal_command(suggested_command)
                return

        # Split multi-line response into separate lines for proper cursor positioning
        response_lines = ai_response.splitlines()

        # Batch all AI response lines to avoid display corruption
        for i, line in enumerate(response_lines):
            if i == 0:
                # First line gets "isaac> " prefix
                self.output_buffer.append(f"isaac> {line}")
            else:
                # Subsequent lines get indentation to align with the text
                self.output_buffer.append(f"       {line}")
            if len(self.output_buffer) > self.max_buffer_lines:
                self.output_buffer.pop(0)

        # Refresh display only once after all lines are added
        # For Windows, clear screen first, then print directly to avoid display corruption with scroll regions
        os.system('cls')
        self.terminal._draw_status_bar()
        
        formatted_lines = []
        for i, line in enumerate(response_lines):
            if i == 0:
                formatted_lines.append(f"isaac> {line}")
            else:
                formatted_lines.append(f"       {line}")
        output_text = '\n'.join(formatted_lines)
        # Print a newline first to move past any existing text
        print("", flush=True)
        print(output_text, flush=True)
        # Add to buffer for consistency
        for line in formatted_lines:
            self.output_buffer.append(line)
            if len(self.output_buffer) > self.max_buffer_lines:
                self.output_buffer.pop(0)

    def _handle_tier3_command(self, command: str, tier: float) -> None:
        """Handle Tier 3+ commands with confirmation."""
        self._print_output_line(f"isaac> Tier {tier} command requires confirmation. Proceed? (y/n)")

        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                self._execute_normal_command(command)
            else:
                self._print_output_line("isaac> Command cancelled.")
        except KeyboardInterrupt:
            self._print_output_line("")
            self._print_output_line("isaac> Command cancelled.")
        except EOFError:
            self._print_output_line("isaac> Command cancelled.")

    def _execute_normal_command(self, command: str) -> None:
        """Execute a normal shell command."""
        if not self.shell_adapter:
            self._print_output_line("isaac> No shell adapter available")
            return

        # Handle special commands that interfere with our UI
        if self._handle_special_command(command):
            return

        try:
            # Show command being executed (like normal terminal)
            self._print_output_line(f"{self.terminal.get_prompt_string()}{command}")

            result = self.shell_adapter.execute(command)

            # Show output as normal terminal output
            if result.output.strip():
                for line in result.output.splitlines():
                    is_blank = len(line.strip()) == 0
                    if not is_blank:
                        self._print_output_line(line)

            # Update working directory if cd command
            if command.startswith("cd "):
                new_path = command[3:].strip()
                if new_path:
                    try:
                        os.chdir(new_path)
                        self.current_directory = Path.cwd()
                        self.terminal.working_directory = self.current_directory
                    except:
                        pass  # Keep current directory on error

            # Save to session if successful
            if result.success:
                self.session_manager.log_command(command, result.exit_code)

        except KeyboardInterrupt:
            # Handle Ctrl+C during command execution
            self._print_output_line("^C")
            self._print_output_line("isaac> Command interrupted")
        except Exception as e:
            self._print_output_line(f"isaac> Execution failed: {str(e)}")

    def _print_output_line(self, line: str):
        """Print a line of output, handling buffering for Windows."""
        self.output_buffer.append(line)
        if len(self.output_buffer) > self.max_buffer_lines:
            self.output_buffer.pop(0)

        # Add to terminal body for new UI
        self.terminal.add_output(line)
        self.terminal.mark_body_dirty()

        # Only update screen if terminal is set up (not during __init__)
        if hasattr(self, 'running') and self.running:
            # On Windows, use efficient screen update
            self.terminal.update_screen()

    def _refresh_display(self):
        """Refresh the entire display for Windows (simulate scroll region)."""
        # Clear screen
        os.system('cls')

        # Redraw status bar
        self.terminal._draw_status_bar()

        # Position cursor at start of output area (line 6) before printing output
        print(f"\033[6;1H", end="", flush=True)

        # Print buffered output, limited to available lines
        available_lines = self.terminal.terminal_height - self.terminal.status_lines - 1
        start_idx = max(0, len(self.output_buffer) - available_lines)

        # Print all lines at once to avoid corruption
        output_text = '\n'.join(self.output_buffer[start_idx:])
        print(output_text)

        # Position cursor at bottom for next input
        displayed_lines = len(self.output_buffer) - start_idx
        bottom_line = self.terminal.status_lines + 1 + displayed_lines
        if bottom_line > self.terminal.terminal_height:
            bottom_line = self.terminal.terminal_height
        print(f"\033[{bottom_line};1H", end="", flush=True)

    def _handle_clear_command(self) -> None:
        """Handle clear/cls commands by clearing the output buffer and refreshing display."""
        # Show the command being executed
        self._print_output_line(f"{self.terminal.get_prompt_string()}{self._get_clear_command_name()}")

        # Clear the output buffer
        self.output_buffer.clear()

        # Refresh the display (clears screen and redraws status bar)
        self._refresh_display()

    def _handle_reset_command(self) -> None:
        """Handle reset command by clearing output buffer and refreshing display."""
        # Show the command being executed
        self._print_output_line(f"{self.terminal.get_prompt_string()}reset")

        # Clear the output buffer
        self.output_buffer.clear()

        # Refresh the display
        self._refresh_display()

    def _handle_special_command(self, command: str) -> bool:
        """Handle commands that need special treatment to preserve UI.

        Returns:
            True if command was handled specially, False if normal execution should continue
        """
        cmd_lower = command.lower().strip()

        # Handle clear/cls commands - only clear below status bar
        if cmd_lower in ["clear", "cls"]:
            self._handle_clear_command()
            return True
        elif cmd_lower == "reset":
            self._handle_reset_command()
            return True

        return False

    def _get_clear_command_name(self) -> str:
        """Get the appropriate clear command name for current shell."""
        return "cls"

    def _format_tier_display(self, tier: float) -> str:
        """Format tier for status display."""
        if tier == 1.0:
            return "1 (Safe)"
        elif tier == 2.0:
            return "2 (Auto-correct)"
        elif tier == 2.5:
            return "2.5 (Confirm)"
        elif tier == 3.0:
            return "3 (Validate)"
        elif tier == 4.0:
            return "4 (Lockdown)"
        else:
            return f"{tier} (Unknown)"

    def _signal_handler(self, signum, frame) -> None:
        """Handle termination signals."""
        self.running = False

    def _cleanup(self) -> None:
        """Clean up terminal state."""
        try:
            self.terminal.restore_terminal()
            print("\nIsaac session ended. Goodbye!")
        except:
            pass  # Best effort cleanup