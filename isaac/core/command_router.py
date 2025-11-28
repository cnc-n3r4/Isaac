"""
CommandRouter - Routes commands through safety tiers and AI processing
SAFETY-CRITICAL: Ensures all commands go through appropriate validation
"""

from pathlib import Path
from typing import Optional

from isaac.adapters.base_adapter import CommandResult
from isaac.ai.query_classifier import QueryClassifier
from isaac.core.tier_validator import TierValidator
from isaac.orchestration import LoadBalancingStrategy, RemoteExecutor
from isaac.runtime import CommandDispatcher


class StrategyContext:
    """Context passed to strategies during execution."""

    def __init__(self, session, shell, validator, query_classifier, dispatcher):
        self.session = session
        self.shell = shell
        self.validator = validator
        self.query_classifier = query_classifier
        self.dispatcher = dispatcher


class BaseStrategy:
    """Base class for all routing strategies."""

    def get_priority(self) -> int:
        """Return priority (lower number = higher priority)."""
        raise NotImplementedError

    def can_handle(self, input_text: str) -> bool:
        """Check if this strategy can handle the input."""
        raise NotImplementedError

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        """Execute the strategy and return result."""
        raise NotImplementedError


class PipeStrategy(BaseStrategy):
    """Handles pipe commands (|)."""

    def get_priority(self) -> int:
        return 10

    def can_handle(self, input_text: str) -> bool:
        return "|" in input_text and not self._is_quoted_pipe(input_text)

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

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        from isaac.core.pipe_engine import PipeEngine

        engine = PipeEngine(context.session, context.shell)
        result_blob = engine.execute_pipeline(input_text)

        if result_blob["kind"] == "error":
            return CommandResult(success=False, output=result_blob["content"], exit_code=1)
        else:
            return CommandResult(success=True, output=result_blob["content"], exit_code=0)


class CdStrategy(BaseStrategy):
    """Handles cd (change directory) command."""

    def get_priority(self) -> int:
        return 15

    def can_handle(self, input_text: str) -> bool:
        return input_text.strip().startswith("cd ") or input_text.strip() == "cd"

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        import os

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


class ForceExecutionStrategy(BaseStrategy):
    """Handles force execution commands (/f or /force)."""

    def get_priority(self) -> int:
        return 20

    def can_handle(self, input_text: str) -> bool:
        return input_text.startswith("/f ") or input_text.startswith("/force ")

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        if input_text.startswith("/f "):
            actual_command = input_text[3:].lstrip()  # Skip '/f ' and any extra spaces
        else:
            actual_command = input_text[7:].lstrip()  # Skip '/force ' and any extra spaces

        print(f"Isaac > Force executing (bypassing AI validation): {actual_command}")
        return context.shell.execute(actual_command)


class ExitQuitStrategy(BaseStrategy):
    """Handles /exit and /quit commands."""

    def get_priority(self) -> int:
        return 25

    def can_handle(self, input_text: str) -> bool:
        return input_text in ["/exit", "/quit"]

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        return CommandResult(success=True, output="", exit_code=0)


class ClearStrategy(BaseStrategy):
    """Handles /clear command."""

    def get_priority(self) -> int:
        return 30

    def can_handle(self, input_text: str) -> bool:
        return input_text == "/clear"

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        import os

        os.system("cls" if os.name == "nt" else "clear")
        return CommandResult(success=True, output="", exit_code=0)


class ConfigStrategy(BaseStrategy):
    """Handles /config commands."""

    def get_priority(self) -> int:
        return 35

    def can_handle(self, input_text: str) -> bool:
        return input_text.startswith("/config ")

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        # Extract and handle config command
        parts = input_text.split()
        if len(parts) < 2:
            from isaac.commands.config.run import show_overview

            output = show_overview(context.session)
            return CommandResult(success=True, output=output, exit_code=0)

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
            "machine_id": getattr(context.session.config, "machine_id", "unknown"),
            "user_prefs": getattr(context.session.preferences, "data", {}),
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


class ConfigConsoleStrategy(BaseStrategy):
    """Handles /config console command."""

    def get_priority(self) -> int:
        return 40

    def can_handle(self, input_text: str) -> bool:
        return input_text == "/config console"

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        from isaac.ui.config_console import show_config_console

        message = show_config_console(context.session)
        return CommandResult(success=True, output=message, exit_code=0)


class MetaCommandStrategy(BaseStrategy):
    """Handles other / commands using dispatcher."""

    def get_priority(self) -> int:
        return 50

    def can_handle(self, input_text: str) -> bool:
        return input_text.startswith("/")

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        try:
            result = context.dispatcher.execute(input_text)
            if result.get("ok", False):
                return CommandResult(success=True, output=result.get("stdout", ""), exit_code=0)
            else:
                error_info = result.get("error", {})
                error_msg = error_info.get("message", "Unknown error") if isinstance(error_info, dict) else str(error_info)
                return CommandResult(success=False, output=f"Command failed: {error_msg}", exit_code=1)
        except Exception as e:
            return CommandResult(success=False, output=f"Command execution error: {str(e)}", exit_code=1)


class DeviceRoutingStrategy(BaseStrategy):
    """Handles !alias device routing commands."""

    def get_priority(self) -> int:
        return 55

    def can_handle(self, input_text: str) -> bool:
        return input_text.startswith("!")

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
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
            if context.session.cloud and context.session.cloud.is_available():
                success = context.session.cloud.route_command(device_alias, device_cmd)
                if success:
                    return CommandResult(
                        success=True,
                        output=f"Command routed to {device_alias} via cloud",
                        exit_code=0,
                    )
        except Exception:
            pass  # Fall through to queuing

        # Queue for later sync if all else fails
        queue_id = context.session.queue.enqueue(
            command=device_cmd,
            command_type="device_route",
            target_device=device_alias,
            metadata={"tier": context.validator.get_tier(device_cmd)},
        )

        return CommandResult(
            success=True,
            output=f"Command queued (#{queue_id}) - will sync when online",
            exit_code=0,
        )


class ExitBlockerStrategy(BaseStrategy):
    """Blocks exit/quit without / prefix."""

    def get_priority(self) -> int:
        return 60

    def can_handle(self, input_text: str) -> bool:
        return input_text.strip() in ["exit", "quit"]

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        return CommandResult(
            success=False,
            output="Isaac > Use /exit or /quit to exit Isaac",
            exit_code=1,
        )


class TaskModeStrategy(BaseStrategy):
    """Handles isaac task: commands."""

    def get_priority(self) -> int:
        return 65

    def can_handle(self, input_text: str) -> bool:
        return input_text.lower().startswith("isaac task:")

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        task_desc = input_text[11:].strip()  # Remove "isaac task:"
        from isaac.ai.task_planner import execute_task
        return execute_task(task_desc, context.shell, context.session)


class AgenticModeStrategy(BaseStrategy):
    """Handles isaac agent: or isaac agentic: commands."""

    def get_priority(self) -> int:
        return 70

    def can_handle(self, input_text: str) -> bool:
        return input_text.lower().startswith("isaac agent:") or input_text.lower().startswith("isaac agentic:")

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        agentic_query = input_text.split(":", 1)[1].strip()  # Remove "isaac agent:" prefix
        from isaac.core.agentic_orchestrator import AgenticOrchestrator
        from isaac.ui.progress_indicator import ProgressIndicator, ProgressStyle
        from isaac.ui.streaming_display import StreamingDisplay

        # Initialize UI components
        display = StreamingDisplay()
        progress = ProgressIndicator(style=ProgressStyle.SPINNER)

        # Initialize orchestrator with UI components
        orchestrator = AgenticOrchestrator(
            session_mgr=context.session, streaming_display=display, progress_indicator=progress
        )

        # Execute agentic task
        return orchestrator.execute_agentic_task_sync(agentic_query)


class NaturalLanguageStrategy(BaseStrategy):
    """Handles natural language queries starting with 'isaac'."""

    def get_priority(self) -> int:
        return 75

    def can_handle(self, input_text: str) -> bool:
        return self._is_natural_language(input_text) and input_text.lower().startswith("isaac ")

    def _is_natural_language(self, input_text: str) -> bool:
        if " " not in input_text.strip():
            return False
        first_word = input_text.strip().split()[0].lower()
        obvious_commands = ["ls", "cd", "pwd", "grep", "find", "cat", "echo", "rm", "cp", "mv"]
        return first_word not in obvious_commands

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        query = input_text[6:].strip()  # Remove "isaac " prefix
        if context.query_classifier.is_chat_mode_query(query):
            return self._handle_chat_query(query, context)

        from isaac.ai.translator import translate_query

        result = translate_query(query, context.shell.name, context.session)
        if result["success"]:
            # Log AI query separately (privacy)
            if hasattr(context.session, "log_ai_query"):
                context.session.log_ai_query(
                    query=query,
                    translated_command=result["command"],
                    explanation=result.get("explanation", ""),
                    executed=True,
                    shell_name=context.shell.name,
                )

            # Execute translated command through tier system (CRITICAL)
            print(f"Isaac > Executing: {result['command']}")
            return context.router.route_command(result["command"])  # Recursive call
        else:
            # Translation failed
            return CommandResult(success=False, output=f"Isaac > {result['error']}", exit_code=-1)

    def _handle_chat_query(self, query: str, context: StrategyContext) -> CommandResult:
        try:
            from isaac.ai import AIRouter

            # Initialize AI router with session config
            router = AIRouter(session_mgr=context.session)

            # Build chat preprompt
            preprompt = self._build_chat_preprompt(context)

            # Prepare messages for router
            messages = [
                {"role": "system", "content": preprompt},
                {"role": "user", "content": query},
            ]

            # Query AI through router
            response = router.chat(messages=messages)

            if response.success:
                # Log query to AI history
                context.session.log_ai_query(
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

    def _build_chat_preprompt(self, context: StrategyContext) -> str:
        shell_name = context.shell.name if hasattr(context.shell, "name") else "PowerShell"

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


class UnixAliasStrategy(BaseStrategy):
    """Handles Unix command aliases on Windows."""

    def get_priority(self) -> int:
        return 80

    def can_handle(self, input_text: str) -> bool:
        import platform
        current_platform = platform.system().lower()
        return current_platform == "windows" and self._is_unix_command(input_text)

    def _is_unix_command(self, cmd: str) -> bool:
        unix_commands = {
            "ls", "grep", "ps", "kill", "find", "cat", "head", "tail", "cp", "mv", "rm", "pwd",
            "which", "echo", "touch", "mkdir", "wc", "sort", "uniq", "chmod", "chown", "du", "df",
        }
        first_word = cmd.strip().split()[0] if cmd.strip() else ""
        return first_word in unix_commands

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        try:
            from isaac.core.unix_aliases import UnixAliasTranslator

            translator = UnixAliasTranslator()
            translated = translator.translate(input_text)
            if translated:
                if translator.show_translation:
                    print(f"Isaac > Translating Unix command: {input_text} -> {translated}")
                input_text = translated
        except Exception as e:
            print(f"Isaac > Warning: Unix alias translation failed: {e}")
        # Fall through to tier execution
        return context.router.route_command(input_text)  # Recursive call


class TierExecutionStrategy(BaseStrategy):
    """Default strategy for tier-based command execution."""

    def get_priority(self) -> int:
        return 100

    def can_handle(self, input_text: str) -> bool:
        return True  # Always can handle as fallback

    def execute(self, input_text: str, context: StrategyContext) -> CommandResult:
        tier = context.validator.get_tier(input_text)

        if tier == 1:
            # Tier 1: Instant execution
            result = context.shell.execute(input_text)

            # Track command execution for learning
            self._track_command_execution(input_text, result, tier, context)

            return result
        elif tier == 2:
            # Tier 2: Auto-correct typos and execute
            from isaac.ai.corrector import correct_command

            # Try auto-correction
            correction = correct_command(input_text, context.shell.name, context.session.config)

            if correction["corrected"] and correction["confidence"] > 0.8:
                # High confidence typo detected - auto-correct
                print(f"Isaac > Auto-correcting: {correction['original']} → {correction['corrected']}")

                # Track the correction for learning
                self._track_auto_correction(correction["original"], correction["corrected"], correction["confidence"], context)

                result = context.shell.execute(correction["corrected"])
                self._track_command_execution(correction["corrected"], result, tier, context, was_corrected=True)
                return result
            else:
                # No typo or low confidence - execute as-is
                result = context.shell.execute(input_text)
                self._track_command_execution(input_text, result, tier, context)
                return result
        elif tier == 2.5:
            # Tier 2.5: Correct + confirm
            from isaac.ai.corrector import correct_command

            # Try correction
            correction = correct_command(input_text, context.shell.name, context.session.config)

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
                    self._track_user_correction_acceptance(correction["original"], correction["corrected"], True, context)
                    result = context.shell.execute(correction["corrected"])
                    self._track_command_execution(correction["corrected"], result, tier, context)
                    return result
            else:
                # No correction needed or low confidence - just confirm original
                confirmed = self._confirm(f"Execute: {input_text}?")
                if confirmed:
                    result = context.shell.execute(input_text)
                    self._track_command_execution(input_text, result, tier, context)
                    return result

            # User aborted
            return CommandResult(success=False, output="Isaac > Aborted.", exit_code=-1)
        elif tier == 3:
            # Tier 3: Validation required (Phase 3.4: AI validation)
            from isaac.ai.validator import validate_command

            # Get AI validation
            validation = validate_command(input_text, context.shell.name, context.session.config)

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
                return context.shell.execute(input_text)
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

    def _confirm(self, message: str) -> bool:
        """Get user confirmation (placeholder - always return True for now)."""
        # TODO: Implement actual user input
        print(f"{message} (y/n): y")
        return True

    def _track_command_execution(self, command: str, result: CommandResult, tier: float, context: StrategyContext, was_corrected: bool = False):
        """Track command execution for learning system.

        Args:
            command: The executed command
            result: Command execution result
            tier: Safety tier level
            was_corrected: Whether command was auto-corrected
        """
        if not hasattr(context.session, "mistake_learner") or not context.session.mistake_learner:
            return

        try:
            # Track failed commands as mistakes
            if not result.success and result.exit_code != 0:
                context = {
                    "tier": tier,
                    "was_corrected": was_corrected,
                    "exit_code": result.exit_code,
                    "shell": context.shell.name,
                }

                # Determine severity based on exit code and tier
                if tier >= 3:
                    severity = "high"
                elif result.exit_code > 100:
                    severity = "medium"
                else:
                    severity = "low"

                context.session.track_mistake(
                    mistake_type="command_error",
                    description=f"Command failed with exit code {result.exit_code}",
                    correction="",  # Will be filled if user retries with different command
                    original_input=command,
                    context=context,
                    severity=severity,
                )

            # Track successful executions for pattern learning
            if result.success and hasattr(context.session, "preference_learner"):
                context.session.observe_coding_pattern(
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

    def _track_auto_correction(self, original: str, corrected: str, confidence: float, context: StrategyContext):
        """Track automatic command corrections for learning.

        Args:
            original: Original command with typo
            corrected: Corrected command
            confidence: Confidence score of correction
        """
        if not hasattr(context.session, "mistake_learner") or not context.session.mistake_learner:
            return

        try:
            context_data = {"confidence": confidence, "auto_corrected": True, "shell": context.shell.name}

            context.session.track_mistake(
                mistake_type="command_typo",
                description=f"Typo detected and auto-corrected (confidence: {confidence:.1%})",
                correction=corrected,
                original_input=original,
                context=context_data,
                severity="low",
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to track auto-correction: {e}")

    def _track_user_correction_acceptance(self, original: str, corrected: str, accepted: bool, context: StrategyContext):
        """Track whether user accepted a suggested correction.

        Args:
            original: Original command
            corrected: Suggested correction
            accepted: Whether user accepted the correction
        """
        if not hasattr(context.session, "behavior_engine") or not context.session.behavior_engine:
            return

        try:
            sentiment = 0.5 if accepted else -0.3
            feedback_text = f"User {'accepted' if accepted else 'rejected'} correction: {original} → {corrected}"

            context.session.record_user_feedback(
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


class CommandRouter:
    """Routes commands through tier validation and AI processing."""

    def __init__(self, session_mgr, shell) -> None:
        """Initialize with session manager and shell adapter."""
        self.session = session_mgr
        self.shell = shell
        self.validator: TierValidator = TierValidator(self.session.preferences)
        self.query_classifier: QueryClassifier = QueryClassifier()

        # Initialize the plugin dispatcher
        self.dispatcher: CommandDispatcher = CommandDispatcher(session_mgr)
        self.dispatcher.load_commands(
            [Path(__file__).parent.parent / "commands", Path.home() / ".isaac" / "commands"]
        )

        # Load routing strategies
        self.strategies = self._load_strategies()
        self.current_strategy = None

    def _load_strategies(self):
        """Load and sort routing strategies by priority."""
        strategies = [
            PipeStrategy(),
            CdStrategy(),
            ForceExecutionStrategy(),
            ExitQuitStrategy(),
            ClearStrategy(),
            ConfigStrategy(),
            ConfigConsoleStrategy(),
            MetaCommandStrategy(),
            DeviceRoutingStrategy(),
            ExitBlockerStrategy(),
            TaskModeStrategy(),
            AgenticModeStrategy(),
            NaturalLanguageStrategy(),
            UnixAliasStrategy(),
            TierExecutionStrategy(),
        ]
        strategies.sort(key=lambda s: s.get_priority())
        return strategies

    @property
    def strategies(self):
        """Get the list of routing strategies."""
        return self._strategies

    @strategies.setter
    def strategies(self, value):
        self._strategies = value

    @property
    def current_strategy(self):
        """Get the currently active strategy."""
        return self._current_strategy

    @current_strategy.setter
    def current_strategy(self, value):
        self._current_strategy = value

    def route_command(self, input_text: str) -> CommandResult:
        """
        Route command through appropriate processing pipeline.

        Args:
            input_text: Raw user input

        Returns:
            CommandResult with execution results
        """
        context = StrategyContext(
            self.session, self.shell, self.validator, self.query_classifier, self.dispatcher
        )
        context.router = self  # For recursive calls

        for strategy in self.strategies:
            if strategy.can_handle(input_text):
                self.current_strategy = strategy
                return strategy.execute(input_text, context)

        # Should never reach here - TierExecutionStrategy should handle all
        return CommandResult(
            success=False,
            output="Isaac > No strategy could handle command",
            exit_code=-1
        )

    def get_help(self) -> str:
        """Get help text for available commands."""
        help_text = "Isaac Command Router - Available command types:\n"
        for strategy in self.strategies:
            strategy_help = strategy.get_help() if hasattr(strategy, 'get_help') else ""
            if strategy_help:
                help_text += f"  • {strategy_help}\n"
        return help_text
