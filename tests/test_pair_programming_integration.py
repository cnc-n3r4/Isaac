"""
Integration tests for collaborative pair programming features (Phase 4.2)
Tests all components working together.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import time

from isaac.core.session_manager import SessionManager
from isaac.pairing import (
    PairProgrammingMode,
    TaskDivider,
    CodeReviewer,
    SuggestionSystem,
    PairingLearner,
    PairMetrics,
    PairRole,
    PairStyle,
    TaskPriority,
    TaskAssignee
)
from isaac.commands.pair.pair_command import PairCommand


class TestPairProgrammingIntegration(unittest.TestCase):
    """Integration tests for pair programming."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.session_manager = SessionManager()

        # Override data directories for testing
        self.original_home = Path.home()

    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_pairing_workflow(self):
        """Test complete pairing workflow from start to finish."""
        pair_mode = PairProgrammingMode(self.session_manager)
        task_divider = TaskDivider(self.session_manager)
        metrics_tracker = PairMetrics(self.session_manager)

        # 1. Start a session
        session = pair_mode.start_session(
            "Implement user authentication",
            PairStyle.DRIVER_NAVIGATOR,
            PairRole.NAVIGATOR
        )
        self.assertIsNotNone(session)
        self.assertEqual(session.task_description, "Implement user authentication")
        self.assertEqual(session.pair_style, PairStyle.DRIVER_NAVIGATOR.value)

        # 2. Divide task into subtasks
        tasks = task_divider.suggest_task_division(
            "Implement user authentication",
            {'files': ['auth.py'], 'type': 'feature'}
        )
        self.assertGreater(len(tasks), 0)

        # 3. Start a task
        first_task = tasks[0]
        success = task_divider.start_task(first_task.id)
        self.assertTrue(success)

        # 4. Track some file modifications
        pair_mode.add_file_touched('/tmp/auth.py')
        pair_mode.add_file_touched('/tmp/user_model.py')

        # 5. Record some metrics events
        metrics_tracker.record_event(session.id, 'suggestion_made', {'count': 1})
        metrics_tracker.record_event(session.id, 'suggestion_accepted', {'count': 1})
        metrics_tracker.record_event(session.id, 'code_review', {'file': '/tmp/auth.py'})

        # 6. Complete the task
        task_divider.complete_task(first_task.id, "Authentication implemented")

        # 7. Calculate metrics
        time.sleep(0.1)  # Small delay to ensure duration > 0
        session_data = {
            'start_time': session.start_time,
            'end_time': time.time(),
            'files_touched': session.files_touched,
            'tasks_total': len(tasks)
        }
        metrics = metrics_tracker.calculate_session_metrics(session.id, session_data)

        self.assertIsNotNone(metrics)
        self.assertEqual(metrics.files_modified, 2)
        self.assertGreater(metrics.overall_score, 0)

        # 8. End session
        pair_mode.end_session(session.id)
        active_session = pair_mode.get_active_session()
        self.assertIsNone(active_session)

    def test_code_review_workflow(self):
        """Test code review functionality."""
        reviewer = CodeReviewer(self.session_manager)

        # Create a test Python file with some issues
        test_file = Path(self.temp_dir) / 'test_code.py'
        test_code = """
import *

def bad_function():
    try:
        eval("print('dangerous')")
    except:
        pass
"""
        test_file.write_text(test_code)

        # Review the code
        suggestions = reviewer.review_code(str(test_file), content=test_code)

        # Should find multiple issues
        self.assertGreater(len(suggestions), 0)

        # Check for specific issues
        severities = [s.severity for s in suggestions]
        self.assertIn('error', severities)  # eval is an error

        # Get unresolved suggestions
        unresolved = reviewer.get_unresolved_suggestions(str(test_file))
        self.assertEqual(len(unresolved), len(suggestions))

        # Resolve a suggestion
        if suggestions:
            reviewer.resolve_suggestion(suggestions[0].id, "fixed")
            unresolved = reviewer.get_unresolved_suggestions(str(test_file))
            self.assertEqual(len(unresolved), len(suggestions) - 1)

    def test_suggestion_system(self):
        """Test inline suggestion system."""
        suggester = SuggestionSystem(self.session_manager)

        # Test style suggestions
        test_line = "if x == True:"
        suggestions = suggester.suggest_for_line(
            '/tmp/test.py',
            10,
            test_line
        )

        # Should suggest simplification
        self.assertGreater(len(suggestions), 0)

        # Accept a suggestion
        if suggestions:
            suggester.accept_suggestion(suggestions[0].id, "Good catch!")

        # Get statistics
        stats = suggester.get_suggestion_statistics(days=1)
        self.assertGreater(stats['total_suggestions'], 0)
        self.assertGreater(stats['accepted_suggestions'], 0)

    def test_pairing_learner(self):
        """Test pairing learning system."""
        learner = PairingLearner(self.session_manager, start_background_learning=False)

        # Learn from code edits
        old_code = "x=5"
        new_code = "user_count = 5"

        learner.learn_from_code_edit(
            '/tmp/test.py',
            old_code,
            new_code
        )

        # Check learned preferences
        preferences = learner.get_style_preferences()
        self.assertIsInstance(preferences, dict)

        # Record interaction
        learner.record_interaction(
            'test-session',
            'suggestion_accepted',
            {'file': '/tmp/test.py'},
            'accepted',
            'Use snake_case',
            'positive'
        )

        # Cleanup
        learner.cleanup()

    def test_task_division_patterns(self):
        """Test different task division patterns."""
        divider = TaskDivider(self.session_manager)

        # Test refactoring task
        refactor_tasks = divider.suggest_task_division("Refactor authentication module")
        self.assertGreater(len(refactor_tasks), 0)
        self.assertTrue(any('test' in t.description.lower() for t in refactor_tasks))

        # Test bug fix task
        bug_tasks = divider.suggest_task_division("Fix login bug")
        self.assertGreater(len(bug_tasks), 0)
        self.assertTrue(any('reproduce' in t.description.lower() for t in bug_tasks))

        # Test feature task
        feature_tasks = divider.suggest_task_division("Implement payment feature")
        self.assertGreater(len(feature_tasks), 0)
        self.assertTrue(any('design' in t.description.lower() for t in feature_tasks))

    def test_role_switching(self):
        """Test role switching functionality."""
        pair_mode = PairProgrammingMode(self.session_manager)

        # Start session
        session = pair_mode.start_session(
            "Test task",
            PairStyle.PING_PONG,
            PairRole.DRIVER
        )

        initial_isaac_role = session.current_role
        initial_human_role = session.human_role

        # Switch roles
        new_isaac_role, new_human_role = pair_mode.switch_roles()

        # Roles should be swapped
        self.assertNotEqual(new_isaac_role, initial_isaac_role)
        self.assertNotEqual(new_human_role, initial_human_role)

        # Clean up
        pair_mode.end_session(session.id)

    def test_metrics_calculation(self):
        """Test metrics calculation."""
        metrics_tracker = PairMetrics(self.session_manager)

        # Record various events
        session_id = 'test-metrics-session'
        metrics_tracker.record_event(session_id, 'task_completed', {})
        metrics_tracker.record_event(session_id, 'task_completed', {})
        metrics_tracker.record_event(session_id, 'suggestion_made', {})
        metrics_tracker.record_event(session_id, 'suggestion_accepted', {})
        metrics_tracker.record_event(session_id, 'code_review', {})
        metrics_tracker.record_event(session_id, 'role_switch', {})

        # Calculate metrics
        session_data = {
            'start_time': time.time() - 3600,  # 1 hour ago
            'end_time': time.time(),
            'files_touched': ['file1.py', 'file2.py', 'file3.py'],
            'tasks_total': 3
        }

        metrics = metrics_tracker.calculate_session_metrics(session_id, session_data)

        # Verify metrics
        self.assertEqual(metrics.tasks_completed, 2)
        self.assertEqual(metrics.files_modified, 3)
        self.assertEqual(metrics.suggestions_made, 1)
        self.assertEqual(metrics.suggestions_accepted, 1)
        self.assertGreater(metrics.productivity_score, 0)
        self.assertGreater(metrics.overall_score, 0)

    def test_pair_command_execution(self):
        """Test pair command execution."""
        command = PairCommand(self.session_manager)

        # Test status with no active session
        result = command.execute([])
        self.assertTrue(result['success'])
        self.assertIn('No active', result['output'])

        # Start a session
        result = command.execute(['start', 'Test task'])
        self.assertTrue(result['success'])
        self.assertIn('Session Started', result['output'])

        # Check status
        result = command.execute([])
        self.assertTrue(result['success'])
        self.assertIn('Active Session', result['output'])

        # End session
        result = command.execute(['end'])
        self.assertTrue(result['success'])
        self.assertIn('Session Ended', result['output'])

        # Cleanup
        command.cleanup()

    def test_session_history(self):
        """Test session history tracking."""
        pair_mode = PairProgrammingMode(self.session_manager)

        # Create multiple sessions
        for i in range(3):
            session = pair_mode.start_session(f"Task {i}", PairStyle.DRIVER_NAVIGATOR, PairRole.NAVIGATOR)
            time.sleep(0.1)
            pair_mode.end_session(session.id)

        # Get history
        history = pair_mode.get_session_history(limit=5)

        self.assertGreaterEqual(len(history), 3)
        # History should be in reverse chronological order
        for i in range(len(history) - 1):
            self.assertGreaterEqual(history[i].start_time, history[i + 1].start_time)

    def test_aggregate_metrics(self):
        """Test aggregate metrics calculation."""
        metrics_tracker = PairMetrics(self.session_manager)

        # Create multiple sessions with metrics
        for i in range(3):
            session_id = f'test-session-{i}'
            metrics_tracker.record_event(session_id, 'task_completed', {})
            metrics_tracker.record_event(session_id, 'suggestion_made', {})

            session_data = {
                'start_time': time.time() - 1800,
                'end_time': time.time(),
                'files_touched': [f'file{i}.py'],
                'tasks_total': 2
            }
            metrics_tracker.calculate_session_metrics(session_id, session_data)

        # Get aggregate metrics
        aggregate = metrics_tracker.get_aggregate_metrics(days=1)

        self.assertGreaterEqual(aggregate['total_sessions'], 3)
        self.assertIn('average_scores', aggregate)
        self.assertIn('totals', aggregate)


def run_tests():
    """Run all integration tests."""
    unittest.main(argv=[''], verbosity=2, exit=False)


if __name__ == '__main__':
    run_tests()
