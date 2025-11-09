"""
Root Cause Analysis - Find deep issues beyond surface symptoms
Isaac's advanced debugging system for thorough problem diagnosis
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class AnalysisDepth(Enum):
    """Depth levels for root cause analysis."""
    SURFACE = "surface"      # Just the obvious error
    INTERMEDIATE = "intermediate"  # Related components
    DEEP = "deep"           # System-wide analysis
    COMPREHENSIVE = "comprehensive"  # Full system investigation


@dataclass
class CausalLink:
    """Represents a causal relationship between events or conditions."""
    cause: str
    effect: str
    confidence: float  # 0-1
    evidence: List[str]
    relationship_type: str  # 'direct', 'contributing', 'root', 'symptom'


@dataclass
class RootCauseHypothesis:
    """A hypothesis about the root cause of an issue."""
    hypothesis_id: str
    description: str
    confidence: float
    supporting_evidence: List[str]
    contradicting_evidence: List[str]
    causal_chain: List[CausalLink]
    recommended_tests: List[str]
    estimated_fix_complexity: str  # 'simple', 'moderate', 'complex', 'major'


@dataclass
class RootCauseAnalysis:
    """Complete root cause analysis result."""
    analysis_id: str
    timestamp: float
    original_error: str
    analysis_depth: AnalysisDepth
    primary_root_cause: str
    confidence: float
    hypotheses: List[RootCauseHypothesis]
    causal_graph: List[CausalLink]
    systemic_issues: List[str]
    preventive_measures: List[str]
    analysis_duration: float


class RootCauseAnalyzer:
    """Performs deep root cause analysis beyond surface-level symptoms."""

    def __init__(self):
        """Initialize the root cause analyzer."""
        self.analysis_history: Dict[str, RootCauseAnalysis] = {}
        self.causal_patterns = self._load_causal_patterns()
        self.max_analysis_time = 60  # seconds for comprehensive analysis

    def _load_causal_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load known causal patterns and relationships."""
        return {
            'memory_issues': {
                'symptoms': ['Out of memory', 'Cannot allocate memory', 'Memory allocation failed'],
                'possible_causes': [
                    'memory_leak', 'insufficient_ram', 'large_dataset', 'memory_fragmentation',
                    'garbage_collection_issues', 'memory_limits'
                ],
                'causal_links': [
                    {'cause': 'memory_leak', 'effect': 'out_of_memory', 'type': 'direct'},
                    {'cause': 'large_dataset', 'effect': 'memory_pressure', 'type': 'contributing'},
                    {'cause': 'memory_pressure', 'effect': 'out_of_memory', 'type': 'direct'}
                ]
            },
            'permission_issues': {
                'symptoms': ['Permission denied', 'Access is denied', 'Operation not permitted'],
                'possible_causes': [
                    'incorrect_permissions', 'wrong_user', 'selinux_policy', 'file_ownership',
                    'executable_permissions', 'directory_traversal'
                ],
                'causal_links': [
                    {'cause': 'incorrect_permissions', 'effect': 'permission_denied', 'type': 'direct'},
                    {'cause': 'selinux_policy', 'effect': 'permission_denied', 'type': 'contributing'}
                ]
            },
            'network_issues': {
                'symptoms': ['Connection refused', 'Connection timed out', 'Network unreachable'],
                'possible_causes': [
                    'service_down', 'firewall_block', 'dns_failure', 'routing_issue',
                    'port_closed', 'network_interface_down'
                ],
                'causal_links': [
                    {'cause': 'service_down', 'effect': 'connection_refused', 'type': 'direct'},
                    {'cause': 'firewall_block', 'effect': 'connection_refused', 'type': 'direct'},
                    {'cause': 'dns_failure', 'effect': 'connection_refused', 'type': 'contributing'}
                ]
            },
            'disk_issues': {
                'symptoms': ['No space left on device', 'Disk full', 'Write failed'],
                'possible_causes': [
                    'disk_full', 'quota_exceeded', 'filesystem_corruption', 'disk_failure',
                    'inode_exhaustion', 'permission_issue'
                ],
                'causal_links': [
                    {'cause': 'disk_full', 'effect': 'no_space_left', 'type': 'direct'},
                    {'cause': 'quota_exceeded', 'effect': 'no_space_left', 'type': 'direct'}
                ]
            },
            'performance_issues': {
                'symptoms': ['Slow response', 'Timeout', 'High CPU usage', 'High memory usage'],
                'possible_causes': [
                    'cpu_bound', 'memory_bound', 'io_bound', 'network_latency', 'lock_contention',
                    'inefficient_algorithm', 'resource_starvation'
                ],
                'causal_links': [
                    {'cause': 'cpu_bound', 'effect': 'slow_response', 'type': 'direct'},
                    {'cause': 'io_bound', 'effect': 'slow_response', 'type': 'direct'},
                    {'cause': 'lock_contention', 'effect': 'slow_response', 'type': 'contributing'}
                ]
            }
        }

    def analyze_root_cause(self, error_message: str, diagnostic_data: Dict[str, Any],
                          analysis_depth: AnalysisDepth = AnalysisDepth.INTERMEDIATE) -> RootCauseAnalysis:
        """Perform comprehensive root cause analysis.

        Args:
            error_message: The original error message
            diagnostic_data: Diagnostic information from auto-investigator
            analysis_depth: How deep to analyze

        Returns:
            Complete root cause analysis
        """
        analysis_id = f"rca_{int(time.time())}_{hash(error_message) % 10000}"
        start_time = time.time()

        # Generate hypotheses
        hypotheses = self._generate_hypotheses(error_message, diagnostic_data)

        # Build causal graph
        causal_graph = self._build_causal_graph(error_message, diagnostic_data, hypotheses)

        # Determine primary root cause
        primary_root_cause, confidence = self._determine_primary_root_cause(hypotheses, causal_graph)

        # Identify systemic issues
        systemic_issues = self._identify_systemic_issues(diagnostic_data, causal_graph)

        # Generate preventive measures
        preventive_measures = self._generate_preventive_measures(primary_root_cause, systemic_issues)

        # Refine hypotheses based on depth
        if analysis_depth in [AnalysisDepth.DEEP, AnalysisDepth.COMPREHENSIVE]:
            hypotheses = self._refine_hypotheses_deep(hypotheses, diagnostic_data)

        analysis_duration = time.time() - start_time

        analysis = RootCauseAnalysis(
            analysis_id=analysis_id,
            timestamp=time.time(),
            original_error=error_message,
            analysis_depth=analysis_depth,
            primary_root_cause=primary_root_cause,
            confidence=confidence,
            hypotheses=hypotheses,
            causal_graph=causal_graph,
            systemic_issues=systemic_issues,
            preventive_measures=preventive_measures,
            analysis_duration=analysis_duration
        )

        # Store in history
        self.analysis_history[analysis_id] = analysis

        return analysis

    def _generate_hypotheses(self, error_message: str, diagnostic_data: Dict[str, Any]) -> List[RootCauseHypothesis]:
        """Generate hypotheses about possible root causes."""
        hypotheses = []

        # Match against known causal patterns
        for pattern_name, pattern_data in self.causal_patterns.items():
            if self._matches_symptoms(error_message, pattern_data['symptoms']):
                for cause in pattern_data['possible_causes']:
                    hypothesis = self._create_hypothesis_from_pattern(
                        cause, pattern_data, error_message, diagnostic_data
                    )
                    if hypothesis:
                        hypotheses.append(hypothesis)

        # Generate additional hypotheses based on diagnostic data
        hypotheses.extend(self._generate_diagnostic_hypotheses(diagnostic_data))

        # Sort by confidence
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)

        return hypotheses[:10]  # Top 10 hypotheses

    def _matches_symptoms(self, error_message: str, symptoms: List[str]) -> bool:
        """Check if error message matches any known symptoms."""
        error_lower = error_message.lower()
        return any(symptom.lower() in error_lower for symptom in symptoms)

    def _create_hypothesis_from_pattern(self, cause: str, pattern_data: Dict[str, Any],
                                       error_message: str, diagnostic_data: Dict[str, Any]) -> Optional[RootCauseHypothesis]:
        """Create a hypothesis from a causal pattern."""
        hypothesis_id = f"hyp_{cause}_{int(time.time())}"

        # Build description
        descriptions = {
            'memory_leak': "Application has a memory leak causing gradual memory exhaustion",
            'insufficient_ram': "System has insufficient RAM for the current workload",
            'large_dataset': "Processing unusually large dataset exceeding memory capacity",
            'incorrect_permissions': "File or directory permissions prevent the operation",
            'wrong_user': "Operation attempted by wrong user account",
            'service_down': "Target service is not running or accessible",
            'firewall_block': "Firewall rules blocking the network connection",
            'disk_full': "Storage device has insufficient free space",
            'cpu_bound': "CPU is fully utilized preventing timely processing",
            'io_bound': "Disk I/O operations are the performance bottleneck"
        }

        description = descriptions.get(cause, f"Root cause appears to be: {cause}")

        # Calculate confidence based on evidence
        confidence = self._calculate_hypothesis_confidence(cause, error_message, diagnostic_data)

        # Gather evidence
        supporting_evidence = self._gather_supporting_evidence(cause, diagnostic_data)
        contradicting_evidence = self._gather_contradicting_evidence(cause, diagnostic_data)

        # Build causal chain
        causal_chain = self._build_causal_chain(cause, pattern_data.get('causal_links', []))

        # Recommended tests
        recommended_tests = self._get_recommended_tests(cause)

        # Estimate fix complexity
        fix_complexity = self._estimate_fix_complexity(cause)

        if confidence > 0.1:  # Only return hypotheses with minimal confidence
            return RootCauseHypothesis(
                hypothesis_id=hypothesis_id,
                description=description,
                confidence=confidence,
                supporting_evidence=supporting_evidence,
                contradicting_evidence=contradicting_evidence,
                causal_chain=causal_chain,
                recommended_tests=recommended_tests,
                estimated_fix_complexity=fix_complexity
            )

        return None

    def _calculate_hypothesis_confidence(self, cause: str, error_message: str,
                                       diagnostic_data: Dict[str, Any]) -> float:
        """Calculate confidence score for a hypothesis."""
        confidence = 0.0

        # Direct symptom match
        if cause in ['memory_leak', 'insufficient_ram'] and 'memory' in error_message.lower():
            confidence += 0.4
        elif cause in ['disk_full', 'quota_exceeded'] and 'space' in error_message.lower():
            confidence += 0.4
        elif cause in ['incorrect_permissions', 'wrong_user'] and 'permission' in error_message.lower():
            confidence += 0.4

        # Diagnostic data support
        memory_usage = diagnostic_data.get('memory_usage', {})
        disk_usage = diagnostic_data.get('disk_usage', {})

        if cause == 'insufficient_ram' and memory_usage.get('percent', 0) > 80:
            confidence += 0.3
        elif cause == 'disk_full' and disk_usage.get('percent', 0) > 80:
            confidence += 0.3
        elif cause == 'memory_leak' and memory_usage.get('percent', 0) > 90:
            confidence += 0.2

        # Network diagnostics
        network_status = diagnostic_data.get('network_status', {})
        if cause in ['service_down', 'firewall_block'] and not network_status.get('has_internet', True):
            confidence += 0.2

        return min(confidence + 0.1, 1.0)  # Base confidence + evidence

    def _gather_supporting_evidence(self, cause: str, diagnostic_data: Dict[str, Any]) -> List[str]:
        """Gather evidence supporting a hypothesis."""
        evidence = []

        memory_usage = diagnostic_data.get('memory_usage', {})
        disk_usage = diagnostic_data.get('disk_usage', {})

        if cause == 'insufficient_ram':
            if memory_usage.get('percent', 0) > 80:
                evidence.append(f"Memory usage is {memory_usage['percent']:.1f}%")
        elif cause == 'disk_full':
            if disk_usage.get('percent', 0) > 80:
                evidence.append(f"Disk usage is {disk_usage['percent']:.1f}%")

        return evidence

    def _gather_contradicting_evidence(self, cause: str, diagnostic_data: Dict[str, Any]) -> List[str]:
        """Gather evidence contradicting a hypothesis."""
        evidence = []

        memory_usage = diagnostic_data.get('memory_usage', {})
        disk_usage = diagnostic_data.get('disk_usage', {})

        if cause == 'insufficient_ram' and memory_usage.get('percent', 0) < 50:
            evidence.append(f"Memory usage is only {memory_usage['percent']:.1f}%, suggesting sufficient RAM")
        elif cause == 'disk_full' and disk_usage.get('percent', 0) < 50:
            evidence.append(f"Disk usage is only {disk_usage['percent']:.1f}%, suggesting sufficient space")

        return evidence

    def _build_causal_chain(self, cause: str, causal_links: List[Dict[str, Any]]) -> List[CausalLink]:
        """Build a chain of causal links for a hypothesis."""
        chain = []

        for link_data in causal_links:
            if link_data.get('cause') == cause or cause in link_data.get('effect', ''):
                chain.append(CausalLink(
                    cause=link_data['cause'],
                    effect=link_data['effect'],
                    confidence=0.8,
                    evidence=[f"Causal pattern: {link_data['cause']} → {link_data['effect']}"],
                    relationship_type=link_data.get('type', 'direct')
                ))

        return chain

    def _get_recommended_tests(self, cause: str) -> List[str]:
        """Get recommended tests to validate a hypothesis."""
        tests = {
            'memory_leak': [
                "Monitor memory usage over time with 'top' or 'htop'",
                "Run application with memory profiling tools",
                "Check for infinite loops or recursive functions"
            ],
            'insufficient_ram': [
                "Check system memory with 'free' or 'vm_stat'",
                "Monitor swap usage",
                "Test with smaller dataset or reduced concurrency"
            ],
            'disk_full': [
                "Check disk usage with 'df -h'",
                "Find large files with 'find / -size +100M'",
                "Check inode usage with 'df -i'"
            ],
            'incorrect_permissions': [
                "Check file permissions with 'ls -la'",
                "Verify user ownership with 'id' and 'ls -ln'",
                "Test with elevated permissions"
            ]
        }

        return tests.get(cause, ["Further investigation needed"])

    def _estimate_fix_complexity(self, cause: str) -> str:
        """Estimate the complexity of fixing a particular cause."""
        complexities = {
            'insufficient_ram': 'moderate',  # May require hardware upgrade
            'disk_full': 'simple',          # Usually just cleanup
            'incorrect_permissions': 'simple',  # Usually chmod/chown
            'memory_leak': 'complex',       # Requires code changes
            'service_down': 'moderate',     # May require service restart/config
            'firewall_block': 'moderate',   # Firewall rule changes
            'cpu_bound': 'complex',         # Algorithm or architecture changes
            'io_bound': 'moderate'          # May require hardware or optimization
        }

        return complexities.get(cause, 'moderate')

    def _generate_diagnostic_hypotheses(self, diagnostic_data: Dict[str, Any]) -> List[RootCauseHypothesis]:
        """Generate hypotheses based on diagnostic data patterns."""
        hypotheses = []

        # Check for resource exhaustion
        memory_percent = diagnostic_data.get('memory_usage', {}).get('percent', 0)
        disk_percent = diagnostic_data.get('disk_usage', {}).get('percent', 0)

        if memory_percent > 95:
            hypotheses.append(RootCauseHypothesis(
                hypothesis_id=f"diag_memory_critical_{int(time.time())}",
                description="System is critically low on memory, causing allocation failures",
                confidence=0.9,
                supporting_evidence=[f"Memory usage: {memory_percent:.1f}%"],
                contradicting_evidence=[],
                causal_chain=[],
                recommended_tests=["Check running processes with high memory usage"],
                estimated_fix_complexity="moderate"
            ))

        if disk_percent > 95:
            hypotheses.append(RootCauseHypothesis(
                hypothesis_id=f"diag_disk_critical_{int(time.time())}",
                description="Disk is critically full, preventing file operations",
                confidence=0.9,
                supporting_evidence=[f"Disk usage: {disk_percent:.1f}%"],
                contradicting_evidence=[],
                causal_chain=[],
                recommended_tests=["Identify large files and cleanup space"],
                estimated_fix_complexity="simple"
            ))

        return hypotheses

    def _build_causal_graph(self, error_message: str, diagnostic_data: Dict[str, Any],
                           hypotheses: List[RootCauseHypothesis]) -> List[CausalLink]:
        """Build a comprehensive causal graph from all hypotheses."""
        graph = []

        # Add links from hypotheses
        for hypothesis in hypotheses:
            graph.extend(hypothesis.causal_chain)

        # Add systemic links
        memory_percent = diagnostic_data.get('memory_usage', {}).get('percent', 0)
        if memory_percent > 80:
            graph.append(CausalLink(
                cause="high_memory_usage",
                effect="application_failures",
                confidence=0.7,
                evidence=[f"Memory usage: {memory_percent:.1f}%"],
                relationship_type="contributing"
            ))

        return graph

    def _determine_primary_root_cause(self, hypotheses: List[RootCauseHypothesis],
                                    causal_graph: List[CausalLink]) -> Tuple[str, float]:
        """Determine the most likely primary root cause."""
        if not hypotheses:
            return "Unknown - insufficient data for analysis", 0.0

        # Find hypothesis with highest confidence
        best_hypothesis = max(hypotheses, key=lambda h: h.confidence)

        # Look for root cause in causal chain
        for link in best_hypothesis.causal_chain:
            if link.relationship_type == 'root':
                return link.cause, best_hypothesis.confidence

        # Fallback to hypothesis description
        return best_hypothesis.description, best_hypothesis.confidence

    def _identify_systemic_issues(self, diagnostic_data: Dict[str, Any],
                                causal_graph: List[CausalLink]) -> List[str]:
        """Identify systemic issues that contributed to the problem."""
        issues = []

        memory_percent = diagnostic_data.get('memory_usage', {}).get('percent', 0)
        disk_percent = diagnostic_data.get('disk_usage', {}).get('percent', 0)

        if memory_percent > 85:
            issues.append("Chronic memory pressure - consider increasing RAM or optimizing applications")

        if disk_percent > 85:
            issues.append("Storage capacity issues - implement log rotation and cleanup policies")

        # Check for multiple related failures
        error_count = len([link for link in causal_graph if 'error' in link.effect.lower()])
        if error_count > 2:
            issues.append("Multiple cascading failures - investigate for common underlying cause")

        return issues

    def _generate_preventive_measures(self, primary_root_cause: str,
                                    systemic_issues: List[str]) -> List[str]:
        """Generate preventive measures based on root cause and systemic issues."""
        measures = []

        if 'memory' in primary_root_cause.lower():
            measures.extend([
                "Implement memory monitoring and alerts",
                "Set up automatic cleanup of temporary files",
                "Consider memory profiling in development"
            ])

        if 'disk' in primary_root_cause.lower():
            measures.extend([
                "Implement log rotation policies",
                "Set up disk usage monitoring and alerts",
                "Regular cleanup of temporary and cache files"
            ])

        if 'permission' in primary_root_cause.lower():
            measures.extend([
                "Review and standardize file permissions",
                "Implement consistent user/group ownership policies",
                "Use ACLs for complex permission requirements"
            ])

        # Add systemic prevention
        for issue in systemic_issues:
            if 'memory' in issue.lower():
                measures.append("Implement application memory limits and monitoring")
            elif 'storage' in issue.lower():
                measures.append("Set up automated storage management policies")

        return list(set(measures))  # Remove duplicates

    def _refine_hypotheses_deep(self, hypotheses: List[RootCauseHypothesis],
                              diagnostic_data: Dict[str, Any]) -> List[RootCauseHypothesis]:
        """Perform deeper analysis to refine hypotheses."""
        # This would include more sophisticated analysis like:
        # - Log analysis for patterns
        # - Performance metric correlation
        # - Historical failure pattern matching
        # - Code analysis for potential issues

        # For now, just boost confidence of hypotheses with strong evidence
        for hypothesis in hypotheses:
            if len(hypothesis.supporting_evidence) > len(hypothesis.contradicting_evidence):
                hypothesis.confidence = min(hypothesis.confidence + 0.1, 1.0)

        return hypotheses

    def get_analysis_history(self) -> List[RootCauseAnalysis]:
        """Get history of all root cause analyses."""
        return list(self.analysis_history.values())

    def get_analysis(self, analysis_id: str) -> Optional[RootCauseAnalysis]:
        """Get a specific analysis by ID."""
        return self.analysis_history.get(analysis_id)