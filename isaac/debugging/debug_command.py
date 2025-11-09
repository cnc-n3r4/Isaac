"""
Debug Command - Integrated debugging interface for Isaac
Provides comprehensive debugging assistance with investigation, analysis, and fix suggestions
"""

import time
from typing import Dict, Any
from pathlib import Path
from dataclasses import asdict

from isaac.debugging.auto_investigator import AutoInvestigator
from isaac.debugging.root_cause_analyzer import RootCauseAnalyzer
from isaac.debugging.fix_suggester import FixSuggester
from isaac.debugging.performance_profiler import PerformanceProfiler
from isaac.debugging.test_generator import TestGenerator
from isaac.debugging.debug_history import DebugHistoryManager, DebugSession


class DebugCommand:
    """Integrated debugging command for Isaac."""

    def __init__(self):
        """Initialize the debug command."""
        self.investigator = AutoInvestigator()
        self.analyzer = RootCauseAnalyzer()
        self.fix_suggester = FixSuggester()
        self.performance_profiler = PerformanceProfiler()
        self.test_generator = TestGenerator()
        self.history_manager = DebugHistoryManager()

    def execute_debug_assistance(self, command: str, error_message: str = None,
                               context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute comprehensive debug assistance.

        Args:
            command: The command that failed
            error_message: The error message (optional)
            context: Additional context information

        Returns:
            Complete debug analysis and suggestions
        """
        context = context or {}
        start_time = time.time()

        result = {
            'command': command,
            'error_message': error_message,
            'timestamp': start_time,
            'investigation': {},
            'root_cause': {},
            'fix_suggestions': {},
            'performance_analysis': {},
            'test_generation': {},
            'historical_insights': {},
            'summary': {}
        }

        try:
            # Step 1: Gather diagnostic data
            print("🔍 Gathering diagnostic information...")
            diagnostic_data = self.investigator.gather_diagnostic_data(command, error_message, context)
            result['investigation'] = diagnostic_data

            # Step 2: Analyze root cause
            print("🎯 Analyzing root cause...")
            root_cause_analysis = self.analyzer.analyze_root_cause(
                error_message or diagnostic_data.get('error_message', ''),
                diagnostic_data
            )
            result['root_cause'] = asdict(root_cause_analysis)

            # Step 3: Generate fix suggestions
            print("💡 Generating fix suggestions...")
            fix_recommendations = self.fix_suggester.suggest_fixes(
                error_message or diagnostic_data.get('error_message', ''),
                diagnostic_data,
                root_cause_analysis.root_cause if root_cause_analysis else None
            )
            result['fix_suggestions'] = {
                'primary_fix': asdict(fix_recommendations.primary_fix) if fix_recommendations.primary_fix else None,
                'alternative_fixes': [asdict(fix) for fix in fix_recommendations.alternative_fixes],
                'preventive_fixes': [asdict(fix) for fix in fix_recommendations.preventive_fixes],
                'context_info': fix_recommendations.context_info
            }

            # Step 4: Performance profiling (if command is available)
            print("📊 Analyzing performance...")
            try:
                self.performance_profiler.start_profiling(command, context)
                # Simulate command execution for profiling
                time.sleep(0.1)  # Brief pause for profiling
                profile = self.performance_profiler.stop_profiling()
                if profile:
                    result['performance_analysis'] = asdict(profile)
                    result['performance_analysis']['report'] = self.performance_profiler.generate_performance_report(profile)
            except Exception as e:
                result['performance_analysis'] = {'error': str(e)}

            # Step 5: Generate tests for bug reproduction
            print("🧪 Generating reproduction tests...")
            if error_message:
                bug_test = self.test_generator.generate_bug_reproduction_test(
                    error_message, diagnostic_data, root_cause_analysis.root_cause if root_cause_analysis else None
                )
                result['test_generation'] = {
                    'bug_reproduction_test': asdict(bug_test),
                    'test_code': bug_test.test_code
                }

            # Step 6: Check historical insights
            print("📚 Checking debug history...")
            historical_solutions = self.history_manager.get_solution_suggestions(error_message or '', command)
            insights = self.history_manager.get_debugging_insights()
            command_stats = self.history_manager.get_command_debugging_stats(command)

            result['historical_insights'] = {
                'similar_solutions': historical_solutions,
                'insights': [asdict(insight) for insight in insights],
                'command_stats': command_stats
            }

            # Step 7: Record this debug session
            resolution_time = time.time() - start_time
            debug_session = DebugSession(
                session_id=f"debug_{int(start_time)}",
                timestamp=start_time,
                command=command,
                error_message=error_message or diagnostic_data.get('error_message', ''),
                root_cause=root_cause_analysis.root_cause if root_cause_analysis else 'unknown',
                solution=result['fix_suggestions'].get('primary_fix', {}).get('commands', ['No solution found'])[0],
                resolution_time=resolution_time,
                success=len(result['fix_suggestions'].get('primary_fix', {})) > 0,
                context=context,
                tags=['auto_debug', 'comprehensive_analysis']
            )
            self.history_manager.record_debug_session(debug_session)

            # Step 8: Generate summary
            result['summary'] = self._generate_debug_summary(result)

        except Exception as e:
            result['error'] = str(e)
            result['summary'] = f"Debug analysis failed: {str(e)}"

        return result

    def execute_quick_debug(self, command: str, error_message: str = None) -> Dict[str, Any]:
        """Execute quick debug analysis for immediate issues.

        Args:
            command: The command that failed
            error_message: The error message

        Returns:
            Quick debug results
        """
        result = {
            'command': command,
            'error_message': error_message,
            'quick_analysis': {},
            'immediate_fixes': {},
            'historical_solutions': {}
        }

        try:
            # Quick investigation
            diagnostic_data = self.investigator.gather_diagnostic_data(command, error_message)

            # Quick fix suggestions
            fix_recommendations = self.fix_suggester.suggest_fixes(
                error_message or diagnostic_data.get('error_message', ''), diagnostic_data
            )

            # Historical solutions
            historical_solutions = self.history_manager.get_solution_suggestions(
                error_message or '', command
            )

            result['quick_analysis'] = diagnostic_data
            result['immediate_fixes'] = {
                'primary_fix': asdict(fix_recommendations.primary_fix) if fix_recommendations.primary_fix else None,
                'alternative_fixes': [asdict(fix) for fix in fix_recommendations.alternative_fixes[:2]]  # Top 2 alternatives
            }
            result['historical_solutions'] = historical_solutions[:3]  # Top 3 historical solutions

        except Exception as e:
            result['error'] = str(e)

        return result

    def execute_performance_analysis(self, command: str, iterations: int = 3) -> Dict[str, Any]:
        """Execute detailed performance analysis.

        Args:
            command: The command to analyze
            iterations: Number of times to run the command

        Returns:
            Performance analysis results
        """
        result = {
            'command': command,
            'iterations': iterations,
            'profiles': [],
            'average_performance': {},
            'bottlenecks': [],
            'optimization_suggestions': []
        }

        try:
            profiles = []

            for i in range(iterations):
                print(f"📊 Running performance iteration {i + 1}/{iterations}...")

                # Start profiling
                self.performance_profiler.start_profiling(command)

                # Execute command (simulated)
                time.sleep(0.5)  # Simulate command execution

                # Stop profiling
                profile = self.performance_profiler.stop_profiling()
                if profile:
                    profiles.append(profile)

            if profiles:
                # Calculate averages
                avg_cpu = sum(p.cpu_usage for p in profiles) / len(profiles)
                avg_memory = sum(p.memory_usage for p in profiles) / len(profiles)
                avg_duration = sum(p.duration for p in profiles) / len(profiles)

                result['average_performance'] = {
                    'cpu_usage': avg_cpu,
                    'memory_usage': avg_memory,
                    'duration': avg_duration
                }

                # Collect all bottlenecks
                all_bottlenecks = []
                for profile in profiles:
                    all_bottlenecks.extend(profile.bottlenecks)
                result['bottlenecks'] = list(set(all_bottlenecks))

                # Get optimization suggestions
                optimizations = []
                for profile in profiles:
                    opts = self.performance_profiler.get_optimization_suggestions(profile)
                    optimizations.extend(opts)

                # Remove duplicates and sort by impact
                seen_solutions = set()
                unique_opts = []
                for opt in optimizations:
                    if opt.suggestion_id not in seen_solutions:
                        unique_opts.append(opt)
                        seen_solutions.add(opt.suggestion_id)

                unique_opts.sort(key=lambda x: x.impact, reverse=True)
                result['optimization_suggestions'] = [asdict(opt) for opt in unique_opts]

                result['profiles'] = [asdict(p) for p in profiles]

        except Exception as e:
            result['error'] = str(e)

        return result

    def execute_test_generation(self, error_message: str, diagnostic_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive tests for bug prevention.

        Args:
            error_message: The error message
            diagnostic_data: Diagnostic information

        Returns:
            Generated tests
        """
        result = {
            'error_message': error_message,
            'bug_reproduction_test': {},
            'regression_tests': {},
            'edge_case_tests': {},
            'performance_tests': {}
        }

        try:
            diagnostic_data = diagnostic_data or {}

            # Generate bug reproduction test
            bug_test = self.test_generator.generate_bug_reproduction_test(
                error_message, diagnostic_data
            )
            result['bug_reproduction_test'] = asdict(bug_test)

            # Generate regression test suite (would need error history)
            # For now, create a basic regression test
            regression_suite = self.test_generator.generate_regression_test_suite([
                {'error_message': error_message, 'command': diagnostic_data.get('command', '')}
            ])
            result['regression_tests'] = {
                'suite_name': regression_suite.suite_name,
                'test_count': len(regression_suite.test_cases),
                'tests': [asdict(test) for test in regression_suite.test_cases]
            }

            # Generate edge case tests
            command = diagnostic_data.get('command', 'unknown_command').split()[0]
            edge_tests = self.test_generator.generate_edge_case_tests(command, diagnostic_data)
            result['edge_case_tests'] = [asdict(test) for test in edge_tests]

            # Generate performance tests (would need performance profile)
            # For now, create basic performance tests
            perf_tests = self.test_generator.generate_performance_tests(command, {
                'duration': 1.0, 'cpu_usage': 50.0, 'memory_usage': 60.0
            })
            result['performance_tests'] = [asdict(test) for test in perf_tests]

        except Exception as e:
            result['error'] = str(e)

        return result

    def get_debug_history_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get summary of debug history and insights.

        Args:
            days: Number of days to look back

        Returns:
            Debug history summary
        """
        result = {
            'period_days': days,
            'insights': [],
            'command_stats': {},
            'pattern_summary': {}
        }

        try:
            # Get insights
            insights = self.history_manager.get_debugging_insights(days)
            result['insights'] = [asdict(insight) for insight in insights]

            # Get stats for common commands (this would be expanded in practice)
            common_commands = ['ls', 'cd', 'grep', 'find', 'python', 'pip']
            command_stats = {}
            for cmd in common_commands:
                stats = self.history_manager.get_command_debugging_stats(cmd, days)
                if stats['total_debug_sessions'] > 0:
                    command_stats[cmd] = stats

            result['command_stats'] = command_stats

            # Pattern summary
            with self.history_manager.db_path as db_path:
                import sqlite3
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.execute('''
                        SELECT error_pattern, COUNT(*) as count
                        FROM debug_patterns
                        WHERE last_seen > ?
                        GROUP BY error_pattern
                        ORDER BY count DESC
                        LIMIT 5
                    ''', (time.time() - (days * 24 * 3600),))

                    patterns = []
                    for row in cursor.fetchall():
                        patterns.append({
                            'error_pattern': row[0],
                            'occurrences': row[1]
                        })

                    result['pattern_summary'] = patterns

        except Exception as e:
            result['error'] = str(e)

        return result

    def _generate_debug_summary(self, debug_result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of debug results."""
        summary_parts = []

        # Basic info
        summary_parts.append(f"🔧 Debug Analysis Complete for: {debug_result['command']}")

        # Error summary
        if debug_result.get('error_message'):
            summary_parts.append(f"❌ Error: {debug_result['error_message'][:100]}...")

        # Investigation summary
        investigation = debug_result.get('investigation', {})
        if investigation:
            issues_found = len(investigation.get('issues', []))
            summary_parts.append(f"🔍 Found {issues_found} potential issues")

        # Root cause
        root_cause = debug_result.get('root_cause', {})
        if root_cause.get('root_cause'):
            summary_parts.append(f"🎯 Root Cause: {root_cause['root_cause'][:100]}...")

        # Fix suggestions
        fix_suggestions = debug_result.get('fix_suggestions', {})
        primary_fix = fix_suggestions.get('primary_fix')
        if primary_fix:
            summary_parts.append(f"💡 Primary Fix: {primary_fix['title']}")
            summary_parts.append(f"   Confidence: {primary_fix['confidence']:.1%}")

        # Performance
        performance = debug_result.get('performance_analysis', {})
        if performance and 'duration' in performance:
            summary_parts.append(f"📊 Performance: {performance['duration']:.2f}s execution time")

        # Historical insights
        historical = debug_result.get('historical_insights', {})
        similar_solutions = historical.get('similar_solutions', [])
        if similar_solutions:
            top_solution = similar_solutions[0]
            summary_parts.append(f"📚 Historical: {len(similar_solutions)} similar cases, "
                              f"top solution confidence: {top_solution['confidence']:.1%}")

        return "\n".join(summary_parts)

    def export_debug_report(self, debug_result: Dict[str, Any], output_path: Path) -> bool:
        """Export complete debug report to file.

        Args:
            debug_result: The debug analysis result
            output_path: Path to save the report

        Returns:
            True if successful
        """
        try:
            with open(output_path, 'w') as f:
                f.write("# Isaac Debug Report\n\n")
                f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

                f.write("## Summary\n")
                f.write(debug_result.get('summary', 'No summary available'))
                f.write("\n\n")

                # Write each section
                sections = [
                    ('investigation', 'Investigation Results'),
                    ('root_cause', 'Root Cause Analysis'),
                    ('fix_suggestions', 'Fix Suggestions'),
                    ('performance_analysis', 'Performance Analysis'),
                    ('test_generation', 'Generated Tests'),
                    ('historical_insights', 'Historical Insights')
                ]

                for section_key, section_title in sections:
                    section_data = debug_result.get(section_key, {})
                    if section_data:
                        f.write(f"## {section_title}\n")
                        f.write("```json\n")
                        f.write(json.dumps(section_data, indent=2))
                        f.write("\n```\n\n")

            return True

        except Exception as e:
            print(f"Error exporting debug report: {e}")
            return False