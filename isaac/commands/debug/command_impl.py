"""
Debug Command - Standardized Implementation

Execute debug analysis commands for troubleshooting and diagnostics.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add isaac to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from isaac.commands.base import BaseCommand, CommandManifest, FlagParser, CommandResponse
from isaac.debugging.debug_command import DebugCommand as DebugProcessor


class DebugCommand(BaseCommand):
    """Debug analysis and troubleshooting command"""

    def execute(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> CommandResponse:
        """
        Execute debug command.

        Args:
            args: Command arguments
            context: Optional execution context

        Returns:
            CommandResponse with debug analysis results
        """
        try:
            parser = FlagParser(args)

            # Parse debug options
            mode = parser.get_flag("mode", default="full")
            command = parser.get_flag("command", default="")
            error = parser.get_flag("error", default="")
            output_path = parser.get_flag("output")

            # If no flags, try positional arguments
            if not command and parser.get_positional(0):
                command = parser.get_positional(0)

            # Execute debug analysis
            debug_processor = DebugProcessor()

            result_data = None

            if mode == "full":
                # Comprehensive debug analysis
                result_data = debug_processor.execute_debug_assistance(command, error)
                formatted = self._format_full_debug_output(result_data)

            elif mode == "quick":
                # Quick debug analysis
                result_data = debug_processor.execute_quick_debug(command, error)
                formatted = self._format_quick_debug_output(result_data)

            elif mode == "performance":
                # Performance analysis
                result_data = debug_processor.execute_performance_analysis(command)
                formatted = self._format_performance_output(result_data)

            elif mode == "tests":
                # Test generation
                diagnostic_data = {"command": command} if command else {}
                result_data = debug_processor.execute_test_generation(error, diagnostic_data)
                formatted = self._format_test_generation_output(result_data)

            elif mode == "history":
                # Debug history summary
                result_data = debug_processor.get_debug_history_summary()
                formatted = self._format_history_output(result_data)

            else:
                return CommandResponse(
                    success=False,
                    error=f"Unknown debug mode: {mode}. Use: full, quick, performance, tests, or history",
                    metadata={"error_code": "INVALID_MODE"}
                )

            # Export detailed report if requested
            if output_path and result_data:
                output_file = Path(output_path)
                success = debug_processor.export_debug_report(result_data, output_file)
                if success:
                    formatted += f"\n\n📄 Detailed report exported to: {output_file}"
                else:
                    formatted += f"\n\n❌ Failed to export report to: {output_file}"

            return CommandResponse(
                success=True,
                data=formatted,
                metadata={"mode": mode, "has_output": bool(output_path)}
            )

        except Exception as e:
            return CommandResponse(
                success=False,
                error=f"Debug analysis failed: {str(e)}",
                metadata={"error_code": "DEBUG_ERROR"}
            )

    def _format_full_debug_output(self, result: Dict[str, Any]) -> str:
        """Format comprehensive debug output."""
        output_lines = []

        # Header
        output_lines.append("🔧 ISAAC COMPREHENSIVE DEBUG ANALYSIS")
        output_lines.append("=" * 50)

        # Summary
        if "summary" in result:
            output_lines.append(result["summary"])
            output_lines.append("")

        # Investigation Results
        investigation = result.get("investigation", {})
        if investigation:
            output_lines.append("🔍 INVESTIGATION RESULTS")
            output_lines.append("-" * 25)

            issues = investigation.get("issues", [])
            if issues:
                output_lines.append(f"Found {len(issues)} potential issues:")
                for i, issue in enumerate(issues[:5], 1):  # Show top 5
                    output_lines.append(f"  {i}. {issue}")
            else:
                output_lines.append("No issues detected")

            # System info
            system_info = investigation.get("system_info", {})
            if system_info:
                output_lines.append(f"Platform: {system_info.get('platform', 'unknown')}")
                output_lines.append(f"Python: {system_info.get('python_version', 'unknown')}")

            output_lines.append("")

        # Root Cause Analysis
        root_cause = result.get("root_cause", {})
        if root_cause:
            output_lines.append("🎯 ROOT CAUSE ANALYSIS")
            output_lines.append("-" * 22)

            if "root_cause" in root_cause:
                output_lines.append(f"Root Cause: {root_cause['root_cause']}")

            confidence = root_cause.get("confidence", 0)
            output_lines.append(f"Confidence: {confidence:.1%}")

            hypotheses = root_cause.get("hypotheses", [])
            if hypotheses:
                output_lines.append("Top hypotheses:")
                for i, hyp in enumerate(hypotheses[:3], 1):
                    output_lines.append(
                        f"  {i}. {hyp.get('description', 'Unknown')} "
                        f"(confidence: {hyp.get('confidence', 0):.1%})"
                    )

            output_lines.append("")

        # Fix Suggestions
        fix_suggestions = result.get("fix_suggestions", {})
        if fix_suggestions:
            output_lines.append("💡 FIX SUGGESTIONS")
            output_lines.append("-" * 17)

            primary_fix = fix_suggestions.get("primary_fix")
            if primary_fix:
                output_lines.append(f"PRIMARY FIX: {primary_fix['title']}")
                output_lines.append(f"Description: {primary_fix['description']}")
                output_lines.append(f"Confidence: {primary_fix['confidence']:.1%}")
                output_lines.append(f"Time Estimate: {primary_fix['estimated_time']}")

                commands = primary_fix.get("commands", [])
                if commands:
                    output_lines.append("Commands to run:")
                    for cmd in commands:
                        output_lines.append(f"  {cmd}")

                risks = primary_fix.get("risks", [])
                if risks:
                    output_lines.append("⚠️  Risks:")
                    for risk in risks:
                        output_lines.append(f"  • {risk}")

            alternative_fixes = fix_suggestions.get("alternative_fixes", [])
            if alternative_fixes:
                output_lines.append(f"ALTERNATIVE FIXES: {len(alternative_fixes)} available")
                for i, fix in enumerate(alternative_fixes[:2], 1):  # Show top 2
                    output_lines.append(f"  {i}. {fix['title']} (confidence: {fix['confidence']:.1%})")

            output_lines.append("")

        return "\n".join(output_lines)

    def _format_quick_debug_output(self, result: Dict[str, Any]) -> str:
        """Format quick debug output."""
        output_lines = []

        output_lines.append("⚡ ISAAC QUICK DEBUG ANALYSIS")
        output_lines.append("=" * 35)

        # Immediate fixes
        immediate_fixes = result.get("immediate_fixes", {})
        primary_fix = immediate_fixes.get("primary_fix")

        if primary_fix:
            output_lines.append("💡 IMMEDIATE FIX:")
            output_lines.append(f"  {primary_fix['title']}")
            output_lines.append(f"  Confidence: {primary_fix['confidence']:.1%}")

            commands = primary_fix.get("commands", [])
            if commands:
                output_lines.append("  Commands:")
                for cmd in commands[:2]:  # Show first 2 commands
                    output_lines.append(f"    {cmd}")

        return "\n".join(output_lines)

    def _format_performance_output(self, result: Dict[str, Any]) -> str:
        """Format performance analysis output."""
        output_lines = []

        output_lines.append("📊 ISAAC PERFORMANCE ANALYSIS")
        output_lines.append("=" * 32)

        avg_perf = result.get("average_performance", {})
        if avg_perf:
            output_lines.append("AVERAGE PERFORMANCE:")
            output_lines.append(f"  CPU Usage: {avg_perf.get('cpu_usage', 0):.1f}%")
            output_lines.append(f"  Memory Usage: {avg_perf.get('memory_usage', 0):.1f}%")
            output_lines.append(f"  Duration: {avg_perf.get('duration', 0):.2f}s")

        bottlenecks = result.get("bottlenecks", [])
        if bottlenecks:
            output_lines.append("")
            output_lines.append("BOTTLENECKS:")
            for bottleneck in bottlenecks:
                output_lines.append(f"  • {bottleneck}")

        optimizations = result.get("optimization_suggestions", [])
        if optimizations:
            output_lines.append("")
            output_lines.append("OPTIMIZATION SUGGESTIONS:")
            for i, opt in enumerate(optimizations[:3], 1):
                output_lines.append(f"  {i}. {opt['title']} ({opt['impact']} impact)")
                output_lines.append(f"     {opt['description']}")

        return "\n".join(output_lines)

    def _format_test_generation_output(self, result: Dict[str, Any]) -> str:
        """Format test generation output."""
        output_lines = []

        output_lines.append("🧪 ISAAC TEST GENERATION")
        output_lines.append("=" * 26)

        # Bug reproduction test
        bug_test = result.get("bug_reproduction_test", {})
        if bug_test:
            output_lines.append("BUG REPRODUCTION TEST:")
            output_lines.append(f"  {bug_test.get('bug_id', 'unknown')}")
            output_lines.append(f"  Success Criteria: {bug_test.get('success_criteria', 'unknown')}")

        # Regression tests
        regression = result.get("regression_tests", {})
        test_count = regression.get("test_count", 0)
        if test_count > 0:
            output_lines.append("")
            output_lines.append(f"REGRESSION TESTS: {test_count} tests generated")

        # Edge case tests
        edge_tests = result.get("edge_case_tests", [])
        if edge_tests:
            output_lines.append("")
            output_lines.append(f"EDGE CASE TESTS: {len(edge_tests)} tests generated")

        return "\n".join(output_lines)

    def _format_history_output(self, result: Dict[str, Any]) -> str:
        """Format debug history output."""
        output_lines = []

        output_lines.append("📚 ISAAC DEBUG HISTORY SUMMARY")
        output_lines.append("=" * 33)

        insights = result.get("insights", [])
        if insights:
            output_lines.append(f"INSIGHTS ({len(insights)} found):")
            for insight in insights[:3]:  # Show top 3
                output_lines.append(f"  • {insight['description']}")

        command_stats = result.get("command_stats", {})
        if command_stats:
            output_lines.append("")
            output_lines.append("COMMAND DEBUG STATS:")
            for cmd, stats in command_stats.items():
                success_rate = stats.get("success_rate", 0)
                sessions = stats.get("total_debug_sessions", 0)
                output_lines.append(f"  {cmd}: {success_rate:.1%} success ({sessions} sessions)")

        return "\n".join(output_lines)

    def get_manifest(self) -> CommandManifest:
        """Get command manifest"""
        return CommandManifest(
            name="debug",
            description="Debug analysis and troubleshooting for commands and errors",
            usage="/debug [--mode <mode>] [--command <cmd>] [--error <error>] [--output <file>]",
            examples=[
                "/debug --mode full --command 'npm install' --error 'EACCES'",
                "/debug --mode quick --command 'python script.py'",
                "/debug --mode performance --command 'pytest tests/'",
                "/debug --mode tests --error 'AssertionError'",
                "/debug --mode history"
            ],
            tier=2,  # Needs validation - reads system state
            aliases=["dbg", "diagnose"],
            category="system"
        )
