"""
Debug Command Runner - Execute debug analysis commands
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from isaac.debugging.debug_command import DebugCommand


def execute_debug(args: Dict[str, Any]) -> str:
    """Execute debug analysis based on arguments.

    Args:
        args: Command arguments from Isaac

    Returns:
        Formatted debug results
    """
    debug_cmd = DebugCommand()

    mode = args.get("mode", "full")
    command = args.get("command", "")
    error = args.get("error", "")
    output_path = args.get("output")

    try:
        if mode == "full":
            # Comprehensive debug analysis
            result = debug_cmd.execute_debug_assistance(command, error)

        elif mode == "quick":
            # Quick debug analysis
            result = debug_cmd.execute_quick_debug(command, error)

        elif mode == "performance":
            # Performance analysis
            result = debug_cmd.execute_performance_analysis(command)

        elif mode == "tests":
            # Test generation
            diagnostic_data = {"command": command} if command else {}
            result = debug_cmd.execute_test_generation(error, diagnostic_data)

        elif mode == "history":
            # Debug history summary
            result = debug_cmd.get_debug_history_summary()

        else:
            return (
                f"❌ Unknown debug mode: {mode}. Use: full, quick, performance, tests, or history"
            )

        # Format output
        output = format_debug_output(result, mode)

        # Export detailed report if requested
        if output_path:
            output_file = Path(output_path)
            success = debug_cmd.export_debug_report(result, output_file)
            if success:
                output += f"\n\n📄 Detailed report exported to: {output_file}"
            else:
                output += f"\n\n❌ Failed to export report to: {output_file}"

        return output

    except Exception as e:
        return f"❌ Debug analysis failed: {str(e)}"


def format_debug_output(result: Dict[str, Any], mode: str) -> str:
    """Format debug results for display.

    Args:
        result: Debug analysis results
        mode: Analysis mode

    Returns:
        Formatted output string
    """
    if mode == "full":
        return format_full_debug_output(result)
    elif mode == "quick":
        return format_quick_debug_output(result)
    elif mode == "performance":
        return format_performance_output(result)
    elif mode == "tests":
        return format_test_generation_output(result)
    elif mode == "history":
        return format_history_output(result)
    else:
        return json.dumps(result, indent=2)


def format_full_debug_output(result: Dict[str, Any]) -> str:
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

    # Performance Analysis
    performance = result.get("performance_analysis", {})
    if performance and "duration" in performance:
        output_lines.append("📊 PERFORMANCE ANALYSIS")
        output_lines.append("-" * 23)

        output_lines.append(f"Execution Time: {performance['duration']:.2f} seconds")
        output_lines.append(f"CPU Usage: {performance.get('cpu_usage', 0):.1f}%")
        output_lines.append(f"Memory Usage: {performance.get('memory_usage', 0):.1f}%")

        bottlenecks = performance.get("bottlenecks", [])
        if bottlenecks:
            output_lines.append("Bottlenecks identified:")
            for bottleneck in bottlenecks:
                output_lines.append(f"  • {bottleneck}")

        recommendations = performance.get("recommendations", [])
        if recommendations:
            output_lines.append("Recommendations:")
            for rec in recommendations[:3]:
                output_lines.append(f"  • {rec}")

        output_lines.append("")

    # Historical Insights
    historical = result.get("historical_insights", {})
    if historical:
        output_lines.append("📚 HISTORICAL INSIGHTS")
        output_lines.append("-" * 21)

        similar_solutions = historical.get("similar_solutions", [])
        if similar_solutions:
            output_lines.append(f"Found {len(similar_solutions)} similar past issues")
            top_solution = similar_solutions[0]
            output_lines.append(
                f"Top historical solution (confidence: {top_solution['confidence']:.1%}):"
            )
            output_lines.append(f"  {top_solution['solution']}")

        command_stats = historical.get("command_stats", {})
        if command_stats:
            success_rate = command_stats.get("success_rate", 0)
            avg_time = command_stats.get("avg_resolution_time", 0)
            output_lines.append(
                f"Command debug stats: {success_rate:.1%} success rate, "
                f"{avg_time:.1f}s avg resolution time"
            )

        output_lines.append("")

    return "\n".join(output_lines)


def format_quick_debug_output(result: Dict[str, Any]) -> str:
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

    # Historical solutions
    historical = result.get("historical_solutions", [])
    if historical:
        output_lines.append("")
        output_lines.append("📚 HISTORICAL SOLUTIONS:")
        for i, solution in enumerate(historical[:2], 1):  # Show top 2
            output_lines.append(f"  {i}. {solution['solution'][:80]}...")
            output_lines.append(f"     Confidence: {solution['confidence']:.1%}")

    return "\n".join(output_lines)


def format_performance_output(result: Dict[str, Any]) -> str:
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


def format_test_generation_output(result: Dict[str, Any]) -> str:
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


def format_history_output(result: Dict[str, Any]) -> str:
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


if __name__ == "__main__":
    # For testing the command directly
    import sys

    if len(sys.argv) < 2:
        print("Usage: python run.py <mode> [command] [error]")
        sys.exit(1)

    mode = sys.argv[1]
    command = sys.argv[2] if len(sys.argv) > 2 else ""
    error = sys.argv[3] if len(sys.argv) > 3 else ""

    args = {"mode": mode, "command": command, "error": error}

    result = execute_debug(args)
    print(result)
