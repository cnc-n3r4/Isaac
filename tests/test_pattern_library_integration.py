"""
Test Pattern Library Integration - Phase 3.4 Complete
Test all pattern library components working together
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

# Import pattern library components
from isaac.patterns.pattern_learner import PatternLearner, CodePattern
from isaac.patterns.pattern_applier import PatternApplier
from isaac.patterns.team_sharing import TeamPatternManager
from isaac.patterns.pattern_evolution import PatternEvolutionEngine, PatternUsage
from isaac.patterns.enhanced_anti_patterns import EnhancedAntiPatternDetector
from isaac.patterns.pattern_documentation import PatternDocumentationGenerator


class TestPatternLibraryIntegration:
    """Test the complete pattern library system."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            # Create test Python files
            test_files = {
                'simple_function.py': '''
def calculate_total(items):
    """Calculate total of numeric items."""
    total = 0
    for item in items:
        if isinstance(item, (int, float)):
            total += item
    return total

def process_data(data):
    """Process data with proper error handling."""
    try:
        result = calculate_total(data['values'])
        return {'success': True, 'result': result}
    except (KeyError, TypeError, ValueError) as exc:
        return {'success': False, 'error': str(exc)}
''',
                'class_example.py': '''
class DataProcessor:
    """A class for processing data."""

    def __init__(self, config=None):
        self.config = config or {}
        self.processed_count = 0

    def process(self, data):
        """Process input data."""
        if not isinstance(data, dict):
            raise ValueError("Data must be a dictionary")

        self.processed_count += 1
        return {
            'processed': True,
            'count': self.processed_count,
            'data': data
        }

    def get_stats(self):
        """Get processing statistics."""
        return {
            'total_processed': self.processed_count,
            'config': self.config
        }
''',
                'problematic_code.py': '''
def bad_function(a, b, c, d, e, f, g, h, i, j):  # Too many parameters
    # No docstring
    # Very long function with complex logic
    result = 0
    if a > 0:
        if b > 0:
            if c > 0:
                for x in range(100):  # Nested loops
                    if x % 2 == 0:
                        result += x
                    else:
                        result -= x
                if d > 0:
                    result *= 2
                elif e > 0:
                    result /= 2
                else:
                    result = 0
            else:
                result = -1
        else:
            result = -2
    else:
        result = -3

    # More complex logic
    for y in range(10):
        if f and g:
            result += y
        elif h or i:
            result -= y
        else:
            result *= y

    return result

class GodClass:  # Too many responsibilities
    def __init__(self):
        self.data = []
        self.config = {}
        self.cache = {}

    def load_data(self, source):
        # Loading logic
        pass

    def process_data(self):
        # Processing logic
        pass

    def save_data(self, destination):
        # Saving logic
        pass

    def validate_data(self):
        # Validation logic
        pass

    def generate_report(self):
        # Report generation
        pass

    def send_notification(self):
        # Notification logic
        pass

    def handle_error(self):
        # Error handling
        pass

    def cleanup(self):
        # Cleanup logic
        pass
'''
            }

            for filename, content in test_files.items():
                (workspace / filename).write_text(content)

            yield workspace

    def test_pattern_learning_and_application(self, temp_workspace):
        """Test pattern learning and application working together."""
        # Initialize components
        learner = PatternLearner()
        applier = PatternApplier(learner)

        # Learn patterns from test files
        patterns_learned = 0
        for file_path in temp_workspace.glob('*.py'):
            if file_path.name == 'problematic_code.py':
                continue  # Skip problematic code for learning

            result = learner.analyze_file(str(file_path))
            patterns_learned += len(result.patterns_found)

        assert patterns_learned > 0, "Should learn some patterns"

        # Test pattern application
        target_file = temp_workspace / 'simple_function.py'
        suggestions = applier.analyze_and_suggest(str(target_file))

        assert isinstance(suggestions, list), "Should return suggestions list"

    def test_anti_pattern_detection(self, temp_workspace):
        """Test enhanced anti-pattern detection."""
        detector = EnhancedAntiPatternDetector()

        # Test on problematic code
        problematic_file = temp_workspace / 'problematic_code.py'
        report = detector.analyze_file(str(problematic_file))

        assert report.anti_patterns, "Should detect anti-patterns in problematic code"
        assert report.quality_score < 100, "Quality score should be reduced"

        # Check for specific anti-patterns
        rule_ids = [ap.rule_id for ap in report.anti_patterns]
        assert 'too_many_parameters' in rule_ids, "Should detect too many parameters"
        assert 'missing_docstring' in rule_ids, "Should detect missing docstrings"

    def test_pattern_evolution(self, temp_workspace):
        """Test pattern evolution system."""
        evolution_engine = PatternEvolutionEngine()

        # Record some usage
        import uuid
        pattern_id = f'test_pattern_{uuid.uuid4().hex[:8]}'
        usage = PatternUsage(
            pattern_id=pattern_id,
            success=True,
            confidence_score=0.8,
            execution_time=0.5
        )
        evolution_engine.record_pattern_usage(usage)

        # Get metrics
        metrics = evolution_engine.get_pattern_metrics(pattern_id)
        assert metrics is not None, "Should have metrics for used pattern"
        assert metrics.total_uses == 1, "Should record usage"
        assert metrics.success_rate == 1.0, "Should have perfect success rate"

        # Test evolution suggestions
        suggestions = evolution_engine.suggest_pattern_improvements('test_pattern_1')
        assert isinstance(suggestions, list), "Should return suggestions list"

    def test_team_pattern_sharing(self, temp_workspace):
        """Test team pattern sharing functionality."""
        manager = TeamPatternManager({'user_id': 'test_user'})

        # Create a repository
        repo_id = manager.create_repository(
            name='Test Patterns',
            description='Test pattern repository'
        )
        assert repo_id, "Should create repository"

        # Add a pattern
        pattern_data = {
            'id': 'test_pattern',
            'name': 'Test Function Pattern',
            'description': 'A test pattern',
            'category': 'function',
            'language': 'python',
            'template': 'def {name}({args}):\n    {body}',
            'variables': {'name': 'function_name', 'args': 'parameters', 'body': 'pass'}
        }

        success = manager.add_pattern_to_repository(repo_id, pattern_data)
        assert success, "Should add pattern to repository"

        # Get patterns
        patterns = manager.get_repository_patterns(repo_id)
        assert len(patterns) == 1, "Should retrieve pattern"
        assert patterns[0]['name'] == 'Test Function Pattern', "Should have correct pattern"

    def test_pattern_documentation(self, temp_workspace):
        """Test pattern documentation generation."""
        generator = PatternDocumentationGenerator()

        # Create documentation for a pattern
        pattern_data = {
            'id': 'test_doc_pattern',
            'name': 'Test Pattern',
            'description': 'A pattern for testing documentation',
            'category': 'function',
            'language': 'python',
            'examples': ['def example():\n    return "test"'],
            'tags': ['test', 'documentation']
        }

        usage_stats = {
            'total_uses': 10,
            'success_rate': 0.9,
            'average_rating': 4.5
        }

        documentation = generator.generate_documentation(pattern_data, usage_stats)
        assert documentation.title == 'Test Pattern', "Should create documentation"
        assert documentation.usage_count == 10, "Should include usage stats"

        # Generate markdown
        markdown_content = generator.generate_markdown('test_doc_pattern')
        assert '# Test Pattern' in markdown_content, "Should generate markdown"
        assert '**Total Usage:** 10 times' in markdown_content, "Should include statistics"

    def test_complete_pattern_workflow(self, temp_workspace):
        """Test complete pattern learning to application workflow."""
        # Setup all components
        learner = PatternLearner()
        applier = PatternApplier(learner)
        detector = EnhancedAntiPatternDetector()
        evolution = PatternEvolutionEngine()
        docs = PatternDocumentationGenerator()

        # Step 1: Learn patterns from good code
        good_file = temp_workspace / 'simple_function.py'
        learn_result = learner.analyze_file(str(good_file))

        assert learn_result.overall_score >= 50, "Good code should have decent score"

        # Step 2: Detect anti-patterns in problematic code
        bad_file = temp_workspace / 'problematic_code.py'
        anti_pattern_report = detector.analyze_file(str(bad_file))

        assert len(anti_pattern_report.anti_patterns) > 0, "Should detect issues"
        assert anti_pattern_report.quality_score < 60, "Bad code should have low score"

        # Step 3: Generate suggestions for improvement
        suggestions = applier.analyze_and_suggest(str(bad_file))
        assert isinstance(suggestions, list), "Should provide suggestions"

        # Step 4: Document a learned pattern
        if learn_result.patterns_found:
            pattern_data = asdict(learn_result.patterns_found[0])
            documentation = docs.generate_documentation(pattern_data)
            assert documentation.pattern_id, "Should create documentation"

        # Step 5: Test evolution with usage data
        if learn_result.patterns_found:
            pattern = learn_result.patterns_found[0]
            usage = PatternUsage(
                pattern_id=pattern.id,
                success=True,
                confidence_score=0.85,
                execution_time=0.3
            )
            evolution.record_pattern_usage(usage)

            metrics = evolution.get_pattern_metrics(pattern.id)
            assert metrics.total_uses == 1, "Should track usage"

    def test_pattern_quality_assessment(self, temp_workspace):
        """Test pattern quality assessment across files."""
        detector = EnhancedAntiPatternDetector()

        # Analyze all files
        results = {}
        for file_path in temp_workspace.glob('*.py'):
            report = detector.analyze_file(str(file_path))
            results[file_path.name] = {
                'quality_score': report.quality_score,
                'issues_count': len(report.anti_patterns),
                'auto_fixable': report.auto_fixable_count
            }

        # Verify problematic code has lower quality
        assert results['problematic_code.py']['quality_score'] < results['simple_function.py']['quality_score']
        assert results['problematic_code.py']['issues_count'] > results['simple_function.py']['issues_count']

    def test_pattern_search_and_filtering(self, temp_workspace):
        """Test pattern search and filtering capabilities."""
        manager = TeamPatternManager({'user_id': 'test_user'})

        # Create multiple repositories and patterns
        repo1_id = manager.create_repository('Function Patterns', tags=['functions'])
        repo2_id = manager.create_repository('Class Patterns', tags=['classes'])

        # Add patterns
        patterns_data = [
            {
                'id': 'func_pattern_1',
                'name': 'Simple Function',
                'category': 'function',
                'language': 'python'
            },
            {
                'id': 'func_pattern_2',
                'name': 'Complex Function',
                'category': 'function',
                'language': 'python'
            },
            {
                'id': 'class_pattern_1',
                'name': 'Data Class',
                'category': 'class',
                'language': 'python'
            }
        ]

        for pattern in patterns_data:
            if 'func' in pattern['id']:
                manager.add_pattern_to_repository(repo1_id, pattern)
            else:
                manager.add_pattern_to_repository(repo2_id, pattern)

        # Test searching
        func_repos = manager.search_repositories(tags=['functions'])
        assert len(func_repos) == 1, "Should find function repository"

        class_repos = manager.search_repositories(tags=['classes'])
        assert len(class_repos) == 1, "Should find class repository"

        # Test pattern retrieval with filtering
        func_patterns = manager.get_repository_patterns(repo1_id, category='function')
        assert len(func_patterns) == 2, "Should find 2 function patterns"

        class_patterns = manager.get_repository_patterns(repo2_id, category='class')
        assert len(class_patterns) == 1, "Should find 1 class pattern"

    def test_pattern_evolution_over_time(self, temp_workspace):
        """Test pattern evolution with multiple usage records."""
        # Use temp directory for evolution data
        config = {'data_dir': str(temp_workspace / 'evolution_data')}
        evolution = PatternEvolutionEngine(config)

        pattern_id = 'evolving_pattern'

        # Record multiple usages with varying success
        usages = [
            PatternUsage(pattern_id, success=True, confidence_score=0.7, execution_time=0.5),
            PatternUsage(pattern_id, success=True, confidence_score=0.8, execution_time=0.4),
            PatternUsage(pattern_id, success=False, confidence_score=0.6, execution_time=1.0),
            PatternUsage(pattern_id, success=True, confidence_score=0.9, execution_time=0.3),
            PatternUsage(pattern_id, success=True, confidence_score=0.85, execution_time=0.35)
        ]

        for usage in usages:
            evolution.record_pattern_usage(usage)

        # Check metrics
        metrics = evolution.get_pattern_metrics(pattern_id)
        assert metrics.total_uses == 5, "Should record all usages"
        assert metrics.successful_uses == 4, "Should have 4 successful uses"
        assert abs(metrics.success_rate - 0.8) < 0.01, "Should calculate correct success rate"

        # Check evolution suggestions
        suggestions = evolution.suggest_pattern_improvements(pattern_id)
        assert isinstance(suggestions, list), "Should provide suggestions"

        # Test performance trend
        trend = evolution.get_pattern_performance_trend(pattern_id)
        assert len(trend) > 0, "Should have performance trend data"

    def test_documentation_export(self, temp_workspace):
        """Test documentation export functionality."""
        generator = PatternDocumentationGenerator()

        # Create some documentation
        pattern_data = {
            'id': 'export_test_pattern',
            'name': 'Export Test Pattern',
            'description': 'Pattern for testing export functionality',
            'category': 'function',
            'language': 'python'
        }

        generator.generate_documentation(pattern_data)

        # Export to temporary directory
        with tempfile.TemporaryDirectory() as export_dir:
            exported_count = generator.export_documentation(export_dir, format='markdown')

            assert exported_count > 0, "Should export some files"

            # Check if files were created
            export_path = Path(export_dir)
            md_files = list(export_path.glob('*.md'))
            assert len(md_files) > 0, "Should create markdown files"

            # Check index file
            index_file = export_path / 'index.md'
            assert index_file.exists(), "Should create index file"

            index_content = index_file.read_text()
            assert 'Export Test Pattern' in index_content, "Should include pattern in index"

    def test_integration_with_file_operations(self, temp_workspace):
        """Test integration with file operations and suggestions."""
        learner = PatternLearner()
        applier = PatternApplier(learner)

        # Test suggestions on different file types
        for file_path in temp_workspace.glob('*.py'):
            suggestions = applier.analyze_and_suggest(str(file_path))

            # Each file should get some analysis
            assert isinstance(suggestions, list), f"Should analyze {file_path.name}"

            # Check suggestion structure
            if suggestions:
                suggestion = suggestions[0]
                assert hasattr(suggestion, 'pattern'), "Should have pattern"
                assert hasattr(suggestion, 'confidence'), "Should have confidence"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])