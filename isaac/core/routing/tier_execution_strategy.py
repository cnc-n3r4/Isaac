"""
Tier-based execution strategy - default strategy for regular commands.
"""

from typing import Any, Dict

from isaac.adapters.base_adapter import CommandResult
from isaac.core.routing.strategy import CommandStrategy


class TierExecutionStrategy(CommandStrategy):
    """Strategy for executing commands through tier-based safety system."""

    def can_handle(self, input_text: str) -> bool:
        """This is the default strategy - always returns True."""
        return True

    def execute(self, input_text: str, context: Dict[str, Any]) -> CommandResult:
        """Execute command through tier-based safety system."""
        validator = context.get("validator")
        if not validator:
            # No validator - just execute
            return self.shell.execute(input_text)

        # Get safety tier
        tier = validator.get_tier(input_text)

        if tier == 1:
            # Tier 1: Instant execution
            result = self.shell.execute(input_text)
            self._track_command_execution(input_text, result, tier=1, context=context)
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
                    context=context,
                )

                result = self.shell.execute(correction["corrected"])
                self._track_command_execution(
                    correction["corrected"], result, tier=2, context=context, was_corrected=True
                )
                return result
            else:
                # No typo or low confidence - execute as-is
                result = self.shell.execute(input_text)
                self._track_command_execution(input_text, result, tier=2, context=context)
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
                        context=context,
                    )
                    result = self.shell.execute(correction["corrected"])
                    self._track_command_execution(
                        correction["corrected"], result, tier=2.5, context=context
                    )
                    return result
            else:
                # No correction needed or low confidence - just confirm original
                confirmed = self._confirm(f"Execute: {input_text}?")
                if confirmed:
                    result = self.shell.execute(input_text)
                    self._track_command_execution(input_text, result, tier=2.5, context=context)
                    return result

            # User aborted
            return CommandResult(success=False, output="Isaac > Aborted.", exit_code=-1)

        elif tier == 3:
            # Tier 3: Validation required (AI validation)
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

    def get_help(self) -> str:
        """Get help text for tier execution."""
        return "Regular commands are executed through a 4-tier safety system"

    def get_priority(self) -> int:
        """Lowest priority - default catch-all strategy."""
        return 100

    def _confirm(self, message: str) -> bool:
        """Get user confirmation (placeholder - always return True for now)."""
        # TODO: Implement actual user input
        print(f"{message} (y/n): y")
        return True

    def _track_command_execution(
        self,
        command: str,
        result: CommandResult,
        tier: float,
        context: Dict[str, Any],
        was_corrected: bool = False,
    ):
        """Track command execution for learning system."""
        if not hasattr(self.session, "mistake_learner") or not self.session.mistake_learner:
            return

        try:
            # Track failed commands as mistakes
            if not result.success and result.exit_code != 0:
                ctx = {
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
                    context=ctx,
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

    def _track_auto_correction(
        self, original: str, corrected: str, confidence: float, context: Dict[str, Any]
    ):
        """Track automatic command corrections for learning."""
        if not hasattr(self.session, "mistake_learner") or not self.session.mistake_learner:
            return

        try:
            ctx = {"confidence": confidence, "auto_corrected": True, "shell": self.shell.name}

            self.session.track_mistake(
                mistake_type="command_typo",
                description=f"Typo detected and auto-corrected (confidence: {confidence:.1%})",
                correction=corrected,
                original_input=original,
                context=ctx,
                severity="low",
            )

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Failed to track auto-correction: {e}")

    def _track_user_correction_acceptance(
        self, original: str, corrected: str, accepted: bool, context: Dict[str, Any]
    ):
        """Track whether user accepted a suggested correction."""
        if not hasattr(self.session, "behavior_engine") or not self.session.behavior_engine:
            return

        try:
            sentiment = 0.5 if accepted else -0.3
            feedback_text = (
                f"User {'accepted' if accepted else 'rejected'} correction: {original} → {corrected}"
            )

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
