"""
CommandRouter - Routes commands through safety tiers and AI processing
SAFETY-CRITICAL: Ensures all commands go through appropriate validation
"""

from pathlib import Path
from typing import Any, Dict, Optional

from isaac.adapters.base_adapter import CommandResult
from isaac.ai.query_classifier import QueryClassifier
from isaac.core.tier_validator import TierValidator
from isaac.orchestration import LoadBalancingStrategy, RemoteExecutor
from isaac.runtime import CommandDispatcher


class CommandRouter:
    """Routes commands through tier validation and AI processing."""

    def __init__(self, session_mgr: Any, shell: Any) -> None:
        """Initialize with session manager and shell adapter."""
        self.session = session_mgr
        self.shell = shell
        self.validator = TierValidator(self.session.preferences)
        self.query_classifier = QueryClassifier()

        # Initialize the plugin dispatcher
        self.dispatcher = CommandDispatcher(session_mgr)
        self.dispatcher.load_commands(
            [Path(__file__).parent.parent / "commands", Path.home() / ".isaac" / "commands"]
        )

    def _confirm(self, message: str) -> bool:
        """Get user confirmation (placeholder - always return True for now)."""
        # TODO: Implement actual user input
        print(f"{message} (y/n): y")
        return True

    def _is_natural_language(self, input_text: str) -> bool:
        """Check if input contains natural language (spaces, common words)."""
        # Simple heuristic: has spaces and not obviously a command
        if " " not in input_text.strip():
            return False

        # Check for obvious command patterns
        first_word = input_text.strip().split()[0].lower()
        obvious_commands = ["ls", "cd", "pwd", "grep", "find", "cat", "echo", "rm", "cp", "mv"]

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
            elif char == "|" and not in_quotes:
                return False  # Found pipe outside quotes

        return True  # All pipes are quoted

    def _is_unix_command(self, cmd: str) -> bool:
        """Check if command is a Unix command that needs translation on Windows."""
        unix_commands = {
            "ls",
            "grep",
            "ps",
            "kill",
            "find",
            "cat",
            "head",
            "tail",
            "cp",
            "mv",
            "rm",
            "pwd",
            "which",
            "echo",
            "touch",
            "mkdir",
            "wc",
            "sort",
            "uniq",
            "chmod",
            "chown",
            "du",
            "df",
        }
        first_word = cmd.strip().split()[0] if cmd.strip() else ""
        return first_word in unix_commands

    def _route_device_command(self, input_text: str) -> CommandResult:
        """Handle !alias device routing commands."""
        # Parse device alias and command
        parts = input_text[1:].split(None, 1)  # Remove ! and split on first space
        if len(parts) != 2:
            return CommandResult(
                success=False,
                output="Usage: !device_alias /command\n       !device_alias:strategy /command",
                exit_code=1,
            )

        device_spec, device_cmd = parts

        # Parse device spec for strategy (alias:strategy)
        if ":" in device_spec:
            device_alias, strategy_name = device_spec.split(":", 1)
            # Map strategy names to enum values
            strategy_map = {
                "round_robin": LoadBalancingStrategy.ROUND_ROBIN,
                "least_load": LoadBalancingStrategy.LEAST_LOAD,
                "weighted": LoadBalancingStrategy.WEIGHTED_LEAST_LOAD,
                "random": LoadBalancingStrategy.RANDOM,
                "resource": LoadBalancingStrategy.RESOURCE_AWARE,
                "performance": LoadBalancingStrategy.PERFORMANCE_BASED,
            }
            strategy = strategy_map.get(strategy_name.lower(), LoadBalancingStrategy.LEAST_LOAD)
        else:
            device_alias = device_spec
            strategy = LoadBalancingStrategy.LEAST_LOAD

        # Initialize remote executor
        from isaac.orchestration import MachineRegistry

        registry = MachineRegistry()
        remote_executor = RemoteExecutor(registry)

        # Try local network execution first
        try:
            # Check if device_alias is a registered machine
            machine = registry.get_machine(device_alias)

            if machine:
                # Execute on specific machine
                print(f"Isaac > Executing on {device_alias}: {device_cmd}")
                result = remote_executor.execute_on_machine(machine.machine_id, device_cmd)

                if result.success:
                    return CommandResult(
                        success=True,
                        output=f"[{device_alias}] {result.output}",
                        exit_code=result.exit_code,
                    )
                else:
                    return CommandResult(
                        success=False,
                        output=f"[{device_alias}] Error: {result.error_message}",
                        exit_code=result.exit_code,
                    )

            # Check if device_alias is a group name
            group_machines = registry.get_group_machines(device_alias)
            if group_machines:
                # Use load balancing for group execution
                print(
                    f"Isaac > Load balancing across group '{device_alias}' ({len(group_machines)} machines): {device_cmd}"
                )
                result = remote_executor.execute_with_load_balancing(
                    device_cmd,
                    strategy=strategy,
                    group_name=device_alias,
                    command_complexity="normal",  # Could be inferred from command
                )

                if result.success:
                    return CommandResult(
                        success=True,
                        output=f"[{device_alias}] {result.output}",
                        exit_code=result.exit_code,
                    )
                else:
                    return CommandResult(
                        success=False,
                        output=f"[{device_alias}] Error: {result.error_message}",
                        exit_code=result.exit_code,
                    )

        except Exception as e:
            # Log error but continue to cloud routing
            print(f"Isaac > Local execution failed: {e}")

        # Try cloud routing (fallback)
        try:
            if self.session.cloud and self.session.cloud.is_available():
                success = self.session.cloud.route_command(device_alias, device_cmd)
                if success:
                    return CommandResult(
                        success=True,
                        output=f"Command routed to {device_alias} via cloud",
                        exit_code=0,
                    )
        except Exception:
            pass  # Fall through to queuing

        # Queue for later sync if all else fails
        queue_id = self.session.queue.enqueue(
            command=device_cmd,
            command_type="device_route",
            target_device=device_alias,
            metadata={"tier": self._get_tier(device_cmd)},
        )

        return CommandResult(
            success=True,
            output=f"Command queued (#{queue_id}) - will sync when online",
            exit_code=0,
        )

    def _get_tier(self, command: str) -> float:
        """Get safety tier for command."""
        return self.validator.get_tier(command)

    def _handle_meta_command(self, command: str) -> CommandResult:
        """Handle /commands using the plugin dispatcher or PipeEngine for pipes"""
        try:
            # Check for pipes - use PipeEngine for all piping
            if "|" in command and not self._is_quoted_pipe(command):
                from isaac.core.pipe_engine import PipeEngine

                engine = PipeEngine(self.session, self.shell)
                result_blob = engine.execute_pipeline(command)

                # Convert blob to CommandResult
                if result_blob["kind"] == "error":
                    return CommandResult(success=False, output=result_blob["content"], exit_code=1)
                else:
                    return CommandResult(success=True, output=result_blob["content"], exit_code=0)
            else:
                # Single command - use dispatcher
                result = self.dispatcher.execute(command)

                # Convert dispatcher result to CommandResult
                if result.get("ok", False):
                    return CommandResult(success=True, output=result.get("stdout", ""), exit_code=0)
                else:
                    # Handle error case
                    error_info = result.get("error", {})
                    error_msg = (
                        error_info.get("message", "Unknown error")
                        if isinstance(error_info, dict)
                        else str(error_info)
                    )
                    return CommandResult(
                        success=False, output=f"Command failed: {error_msg}", exit_code=1
                    )

        except Exception as e:
            return CommandResult(
                success=False, output=f"Command execution error: {str(e)}", exit_code=1
            )

    def _handle_config_command(self, input_text: str) -> CommandResult:
        """Handle /config commands directly"""
        try:
            # Parse the command: /config [args...]
            parts = input_text.split()
            if len(parts) < 2:
                # Just /config - show overview
                from isaac.commands.config.run import show_overview

                output = show_overview(self.session)
                return CommandResult(success=True, output=output, exit_code=0)

            # Parse arguments
            args_raw = " ".join(parts[1:])
            import shlex

            parsed_parts = shlex.split(args_raw)

            # Simple flag parsing for --flag format
            flags = {}
            i = 0
            while i < len(parsed_parts):
                part = parsed_parts[i]
                if part.startswith("--"):
                    flag_name = part[2:]  # Remove --
                    if i + 1 < len(parsed_parts) and not parsed_parts[i + 1].startswith("--"):
                        flags[flag_name] = parsed_parts[i + 1]
                        i += 1  # Skip the value
                    else:
                        flags[flag_name] = True
                i += 1

            # Call the appropriate config function
            from isaac.commands.config.run import (
                set_api_key,
                set_config,
                show_ai_details,
                show_cloud_details,
                show_collections_config,
                show_overview,
                show_plugins,
                show_status,
            )

            # Convert session to dict format expected by config functions
            session_dict = {
                "machine_id": getattr(self.session.config, "machine_id", "unknown"),
                "user_prefs": getattr(self.session.preferences, "data", {}),
            }

            if "help" in flags:
                # Show detailed help for config command
                from isaac.commands.help.run import get_detailed_help

                output = get_detailed_help("/config")
            elif "status" in flags:
                output = show_status(session_dict)
            elif "ai" in flags:
                output = show_ai_details(session_dict)
            elif "cloud" in flags:
                output = show_cloud_details(session_dict)
            elif "plugins" in flags:
                output = show_plugins()
            elif "collections" in flags:
                output = show_collections_config(session_dict)
            elif "set" in flags:
                key = flags["set"]
                # Find the value (everything after the key)
                key_index = parsed_parts.index(f"--set")
                if key_index + 1 < len(parsed_parts):
                    value = parsed_parts[key_index + 1]
                    output = set_config(session_dict, key, value)
                else:
                    output = "Usage: /config --set <key> <value>"
            elif "apikey" in flags or "key" in flags:
                service = flags.get("apikey") or flags.get("key")
                # Find the API key (next argument after the service in parsed_parts)
                service_index = None
                for i, part in enumerate(parsed_parts):
                    if part == service:  # Only match the service name, not the flag
                        service_index = i + 1
                        break
                if service_index and service_index < len(parsed_parts):
                    api_key = parsed_parts[service_index]
                    output = set_api_key(session_dict, service, api_key)
                else:
                    output = "Usage: /config --apikey <service> <api_key>\n\nSupported services:\n  xai-chat        - xAI API key for chat completion\n  xai-collections - xAI API key for collections\n  claude          - Anthropic Claude API key\n  openai          - OpenAI API key"
            else:
                output = show_overview(session_dict)

            return CommandResult(success=True, output=output, exit_code=0)

        except Exception as e:
            return CommandResult(
                success=False, output=f"Config command error: {str(e)}", exit_code=1
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
        if "|" in input_text and not self._is_quoted_pipe(input_text):
            from isaac.core.pipe_engine import PipeEngine

            engine = PipeEngine(self.session, self.shell)
            result_blob = engine.execute_pipeline(input_text)

            # Convert blob to CommandResult
            if result_blob["kind"] == "error":
                return CommandResult(success=False, output=result_blob["content"], exit_code=1)
            else:
                return CommandResult(success=True, output=result_blob["content"], exit_code=0)

        # Handle cd (change directory) specially - must change Isaac's working directory
        import os

        if input_text.strip().startswith("cd ") or input_text.strip() == "cd":
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
        if input_text.startswith("/f ") or input_text.startswith("/force "):
            # Extract actual command (skip /f or /force prefix)
            if input_text.startswith("/f "):
                actual_command = input_text[3:].lstrip()  # Skip '/f ' and any extra spaces
            else:
                actual_command = input_text[7:].lstrip()  # Skip '/force ' and any extra spaces

            print(f"Isaac > Force executing (bypassing AI validation): {actual_command}")
            return self.shell.execute(actual_command)

        # Check for meta-commands first
        if input_text.startswith("/"):
            # Handle special cases that don't go through dispatcher
            if input_text in ["/exit", "/quit"]:
                return CommandResult(success=True, output="", exit_code=0)
            if input_text == "/clear":
                import os

                os.system("cls" if os.name == "nt" else "clear")
                return CommandResult(success=True, output="", exit_code=0)
            if input_text.startswith("/config "):
                # Handle /config commands directly
                return self._handle_config_command(input_text)
            if input_text == "/config console":
                # Launch the config console TUI
                from isaac.ui.config_console import show_config_console

                message = show_config_console(self.session)
                return CommandResult(success=True, output=message, exit_code=0)

            # All other / commands go through dispatcher
            return self._handle_meta_command(input_text)

        # Check for device routing (!alias)
        if input_text.startswith("!"):
            return self._route_device_command(input_text)

        # Block exit/quit commands without / prefix
        if input_text.strip() in ["exit", "quit"]:
            return CommandResult(
                success=False, output="Isaac > Use /exit or /quit to exit Isaac", exit_code=1
            )

        # Task mode detection
        if input_text.lower().startswith("isaac task:"):
            task_desc = input_text[11:].strip()  # Remove "isaac task:"

            from isaac.ai.task_planner import execute_task

            return execute_task(task_desc, self.shell, self.session)

        # Agentic mode detection (Phase 2)
        if input_text.lower().startswith("isaac agent:") or input_text.lower().startswith(
            "isaac agentic:"
        ):
            agentic_query = input_text.split(":", 1)[1].strip()  # Remove "isaac agent:" prefix

            from isaac.core.agentic_orchestrator import AgenticOrchestrator
            from isaac.ui.progress_indicator import ProgressIndicator, ProgressStyle
            from isaac.ui.streaming_display import StreamingDisplay

            # Initialize UI components
            display = StreamingDisplay()
            progress = ProgressIndicator(style=ProgressStyle.SPINNER)

            # Initialize orchestrator with UI components
            orchestrator = AgenticOrchestrator(
                session_mgr=self.session, streaming_display=display, progress_indicator=progress
            )

            # Execute agentic task
            return orchestrator.execute_agentic_task_sync(agentic_query)

        # Natural language check - AI translation
        if self._is_natural_language(input_text):
            if not input_text.lower().startswith("isaac "):
                return CommandResult(
                    success=False, output="Isaac > I have a name, use it.", exit_code=-1
                )

            # AI translation (Phase 3.2)
            query = input_text[6:].strip()  # Remove "isaac " prefix

            # Check if query should route to chat mode (geographic/general info)
            if self.query_classifier.is_chat_mode_query(query):
                # Route to chat mode (like /ask command)
                return self._handle_chat_query(query)

            from isaac.ai.translator import translate_query

            result = translate_query(query, self.shell.name, self.session)

            if result["success"]:
                # Log AI query separately (privacy)
                if hasattr(self.session, "log_ai_query"):
                    self.session.log_ai_query(
                        query=query,
                        translated_command=result["command"],
                        explanation=result.get("explanation", ""),
                        executed=True,
                        shell_name=self.shell.name,
                    )

                # Execute translated command through tier system (CRITICAL)
                print(f"Isaac > Executing: {result['command']}")
                return self.route_command(result["command"])
            else:
                # Translation failed
                return CommandResult(
                    success=False, output=f"Isaac > {result['error']}", exit_code=-1
                )

        # Cross-platform alias translation for Unix commands on Windows
        import platform

        current_platform = platform.system().lower()

        if current_platform == "windows" and self._is_unix_command(input_text):
            try:
                from isaac.core.unix_aliases import UnixAliasTranslator

                translator = UnixAliasTranslator()
                translated = translator.translate(input_text)
                if translated:
                    if translator.show_translation:
                        print(f"Isaac > Translating Unix command: {input_text} -> {translated}")
                    input_text = translated
            except Exception as e:
                # If translation fails, continue with original command
                print(f"Isaac > Warning: Unix alias translation failed: {e}")

        # Regular command processing
        tier = self.validator.get_tier(input_text)

        if tier == 1:
            # Tier 1: Instant execution
            result = self.shell.execute(input_text)

            # Track command execution for learning
            self._track_command_execution(input_text, result, tier=1)

            return result
        elif tier == 2:
            # Tier 2: Auto-correct typos and execute
            from isaac.ai.corrector import correct_command

            # Try auto-correction
            correction = correct_command(input_text, self.shell.name, self.session.config)

            if correction["corrected"] and correction["confidence"] > 0.8:
                # High confidence typo detected - auto-correct
                print(
                    f"Isaac > Auto-correcting: {correction['original']} → {correction['corrected']}"
                )

                # Track the correction for learning
                self._track_auto_correction(
                    original=correction["original"],
                    corrected=correction["corrected"],
                    confidence=correction["confidence"],
                )

                result = self.shell.execute(correction["corrected"])
                self._track_command_execution(
                    correction["corrected"], result, tier=2, was_corrected=True
                )
                return result
            else:
                # No typo or low confidence - execute as-is
                result = self.shell.execute(input_text)
                self._track_command_execution(input_text, result, tier=2)
                return result
        elif tier == 2.5:
            # Tier 2.5: Correct + confirm
            from isaac.ai.corrector import correct_command

            # Try correction
            correction = correct_command(input_text, self.shell.name, self.session.config)

            if correction["corrected"] and correction["confidence"] > 0.7:
                # Show correction, ask for confirmation
                print("\n" + "=" * 60)
                print(f"Corrected: {correction['corrected']}")
                print(f"Original: {correction['original']}")
                print(f"Confidence: {correction['confidence']:.0%}")
                print("=" * 60 + "\n")

                confirmed = self._confirm("Execute corrected version?")
                if confirmed:
                    # Track user accepting correction
                    self._track_user_correction_acceptance(
                        original=correction["original"],
                        corrected=correction["corrected"],
                        accepted=True,
                    )
                    result = self.shell.execute(correction["corrected"])
                    self._track_command_execution(correction["corrected"], result, tier=2.5)
                    return result
            else:
                # No correction needed or low confidence - just confirm original
                confirmed = self._confirm(f"Execute: {input_text}?")
                if confirmed:
                    result = self.shell.execute(input_text)
                    self._track_command_execution(input_text, result, tier=2.5)
                    return result

            # User aborted
            return CommandResult(success=False, output="Isaac > Aborted.", exit_code=-1)
        elif tier == 3:
            # Tier 3: Validation required (Phase 3.4: AI validation)
            from isaac.ai.validator import validate_command

            # Get AI validation
            validation = validate_command(input_text, self.shell.name, self.session.config)

            # Show warnings if any
            if validation["warnings"]:
                print("\n" + "=" * 60)
                print("⚠️  SAFETY WARNINGS:")
                for warning in validation["warnings"]:
                    print(f"  • {warning}")
                print("=" * 60)

            # Show suggestions if any
            if validation["suggestions"]:
                print("\n💡 SUGGESTIONS:")
                for suggestion in validation["suggestions"]:
                    print(f"  • {suggestion}")
                print()

            # Confirm execution
            if validation["safe"]:
                confirmed = self._confirm(f"Execute: {input_text}?")
            else:
                confirmed = self._confirm(f"⚠️  POTENTIALLY UNSAFE - Execute anyway: {input_text}?")

            if confirmed:
                return self.shell.execute(input_text)
            else:
                return CommandResult(success=False, output="Isaac > Aborted.", exit_code=-1)
        elif tier == 4:
            # Tier 4: Lockdown - never execute
            return CommandResult(
                success=False, output="Isaac > Command too dangerous. Aborted.", exit_code=-1
            )
        else:
            # Unknown tier
            return CommandResult(
                success=False,
                output="Isaac > Unknown command tier. Aborted for safety.",
                exit_code=-1,
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
            from isaac.ai import AIRouter

            # Initialize AI router with session config
            router = AIRouter(session_mgr=self.session)

            # Build chat preprompt
            preprompt = self._build_chat_preprompt()

            # Prepare messages for router
            messages = [
                {"role": "system", "content": preprompt},
                {"role": "user", "content": query},
            ]

            # Query AI through router
            response = router.chat(messages=messages)

            if response.success:
                # Log query to AI history
                self.session.log_ai_query(
                    query=query,
                    translated_command="[chat_mode_auto]",
                    explanation=response.content[:100],
                    executed=False,
                    shell_name="chat",
                )

                return CommandResult(
                    success=True, output=f"Isaac > {response.content}", exit_code=0
                )
            else:
                return CommandResult(
                    success=False, output=f"Isaac > AI Error: {response.error}", exit_code=-1
                )

        except Exception as e:
            return CommandResult(
                success=False, output=f"Isaac > Error querying AI: {e}", exit_code=-1
            )

    def _build_chat_preprompt(self) -> str:
        """Build context-aware preprompt for chat mode."""
        shell_name = self.shell.name if hasattr(self.shell, "name") else "PowerShell"

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

    def _track_command_execution(
        self, command: str, result: CommandResult, tier: float, was_corrected: bool = False
    ) -> None:
        """Track command execution for learning system.

        Args:
            command: The executed command
            result: Command execution result
            tier: Safety tier level
            was_corrected: Whether command was auto-corrected
        """
        if not hasattr(self.session, "mistake_learner") or not self.session.mistake_learner:
            return

        try:
            # Track failed commands as mistakes
            if not result.success and result.exit_code != 0:
                context = {
                    "tier": tier,
                    "was_corrected": was_corrected,
                    "exit_code": result.exit_code,
                    "shell": self.shell.name,
                }

                # Determine severity based on exit code and tier
                if tier >= 3:
                    severity = "high"
                elif result.exit_code > 100:
                    severity = "medium"
                else:
                    severity = "low"

                self.session.track_mistake(
                    mistake_type="command_error",
                    description=f"Command failed with exit code {result.exit_code}",
                    correction="",  # Will be filled if user retries with different command
                    original_input=command,
                    context=context,
                    severity=severity,
                )

            # Track successful executions for pattern learning
            if result.success and hasattr(self.session, "preference_learner"):
                self.session.observe_coding_pattern(
                    pattern_type="command_patterns",
                    pattern_key=f"successful_command_{tier}",
                    observed_value={"command": command, "tier": tier},
                    context={"timestamp": __import__("time").time(), "success": True},
                )

        except Exception as e:
            # Don't fail command execution if tracking fails
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to track command execution: {e}")

    def _track_auto_correction(self, original: str, corrected: str, confidence: float) -> None:
        """Track automatic command corrections for learning.

        Args:
            original: Original command with typo
            corrected: Corrected command
            confidence: Confidence score of correction
        """
        if not hasattr(self.session, "mistake_learner") or not self.session.mistake_learner:
            return

        try:
            context = {"confidence": confidence, "auto_corrected": True, "shell": self.shell.name}

            self.session.track_mistake(
                mistake_type="command_typo",
                description=f"Typo detected and auto-corrected (confidence: {confidence:.1%})",
                correction=corrected,
                original_input=original,
                context=context,
                severity="low",
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to track auto-correction: {e}")

    def _track_user_correction_acceptance(self, original: str, corrected: str, accepted: bool) -> None:
        """Track whether user accepted a suggested correction.

        Args:
            original: Original command
            corrected: Suggested correction
            accepted: Whether user accepted the correction
        """
        if not hasattr(self.session, "behavior_engine") or not self.session.behavior_engine:
            return

        try:
            sentiment = 0.5 if accepted else -0.3
            feedback_text = f"User {'accepted' if accepted else 'rejected'} correction: {original} → {corrected}"

            self.session.record_user_feedback(
                feedback_type="correction" if accepted else "negative",
                context=f"Correction suggestion: {corrected}",
                response=feedback_text,
                category="suggestion_frequency",
                sentiment=sentiment,
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to track correction acceptance: {e}")
