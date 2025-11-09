"""
Code Quality Tracker

Tracks code improvements, patterns, anti-patterns, and quality metrics.
"""

import json
import os
import ast
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from isaac.analytics.database import AnalyticsDatabase


@dataclass
class CodeQualitySnapshot:
    """A snapshot of code quality metrics"""
    timestamp: str
    files_analyzed: int
    patterns_detected: int
    anti_patterns_detected: int
    quality_score: float
    complexity_score: float
    maintainability_score: float


class CodeQualityTracker:
    """Tracks code quality metrics and improvements"""

    def __init__(self, db: Optional[AnalyticsDatabase] = None):
        """Initialize code quality tracker"""
        self.db = db or AnalyticsDatabase()
        self.session_id = datetime.now().isoformat()

        # Metrics
        self.files_analyzed = 0
        self.patterns_detected = 0
        self.anti_patterns_detected = 0

    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """Analyze a file for code quality metrics"""
        if not os.path.exists(file_path):
            return {'error': 'File not found'}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Python file analysis
            if file_path.endswith('.py'):
                return self._analyze_python_file(file_path, content)
            else:
                return self._analyze_generic_file(file_path, content)

        except Exception as e:
            return {'error': str(e)}

    def _analyze_python_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze Python file for quality metrics"""
        try:
            tree = ast.parse(content)
            self.files_analyzed += 1

            # Count various elements
            classes = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
            functions = sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
            lines = len(content.splitlines())
            docstrings = self._count_docstrings(tree)

            # Calculate complexity
            complexity = self._calculate_complexity(tree)

            # Calculate maintainability
            maintainability = self._calculate_maintainability(
                lines, functions, classes, docstrings
            )

            # Calculate overall quality score
            quality_score = self._calculate_quality_score(
                complexity, maintainability, docstrings, functions
            )

            # Record metrics
            self.db.record_code_quality_metric(
                metric_type='quality_score',
                metric_name='overall_quality',
                metric_value=quality_score,
                file_path=file_path,
                session_id=self.session_id,
                metadata=json.dumps({
                    'lines': lines,
                    'functions': functions,
                    'classes': classes,
                    'docstrings': docstrings,
                    'complexity': complexity,
                    'maintainability': maintainability
                })
            )

            return {
                'file_path': file_path,
                'lines': lines,
                'functions': functions,
                'classes': classes,
                'docstrings': docstrings,
                'complexity_score': complexity,
                'maintainability_score': maintainability,
                'quality_score': quality_score
            }

        except SyntaxError as e:
            return {
                'file_path': file_path,
                'error': f'Syntax error: {str(e)}',
                'quality_score': 0
            }

    def _analyze_generic_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Analyze generic file for basic metrics"""
        lines = len(content.splitlines())
        non_empty_lines = len([l for l in content.splitlines() if l.strip()])

        # Simple quality score based on structure
        quality_score = min(100, (non_empty_lines / max(1, lines)) * 100)

        self.db.record_code_quality_metric(
            metric_type='quality_score',
            metric_name='overall_quality',
            metric_value=quality_score,
            file_path=file_path,
            session_id=self.session_id,
            metadata=json.dumps({
                'lines': lines,
                'non_empty_lines': non_empty_lines
            })
        )

        return {
            'file_path': file_path,
            'lines': lines,
            'non_empty_lines': non_empty_lines,
            'quality_score': quality_score
        }

    def _count_docstrings(self, tree: ast.AST) -> int:
        """Count docstrings in AST"""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                docstring = ast.get_docstring(node)
                if docstring:
                    count += 1
        return count

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity score (0-100, lower is better)"""
        complexity = 0

        for node in ast.walk(tree):
            # Count decision points
            if isinstance(node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(node, ast.ExceptHandler):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1

        # Normalize to 0-100 scale (inverse, so lower complexity = higher score)
        # Assume 0 complexity = 100, 50+ complexity = 0
        normalized = max(0, 100 - (complexity * 2))
        return normalized

    def _calculate_maintainability(
        self,
        lines: int,
        functions: int,
        classes: int,
        docstrings: int
    ) -> float:
        """Calculate maintainability score (0-100)"""
        # Factors
        avg_function_length = lines / max(1, functions) if functions > 0 else lines
        documentation_ratio = docstrings / max(1, functions + classes)

        # Score components
        size_score = max(0, 100 - avg_function_length)  # Prefer smaller functions
        doc_score = min(100, documentation_ratio * 100)  # Prefer good documentation

        # Weighted average
        maintainability = (size_score * 0.6 + doc_score * 0.4)
        return min(100, max(0, maintainability))

    def _calculate_quality_score(
        self,
        complexity: float,
        maintainability: float,
        docstrings: int,
        functions: int
    ) -> float:
        """Calculate overall quality score (0-100)"""
        # Weighted combination
        quality = (
            complexity * 0.3 +
            maintainability * 0.4 +
            min(100, (docstrings / max(1, functions)) * 100) * 0.3
        )
        return min(100, max(0, quality))

    def record_pattern_detection(
        self,
        pattern_name: str,
        file_path: str,
        confidence: float
    ):
        """Record detected code pattern"""
        self.patterns_detected += 1

        self.db.record_code_quality_metric(
            metric_type='pattern_detection',
            metric_name=pattern_name,
            metric_value=confidence,
            file_path=file_path,
            session_id=self.session_id
        )

    def record_anti_pattern_detection(
        self,
        anti_pattern_name: str,
        file_path: str,
        severity: float
    ):
        """Record detected anti-pattern"""
        self.anti_patterns_detected += 1

        self.db.record_code_quality_metric(
            metric_type='anti_pattern_detection',
            metric_name=anti_pattern_name,
            metric_value=severity,
            file_path=file_path,
            session_id=self.session_id
        )

    def record_code_improvement(
        self,
        improvement_type: str,
        file_path: str,
        before_score: float,
        after_score: float
    ):
        """Record code improvement"""
        improvement = after_score - before_score

        self.db.record_code_quality_metric(
            metric_type='improvement',
            metric_name=improvement_type,
            metric_value=improvement,
            file_path=file_path,
            before_value=before_score,
            after_value=after_score,
            session_id=self.session_id
        )

    def get_current_snapshot(self) -> CodeQualitySnapshot:
        """Get current code quality snapshot"""
        # Calculate average scores from recent analysis
        recent_metrics = self.db.query_metrics(
            'code_quality_metrics',
            start_date=(datetime.now() - timedelta(hours=1)).isoformat(),
            filters={'session_id': self.session_id}
        )

        quality_scores = [
            m['metric_value'] for m in recent_metrics
            if m['metric_type'] == 'quality_score'
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 50.0

        return CodeQualitySnapshot(
            timestamp=datetime.now().isoformat(),
            files_analyzed=self.files_analyzed,
            patterns_detected=self.patterns_detected,
            anti_patterns_detected=self.anti_patterns_detected,
            quality_score=avg_quality,
            complexity_score=70.0,  # Placeholder
            maintainability_score=70.0  # Placeholder
        )

    def get_quality_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate code quality report"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()

        # Get metrics from database
        metrics = self.db.query_metrics(
            'code_quality_metrics',
            start_date=start_date,
            end_date=end_date
        )

        # Aggregate by file
        files_analyzed = {}
        for metric in metrics:
            file_path = metric.get('file_path', 'unknown')
            if file_path not in files_analyzed:
                files_analyzed[file_path] = {
                    'quality_scores': [],
                    'patterns': 0,
                    'anti_patterns': 0,
                    'improvements': []
                }

            if metric['metric_type'] == 'quality_score':
                files_analyzed[file_path]['quality_scores'].append(metric['metric_value'])
            elif metric['metric_type'] == 'pattern_detection':
                files_analyzed[file_path]['patterns'] += 1
            elif metric['metric_type'] == 'anti_pattern_detection':
                files_analyzed[file_path]['anti_patterns'] += 1
            elif metric['metric_type'] == 'improvement':
                files_analyzed[file_path]['improvements'].append(metric['metric_value'])

        # Calculate averages
        total_quality = []
        total_patterns = 0
        total_anti_patterns = 0
        total_improvement = 0

        for file_data in files_analyzed.values():
            if file_data['quality_scores']:
                total_quality.extend(file_data['quality_scores'])
            total_patterns += file_data['patterns']
            total_anti_patterns += file_data['anti_patterns']
            if file_data['improvements']:
                total_improvement += sum(file_data['improvements'])

        avg_quality = sum(total_quality) / len(total_quality) if total_quality else 50.0

        return {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'summary': {
                'files_analyzed': len(files_analyzed),
                'average_quality_score': avg_quality,
                'total_patterns_detected': total_patterns,
                'total_anti_patterns_detected': total_anti_patterns,
                'total_improvement': total_improvement,
                'quality_trend': 'improving' if total_improvement > 0 else 'stable'
            },
            'current_session': asdict(self.get_current_snapshot()),
            'files': files_analyzed,
            'insights': self._generate_quality_insights(
                avg_quality, total_patterns, total_anti_patterns, total_improvement
            )
        }

    def _generate_quality_insights(
        self,
        avg_quality: float,
        patterns: int,
        anti_patterns: int,
        improvement: float
    ) -> List[str]:
        """Generate insights from code quality data"""
        insights = []

        if avg_quality >= 80:
            insights.append("✨ Excellent code quality! Keep up the good work")
        elif avg_quality >= 60:
            insights.append("👍 Good code quality with room for improvement")
        else:
            insights.append("⚠️  Code quality needs attention - consider refactoring")

        if patterns > 10:
            insights.append(f"📐 {patterns} good patterns detected - following best practices")

        if anti_patterns > 5:
            insights.append(f"🚨 {anti_patterns} anti-patterns found - review and refactor")

        if improvement > 10:
            insights.append(f"📈 Code quality improved by {improvement:.1f} points")

        return insights

    def get_quality_trend(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get quality trend over time"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        metrics = self.db.query_metrics(
            'code_quality_metrics',
            start_date=start_date
        )

        # Group by day
        daily_metrics = {}
        for metric in metrics:
            date = metric['timestamp'][:10]
            if date not in daily_metrics:
                daily_metrics[date] = {
                    'quality_scores': [],
                    'patterns': 0,
                    'anti_patterns': 0
                }

            if metric['metric_type'] == 'quality_score':
                daily_metrics[date]['quality_scores'].append(metric['metric_value'])
            elif metric['metric_type'] == 'pattern_detection':
                daily_metrics[date]['patterns'] += 1
            elif metric['metric_type'] == 'anti_pattern_detection':
                daily_metrics[date]['anti_patterns'] += 1

        # Convert to list
        trend = []
        for date, data in sorted(daily_metrics.items()):
            avg_quality = (
                sum(data['quality_scores']) / len(data['quality_scores'])
                if data['quality_scores'] else 50.0
            )
            trend.append({
                'date': date,
                'average_quality': avg_quality,
                'patterns': data['patterns'],
                'anti_patterns': data['anti_patterns']
            })

        return trend
