"""
Pattern Learning System - Detect repetitive workflows from command history
Isaac's intelligent workflow pattern recognition
"""

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Any



@dataclass
class CommandPattern:
    """A detected command pattern."""
    commands: List[str]
    frequency: int
    avg_interval_seconds: float
    last_seen: float
    first_seen: float
    confidence: float
    suggested_name: str
    suggested_description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowPattern:
    """A multi-step workflow pattern."""
    steps: List[List[str]]  # List of command sequences
    frequency: int
    avg_duration_seconds: float
    confidence: float
    suggested_pipeline_name: str
    suggested_description: str
    estimated_savings_seconds: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PatternLearner:
    """Learns patterns from command history to suggest pipeline automation."""

    def __init__(self, min_pattern_length: int = 2, max_pattern_length: int = 10):
        """Initialize pattern learner.

        Args:
            min_pattern_length: Minimum commands in a pattern
            max_pattern_length: Maximum commands in a pattern
        """
        self.min_pattern_length = min_pattern_length
        self.max_pattern_length = max_pattern_length

        # Pattern storage
        self.command_patterns: Dict[str, CommandPattern] = {}
        self.workflow_patterns: List[WorkflowPattern] = []

    def analyze_command_history(self, command_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze command history to find patterns.

        Args:
            command_history: List of command records with 'command', 'timestamp', 'success', etc.

        Returns:
            Analysis results with patterns and suggestions
        """
        if not command_history:
            return {'patterns': [], 'suggestions': []}

        # Extract successful commands
        commands = []
        for record in command_history:
            if record.get('success', True):  # Default to True if not specified
                command = record.get('command', '').strip()
                if command:
                    commands.append({
                        'command': command,
                        'timestamp': record.get('timestamp', time.time()),
                        'session_id': record.get('session_id', 'unknown')
                    })

        # Find command patterns
        command_patterns = self._find_command_patterns(commands)

        # Find workflow patterns
        workflow_patterns = self._find_workflow_patterns(commands)

        # Generate suggestions
        suggestions = self._generate_suggestions(command_patterns, workflow_patterns)

        return {
            'command_patterns': command_patterns,
            'workflow_patterns': workflow_patterns,
            'suggestions': suggestions,
            'analysis_timestamp': time.time()
        }

    def _find_command_patterns(self, commands: List[Dict[str, Any]]) -> List[CommandPattern]:
        """Find frequently repeated individual commands."""
        if not commands:
            return []

        # Group by command
        command_groups = defaultdict(list)
        for cmd in commands:
            command_groups[cmd['command']].append(cmd['timestamp'])

        patterns = []
        for command, timestamps in command_groups.items():
            if len(timestamps) < 2:
                continue

            timestamps.sort()
            frequency = len(timestamps)

            # Calculate average interval
            intervals = []
            for i in range(1, len(timestamps)):
                intervals.append(timestamps[i] - timestamps[i-1])
            avg_interval = sum(intervals) / len(intervals) if intervals else 0

            # Calculate confidence based on frequency and regularity
            time_span = timestamps[-1] - timestamps[0]
            expected_occurrences = time_span / avg_interval if avg_interval > 0 else 0
            regularity_score = min(frequency / expected_occurrences, 1.0) if expected_occurrences > 0 else 0
            confidence = min(frequency / 10.0, 1.0) * regularity_score

            if confidence > 0.3:  # Minimum confidence threshold
                pattern = CommandPattern(
                    commands=[command],
                    frequency=frequency,
                    avg_interval_seconds=avg_interval,
                    last_seen=timestamps[-1],
                    first_seen=timestamps[0],
                    confidence=confidence,
                    suggested_name=self._suggest_command_name(command),
                    suggested_description=f"Run '{command}' (executed {frequency} times)"
                )
                patterns.append(pattern)

        # Sort by confidence
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns

    def _find_workflow_patterns(self, commands: List[Dict[str, Any]]) -> List[WorkflowPattern]:
        """Find sequences of commands that are executed together."""
        if len(commands) < self.min_pattern_length:
            return []

        # Group commands by session to find workflows
        session_commands = defaultdict(list)
        for cmd in commands:
            session_id = cmd.get('session_id', 'unknown')
            session_commands[session_id].append(cmd)

        # Find patterns within sessions
        all_sequences = []
        for session_cmds in session_commands.values():
            if len(session_cmds) >= self.min_pattern_length:
                session_cmds.sort(key=lambda x: x['timestamp'])
                sequences = self._extract_sequences(session_cmds)
                all_sequences.extend(sequences)

        # Group similar sequences
        sequence_groups = self._group_similar_sequences(all_sequences)

        patterns = []
        for sequence_group in sequence_groups.values():
            if len(sequence_group) < 2:  # Need at least 2 occurrences
                continue

            # Calculate pattern statistics
            commands_list = [seq['commands'] for seq in sequence_group]
            durations = [seq['duration'] for seq in sequence_group]

            avg_duration = sum(durations) / len(durations)
            frequency = len(sequence_group)
            confidence = min(frequency / 5.0, 1.0)  # Scale confidence by frequency

            # Estimate time savings (assume 80% of manual execution time)
            estimated_savings = avg_duration * 0.8 * frequency

            if confidence > 0.4:  # Minimum confidence threshold
                pattern = WorkflowPattern(
                    steps=commands_list,
                    frequency=frequency,
                    avg_duration_seconds=avg_duration,
                    confidence=confidence,
                    suggested_pipeline_name=self._suggest_workflow_name(commands_list[0]),
                    suggested_description=f"Automate {len(commands_list[0])} step workflow (run {frequency} times)",
                    estimated_savings_seconds=estimated_savings
                )
                patterns.append(pattern)

        # Sort by potential savings
        patterns.sort(key=lambda p: p.estimated_savings_seconds, reverse=True)
        return patterns

    def _extract_sequences(self, session_commands: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract command sequences from a session."""
        sequences = []

        for length in range(self.min_pattern_length, min(self.max_pattern_length + 1, len(session_commands) + 1)):
            for start_idx in range(len(session_commands) - length + 1):
                end_idx = start_idx + length
                sequence_cmds = session_commands[start_idx:end_idx]

                # Check if commands are close together (within reasonable time)
                start_time = sequence_cmds[0]['timestamp']
                end_time = sequence_cmds[-1]['timestamp']
                duration = end_time - start_time

                # Only consider sequences that take less than 30 minutes
                if duration <= 1800:  # 30 minutes
                    sequences.append({
                        'commands': [cmd['command'] for cmd in sequence_cmds],
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration,
                        'session_id': sequence_cmds[0].get('session_id', 'unknown')
                    })

        return sequences

    def _group_similar_sequences(self, sequences: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group similar command sequences."""
        groups = defaultdict(list)

        for seq in sequences:
            # Create a signature for the sequence
            signature = '|'.join(seq['commands'])
            groups[signature].append(seq)

        return dict(groups)

    def _generate_suggestions(self, command_patterns: List[CommandPattern],
                            workflow_patterns: List[WorkflowPattern]) -> List[Dict[str, Any]]:
        """Generate pipeline suggestions from patterns."""
        suggestions = []

        # Single command suggestions
        for pattern in command_patterns[:5]:  # Top 5
            if pattern.confidence > 0.5:
                suggestion = {
                    'type': 'single_command',
                    'pattern': pattern,
                    'pipeline_template': self._create_single_command_pipeline(pattern),
                    'priority': 'high' if pattern.confidence > 0.8 else 'medium',
                    'reason': f"Command executed {pattern.frequency} times with high regularity"
                }
                suggestions.append(suggestion)

        # Workflow suggestions
        for pattern in workflow_patterns[:3]:  # Top 3
            if pattern.confidence > 0.6:
                suggestion = {
                    'type': 'workflow',
                    'pattern': pattern,
                    'pipeline_template': self._create_workflow_pipeline(pattern),
                    'priority': 'high',
                    'reason': f"Workflow saves ~{int(pattern.estimated_savings_seconds/60)} minutes total"
                }
                suggestions.append(suggestion)

        return suggestions

    def _create_single_command_pipeline(self, pattern: CommandPattern) -> Dict[str, Any]:
        """Create a pipeline template for a single command."""
        command = pattern.commands[0]

        return {
            'name': pattern.suggested_name,
            'description': pattern.suggested_description,
            'steps': [
                {
                    'id': 'run_command',
                    'name': pattern.suggested_name,
                    'type': 'command',
                    'config': {'command': command}
                }
            ],
            'variables': {},
            'triggers': []
        }

    def _create_workflow_pipeline(self, pattern: WorkflowPattern) -> Dict[str, Any]:
        """Create a pipeline template for a workflow."""
        steps = []
        for i, command in enumerate(pattern.steps[0]):  # Use first occurrence as template
            step = {
                'id': f'step_{i+1}',
                'name': f'Step {i+1}: {self._suggest_command_name(command)}',
                'type': 'command',
                'config': {'command': command}
            }
            steps.append(step)

        return {
            'name': pattern.suggested_pipeline_name,
            'description': pattern.suggested_description,
            'steps': steps,
            'variables': {},
            'triggers': []
        }

    def _suggest_command_name(self, command: str) -> str:
        """Suggest a human-readable name for a command."""
        command = command.strip()

        # Common command patterns
        patterns = [
            (r'^git\s+(.*)', lambda m: f"Git {m.group(1).replace('-', ' ')}"),
            (r'^pip\s+install', 'Install Python packages'),
            (r'^pytest', 'Run tests'),
            (r'^python\s+-m\s+build', 'Build package'),
            (r'^docker\s+build', 'Build Docker image'),
            (r'^kubectl\s+apply', 'Deploy to Kubernetes'),
            (r'^npm\s+install', 'Install Node packages'),
            (r'^npm\s+run\s+(\w+)', lambda m: f"Run npm script: {m.group(1)}"),
        ]

        for pattern, name_func in patterns:
            match = re.match(pattern, command, re.IGNORECASE)
            if match:
                if callable(name_func):
                    return name_func(match)
                else:
                    return name_func

        # Fallback: capitalize first word
        words = command.split()
        if words:
            return words[0].capitalize()

        return "Run command"

    def _suggest_workflow_name(self, commands: List[str]) -> str:
        """Suggest a name for a workflow."""
        if not commands:
            return "Workflow"

        first_cmd = commands[0]
        cmd_count = len(commands)

        if cmd_count == 2:
            return f"{self._suggest_command_name(first_cmd)} + 1 more"
        elif cmd_count == 3:
            return f"{self._suggest_command_name(first_cmd)} + 2 more"
        else:
            return f"{self._suggest_command_name(first_cmd)} workflow"