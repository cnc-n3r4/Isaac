#!/usr/bin/env python
"""
Analytics System Demo

Demonstrates the capabilities of Isaac's Advanced Analytics System.
"""

import os
import sys
import time
import tempfile

# Add Isaac to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from isaac.analytics import (
    AnalyticsManager,
    ProductivityTracker,
    CodeQualityTracker,
    LearningTracker,
    TeamTracker,
    DashboardBuilder,
    ReportExporter,
    AnalyticsDatabase
)


def demo_productivity_tracking():
    """Demonstrate productivity tracking"""
    print("\n" + "=" * 80)
    print("PRODUCTIVITY TRACKING DEMO".center(80))
    print("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = AnalyticsDatabase(os.path.join(tmpdir, "demo.db"))
        tracker = ProductivityTracker(db)

        # Simulate command executions
        print("📊 Recording command executions...")
        commands = [
            ('build', 5.0, 30.0),
            ('test', 3.0, 15.0),
            ('deploy', 10.0, 60.0),
            ('lint', 2.0, 10.0)
        ]

        for cmd, exec_time, manual_time in commands:
            tracker.record_command_execution(cmd, exec_time, manual_time)
            print(f"  ✓ {cmd}: {exec_time}s (saved {manual_time - exec_time:.1f}s)")

        # Record automation
        print("\n🤖 Recording automation runs...")
        tracker.record_automation_run('ci_pipeline', 10, 600.0)
        print("  ✓ CI pipeline: 10 steps, 10 minutes saved")

        # Get snapshot
        snapshot = tracker.get_current_snapshot()
        print(f"\n📈 Current Productivity:")
        print(f"  Commands Executed:   {snapshot.commands_executed}")
        print(f"  Time Saved:          {snapshot.time_saved / 60:.1f} minutes")
        print(f"  Automation Runs:     {snapshot.automation_runs}")
        print(f"  Efficiency Score:    {snapshot.efficiency_score:.1f}%")


def demo_code_quality_tracking():
    """Demonstrate code quality tracking"""
    print("\n" + "=" * 80)
    print("CODE QUALITY TRACKING DEMO".center(80))
    print("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create sample Python file
        sample_file = os.path.join(tmpdir, "sample.py")
        with open(sample_file, 'w') as f:
            f.write('''
def calculate_sum(numbers):
    """Calculate sum of numbers"""
    total = 0
    for num in numbers:
        total += num
    return total

class Calculator:
    """A simple calculator"""

    def add(self, a, b):
        """Add two numbers"""
        return a + b

    def multiply(self, a, b):
        """Multiply two numbers"""
        return a * b
''')

        db = AnalyticsDatabase(os.path.join(tmpdir, "demo.db"))
        tracker = CodeQualityTracker(db)

        print("📊 Analyzing Python file...")
        analysis = tracker.analyze_file(sample_file)

        print(f"\n✨ Code Quality Analysis:")
        print(f"  Quality Score:       {analysis['quality_score']:.1f}%")
        print(f"  Lines of Code:       {analysis['lines']}")
        print(f"  Functions:           {analysis['functions']}")
        print(f"  Classes:             {analysis['classes']}")
        print(f"  Docstrings:          {analysis['docstrings']}")
        print(f"  Complexity:          {analysis['complexity_score']:.1f}%")
        print(f"  Maintainability:     {analysis['maintainability_score']:.1f}%")

        # Record patterns
        print("\n📐 Recording pattern detections...")
        tracker.record_pattern_detection('iterator', sample_file, 0.9)
        tracker.record_pattern_detection('class_methods', sample_file, 0.85)
        print("  ✓ Iterator pattern detected")
        print("  ✓ Class methods pattern detected")


def demo_learning_tracking():
    """Demonstrate learning tracking"""
    print("\n" + "=" * 80)
    print("LEARNING ANALYTICS DEMO".center(80))
    print("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = AnalyticsDatabase(os.path.join(tmpdir, "demo.db"))
        tracker = LearningTracker(db)

        print("🧠 Recording learned patterns...")
        patterns = [
            ('singleton', 'design_pattern', 0.9),
            ('factory', 'design_pattern', 0.85),
            ('observer', 'design_pattern', 0.8)
        ]

        for pattern, type, conf in patterns:
            tracker.record_pattern_learned(pattern, type, conf)
            print(f"  ✓ {pattern} pattern (confidence: {conf:.0%})")

        print("\n🎯 Recording user preferences...")
        preferences = [
            ('indentation', '4 spaces', 0.95),
            ('quote_style', 'single', 0.9),
            ('import_order', 'alphabetical', 0.85)
        ]

        for pref, value, conf in preferences:
            tracker.record_preference_adaptation(pref, value, conf)
            print(f"  ✓ {pref}: {value}")

        # Get snapshot
        snapshot = tracker.get_current_snapshot()
        print(f"\n📚 Learning Progress:")
        print(f"  Patterns Learned:    {snapshot.patterns_learned}")
        print(f"  Preferences Adapted: {snapshot.preferences_adapted}")
        print(f"  Learning Rate:       {snapshot.learning_rate:.1f}%")
        print(f"  Adaptation Score:    {snapshot.adaptation_score:.1f}%")


def demo_team_tracking():
    """Demonstrate team tracking"""
    print("\n" + "=" * 80)
    print("TEAM ANALYTICS DEMO".center(80))
    print("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = AnalyticsDatabase(os.path.join(tmpdir, "demo.db"))
        tracker = TeamTracker('demo_team', db)

        print("👥 Recording team contributions...")
        tracker.record_contribution('alice', 'code_commit', 1.0)
        tracker.record_contribution('bob', 'code_commit', 1.0)
        tracker.record_contribution('charlie', 'documentation', 1.0)
        print("  ✓ Alice: code commit")
        print("  ✓ Bob: code commit")
        print("  ✓ Charlie: documentation")

        print("\n👀 Recording code reviews...")
        tracker.record_code_review('bob', 'alice', 0.9)
        tracker.record_code_review('alice', 'bob', 0.85)
        print("  ✓ Bob reviewed Alice's code")
        print("  ✓ Alice reviewed Bob's code")

        print("\n🤝 Recording pair programming...")
        tracker.record_pair_programming('alice', 'charlie', 60, 0.9)
        print("  ✓ Alice & Charlie paired for 60 minutes")

        # Get snapshot
        snapshot = tracker.get_current_snapshot()
        print(f"\n📊 Team Metrics:")
        print(f"  Active Members:      {snapshot.active_members}")
        print(f"  Contributions:       {snapshot.total_contributions}")
        print(f"  Collaboration Score: {snapshot.collaboration_score:.1f}%")


def demo_dashboard():
    """Demonstrate dashboard rendering"""
    print("\n" + "=" * 80)
    print("DASHBOARD DEMO".center(80))
    print("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = AnalyticsDatabase(os.path.join(tmpdir, "demo.db"))

        # Add some sample data
        db.record_productivity_metric('command_execution', 'build', 1.0)
        db.record_productivity_metric('time_saved', 'automation', 300.0)
        db.record_code_quality_metric('quality_score', 'overall', 85.0)
        db.record_learning_metric('pattern_learned', 'singleton', 0.9)

        builder = DashboardBuilder(db)

        print("📊 Available Dashboards:")
        for dashboard_id in builder.list_dashboards():
            print(f"  • {dashboard_id}")

        print("\n" + "=" * 80)
        print("OVERVIEW DASHBOARD".center(80))
        print("=" * 80)
        dashboard = builder.render_dashboard('overview', width=80)
        print(dashboard)


def demo_export():
    """Demonstrate report export"""
    print("\n" + "=" * 80)
    print("REPORT EXPORT DEMO".center(80))
    print("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db = AnalyticsDatabase(os.path.join(tmpdir, "demo.db"))

        # Add sample data
        db.record_productivity_metric('command_execution', 'build', 1.0)
        db.record_productivity_metric('time_saved', 'test', 10.0)

        exporter = ReportExporter(db)

        print("📄 Exporting reports...")

        # JSON export
        json_file = os.path.join(tmpdir, "report.json")
        exporter.export_report('productivity', 'json', json_file)
        print(f"  ✓ JSON: {json_file}")

        # Markdown export
        md_file = os.path.join(tmpdir, "report.md")
        exporter.export_report('productivity', 'markdown', md_file)
        print(f"  ✓ Markdown: {md_file}")

        # HTML export
        html_file = os.path.join(tmpdir, "report.html")
        exporter.export_report('productivity', 'html', html_file)
        print(f"  ✓ HTML: {html_file}")

        # Show markdown preview
        print("\n📝 Markdown Report Preview:")
        print("-" * 80)
        with open(md_file, 'r') as f:
            preview = f.read()[:500]
            print(preview)
            if len(preview) == 500:
                print("\n[... truncated ...]")
        print("-" * 80)


def demo_full_system():
    """Demonstrate full analytics system"""
    print("\n" + "=" * 80)
    print("FULL ANALYTICS SYSTEM DEMO".center(80))
    print("=" * 80 + "\n")

    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "demo.db")
        manager = AnalyticsManager(db_path=db_path)

        print("🚀 Simulating Isaac usage...")

        # Commands
        print("\n1. Executing commands...")
        manager.record_command_execution('build', 5.0, True)
        manager.record_command_execution('test', 3.0, True)
        print("  ✓ 2 commands executed")

        # Code analysis
        print("\n2. Analyzing code...")
        sample_file = os.path.join(tmpdir, "demo.py")
        with open(sample_file, 'w') as f:
            f.write('def hello():\n    """Say hello"""\n    return "Hello!"\n')
        manager.code_quality.analyze_file(sample_file)
        print("  ✓ Code analyzed")

        # Learning
        print("\n3. Learning patterns...")
        manager.record_pattern_learned('factory', 'design_pattern', 0.85)
        manager.record_user_preference('indentation', '4 spaces', 0.9)
        print("  ✓ Patterns and preferences learned")

        # Get summary
        print("\n" + "=" * 80)
        summary = manager.get_summary()

        print("📊 ANALYTICS SUMMARY:")
        print(f"\n⚡ Productivity:")
        print(f"  Efficiency Score: {summary['productivity']['efficiency_score']:.1f}%")
        print(f"  Commands:         {summary['productivity']['commands_executed']}")

        print(f"\n✨ Code Quality:")
        print(f"  Quality Score:    {summary['code_quality']['quality_score']:.1f}%")
        print(f"  Files Analyzed:   {summary['code_quality']['files_analyzed']}")

        print(f"\n🧠 Learning:")
        print(f"  Learning Rate:    {summary['learning']['learning_rate']:.1f}%")
        print(f"  Patterns Learned: {summary['learning']['patterns_learned']}")

        print(f"\n👥 Team:")
        print(f"  Active Members:   {summary['team']['active_members']}")

        # Get insights
        insights = manager.get_insights()
        if insights:
            print("\n💡 Insights:")
            for insight in insights[:3]:
                print(f"  • {insight}")

        print("\n" + "=" * 80)


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("ISAAC ADVANCED ANALYTICS SYSTEM DEMO".center(80))
    print("=" * 80)

    demos = [
        ("Productivity Tracking", demo_productivity_tracking),
        ("Code Quality Tracking", demo_code_quality_tracking),
        ("Learning Analytics", demo_learning_tracking),
        ("Team Analytics", demo_team_tracking),
        ("Dashboard Builder", demo_dashboard),
        ("Report Export", demo_export),
        ("Full System Integration", demo_full_system)
    ]

    for name, demo_func in demos:
        try:
            demo_func()
        except Exception as e:
            print(f"\n❌ Error in {name}: {str(e)}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 80)
    print("DEMO COMPLETE!".center(80))
    print("=" * 80)
    print("\nFor more information, see isaac/analytics/README.md")
    print()


if __name__ == '__main__':
    main()
