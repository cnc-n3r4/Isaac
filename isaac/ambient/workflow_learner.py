"""
Workflow Learning - Detect patterns in user behavior and command sequences
Isaac's ambient intelligence system for learning user workflows
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict


@dataclass
class CommandPattern:
    """Represents a detected command pattern."""
    pattern_id: str
    commands: List[str]
    frequency: int
    avg_interval: float  # Average time between executions
    last_seen: float
    first_seen: float
    confidence: float  # 0-1, how confident we are this is a real pattern
    description: str
    suggested_pipeline: Optional[Dict[str, Any]] = None


@dataclass
class WorkflowPattern:
    """Represents a multi-step workflow pattern."""
    workflow_id: str
    steps: List[str]
    frequency: int
    avg_duration: float
    success_rate: float
    last_executed: float
    tags: List[str]
    suggested_automation: Optional[Dict[str, Any]] = None


class WorkflowLearner:
    """Learns patterns from user command history and behavior."""

    def __init__(self, history_path: Optional[Path] = None):
        """Initialize workflow learner.

        Args:
            history_path: Path to command history file
        """
        if history_path is None:
            isaac_dir = Path.home() / '.isaac'
            isaac_dir.mkdir(exist_ok=True)
            history_path = isaac_dir / 'command_history.json'

        self.history_path = history_path
        self.patterns: Dict[str, CommandPattern] = {}
        self.workflows: Dict[str, WorkflowPattern] = {}
        self.command_sequences: List[List[str]] = []
        self.min_pattern_length = 3  # Minimum commands to consider a pattern
        self.min_frequency = 2  # Minimum times a pattern must occur
        self.pattern_window = 300  # 5 minutes - commands within this window are related

        self._load_existing_patterns()

    def _normalize_timestamp(self, timestamp) -> float:
        """Normalize timestamp to float, handling string timestamps."""
        if isinstance(timestamp, str):
            # Try to parse as float, fallback to current time
            try:
                return float(timestamp)
            except ValueError:
                return time.time()
        elif isinstance(timestamp, (int, float)):
            return float(timestamp)
        else:
            return time.time()

    def _load_existing_patterns(self) -> None:
        """Load previously learned patterns."""
        pattern_file = self.history_path.parent / 'learned_patterns.json'
        if pattern_file.exists():
            try:
                with open(pattern_file, 'r') as f:
                    data = json.load(f)
                    # Load command patterns
                    for pattern_data in data.get('command_patterns', []):
                        pattern = CommandPattern(**pattern_data)
                        self.patterns[pattern.pattern_id] = pattern

                    # Load workflow patterns
                    for workflow_data in data.get('workflow_patterns', []):
                        workflow = WorkflowPattern(**workflow_data)
                        self.workflows[workflow.workflow_id] = workflow
            except Exception as e:
                print(f"Warning: Could not load existing patterns: {e}")

    def _save_patterns(self) -> None:
        """Save learned patterns to disk."""
        pattern_file = self.history_path.parent / 'learned_patterns.json'
        data = {
            'command_patterns': [asdict(p) for p in self.patterns.values()],
            'workflow_patterns': [asdict(w) for w in self.workflows.values()],
            'last_updated': time.time()
        }

        try:
            with open(pattern_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save patterns: {e}")

    def analyze_command_history(self) -> Dict[str, Any]:
        """Analyze command history to detect patterns.

        Returns:
            Analysis results with detected patterns and suggestions
        """
        if not self.history_path.exists():
            return {'patterns_found': 0, 'workflows_found': 0, 'suggestions': []}

        # Load command history
        try:
            with open(self.history_path, 'r') as f:
                history = json.load(f)
        except Exception as e:
            return {'error': f'Could not load history: {e}'}

        # Extract command sequences from history
        sequences = self._extract_command_sequences(history)
        self.command_sequences = sequences

        # Analyze for patterns
        new_patterns = self._detect_command_patterns(sequences)
        new_workflows = self._detect_workflow_patterns(sequences)

        # Update existing patterns
        self._update_patterns(new_patterns, new_workflows)

        # Generate suggestions
        suggestions = self._generate_suggestions()

        # Save updated patterns
        self._save_patterns()

        return {
            'patterns_found': len(self.patterns),
            'workflows_found': len(self.workflows),
            'new_patterns': len(new_patterns),
            'new_workflows': len(new_workflows),
            'suggestions': suggestions
        }

    def _extract_command_sequences(self, history: Dict[str, Any]) -> List[List[str]]:
        """Extract command sequences from history data."""
        sequences = []

        # Handle different history formats
        if isinstance(history, list):
            commands = history
        elif isinstance(history, dict) and 'commands' in history:
            commands = history['commands']
        else:
            return sequences

        # Group commands by time windows
        current_sequence = []
        last_time = 0

        for cmd_data in sorted(commands, key=lambda x: self._normalize_timestamp(x.get('timestamp', 0)) if isinstance(x, dict) else time.time()):
            cmd_time = self._normalize_timestamp(cmd_data.get('timestamp', 0)) if isinstance(cmd_data, dict) else time.time()
            command = cmd_data.get('command', '').strip() if isinstance(cmd_data, dict) else str(cmd_data).strip()

            if not command:
                continue

            # Start new sequence if time gap is too large
            if last_time > 0 and (cmd_time - last_time) > self.pattern_window:
                if len(current_sequence) >= 2:
                    sequences.append(current_sequence)
                current_sequence = []

            current_sequence.append(command)
            last_time = cmd_time

        # Add final sequence
        if len(current_sequence) >= 2:
            sequences.append(current_sequence)

        return sequences

    def _detect_command_patterns(self, sequences: List[List[str]]) -> List[CommandPattern]:
        """Detect repetitive command patterns."""
        patterns = []

        # Count command frequencies
        command_counter = Counter()
        for sequence in sequences:
            for cmd in sequence:
                command_counter[cmd] += 1

        # Find frequently used commands that might benefit from automation
        frequent_commands = [
            cmd for cmd, count in command_counter.items()
            if count >= self.min_frequency
        ]

        # Look for command sequences that repeat
        sequence_counter = Counter()
        for sequence in sequences:
            if len(sequence) >= self.min_pattern_length:
                # Look for subsequences
                for i in range(len(sequence) - self.min_pattern_length + 1):
                    subseq = tuple(sequence[i:i + self.min_pattern_length])
                    sequence_counter[subseq] += 1

        # Create patterns from frequent sequences
        for sequence, count in sequence_counter.items():
            if count >= self.min_frequency:
                pattern_id = f"pattern_{hash(sequence) % 10000}"
                commands = list(sequence)

                # Calculate timing (simplified)
                avg_interval = 300.0  # 5 minutes default
                confidence = min(count / 10.0, 1.0)  # Higher frequency = higher confidence

                pattern = CommandPattern(
                    pattern_id=pattern_id,
                    commands=commands,
                    frequency=count,
                    avg_interval=avg_interval,
                    last_seen=time.time(),
                    first_seen=time.time() - (count * avg_interval),
                    confidence=confidence,
                    description=f"Command sequence: {' → '.join(commands[:3])}{'...' if len(commands) > 3 else ''}"
                )

                patterns.append(pattern)

        return patterns

    def _detect_workflow_patterns(self, sequences: List[List[str]]) -> List[WorkflowPattern]:
        """Detect multi-step workflow patterns."""
        workflows = []

        # Group sequences by their first command to find workflow starts
        workflow_starts = defaultdict(list)
        for sequence in sequences:
            if sequence:
                workflow_starts[sequence[0]].append(sequence)

        # Analyze each potential workflow
        for start_cmd, sequences in workflow_starts.items():
            if len(sequences) < self.min_frequency:
                continue

            # Find common workflow patterns
            workflow_counter = Counter()
            for seq in sequences:
                workflow_counter[tuple(seq)] += 1

            # Create workflow patterns
            for workflow_seq, count in workflow_counter.items():
                if count >= self.min_frequency and len(workflow_seq) >= 3:
                    workflow_id = f"workflow_{hash(workflow_seq) % 10000}"
                    steps = list(workflow_seq)

                    # Calculate success rate (simplified - assume all successful for now)
                    success_rate = 0.9  # 90% success rate assumption

                    # Calculate average duration (simplified)
                    avg_duration = len(steps) * 30.0  # 30 seconds per step

                    # Generate tags based on commands
                    tags = self._generate_workflow_tags(steps)

                    workflow = WorkflowPattern(
                        workflow_id=workflow_id,
                        steps=steps,
                        frequency=count,
                        avg_duration=avg_duration,
                        success_rate=success_rate,
                        last_executed=time.time(),
                        tags=tags
                    )

                    workflows.append(workflow)

        return workflows

    def _generate_workflow_tags(self, steps: List[str]) -> List[str]:
        """Generate tags for a workflow based on its steps."""
        tags = []

        # Analyze commands for common patterns
        if any('git' in step.lower() for step in steps):
            tags.append('git')
        if any('test' in step.lower() or 'pytest' in step.lower() for step in steps):
            tags.append('testing')
        if any('build' in step.lower() or 'compile' in step.lower() for step in steps):
            tags.append('build')
        if any('deploy' in step.lower() or 'upload' in step.lower() for step in steps):
            tags.append('deployment')
        if any('pip' in step.lower() or 'install' in step.lower() for step in steps):
            tags.append('package-management')

        # Add complexity tag
        if len(steps) > 5:
            tags.append('complex')
        elif len(steps) <= 3:
            tags.append('simple')

        return tags

    def _update_patterns(self, new_patterns: List[CommandPattern],
                        new_workflows: List[WorkflowPattern]) -> None:
        """Update existing patterns with new data."""
        # Update command patterns
        for new_pattern in new_patterns:
            existing = self.patterns.get(new_pattern.pattern_id)
            if existing:
                # Update existing pattern
                existing.frequency += new_pattern.frequency
                existing.last_seen = new_pattern.last_seen
                existing.confidence = min(existing.confidence + 0.1, 1.0)
            else:
                # Add new pattern
                self.patterns[new_pattern.pattern_id] = new_pattern

        # Update workflow patterns
        for new_workflow in new_workflows:
            existing = self.workflows.get(new_workflow.workflow_id)
            if existing:
                # Update existing workflow
                existing.frequency += new_workflow.frequency
                existing.last_executed = new_workflow.last_executed
            else:
                # Add new workflow
                self.workflows[new_workflow.workflow_id] = new_workflow

    def _generate_suggestions(self) -> List[Dict[str, Any]]:
        """Generate suggestions based on learned patterns."""
        suggestions = []

        # Suggest pipelines for frequent command patterns
        for pattern in self.patterns.values():
            if pattern.confidence > 0.7 and pattern.frequency >= 5:
                suggestion = {
                    'type': 'pipeline_suggestion',
                    'pattern_id': pattern.pattern_id,
                    'description': f"Create a pipeline for this repeated command sequence",
                    'commands': pattern.commands,
                    'frequency': pattern.frequency,
                    'potential_time_saved': pattern.frequency * len(pattern.commands) * 10  # 10 seconds per command
                }
                suggestions.append(suggestion)

        # Suggest automation for complex workflows
        for workflow in self.workflows.values():
            if workflow.success_rate > 0.8 and len(workflow.steps) >= 4:
                suggestion = {
                    'type': 'workflow_automation',
                    'workflow_id': workflow.workflow_id,
                    'description': f"Automate this {len(workflow.steps)}-step workflow",
                    'steps': workflow.steps,
                    'frequency': workflow.frequency,
                    'tags': workflow.tags,
                    'time_saved_per_run': workflow.avg_duration
                }
                suggestions.append(suggestion)

        return suggestions

    def get_pattern_suggestions(self, current_command: str = "") -> List[Dict[str, Any]]:
        """Get suggestions based on current context."""
        suggestions = []

        if current_command:
            # Find patterns that start with similar commands
            for pattern in self.patterns.values():
                if pattern.commands and pattern.commands[0].startswith(current_command):
                    suggestions.append({
                        'type': 'command_completion',
                        'pattern': pattern,
                        'next_commands': pattern.commands[1:] if len(pattern.commands) > 1 else []
                    })

        # Add general suggestions
        suggestions.extend(self._generate_suggestions()[:3])  # Top 3 suggestions

        return suggestions

    def suggest_pipeline_for_commands(self, commands: List[str]) -> Optional[Dict[str, Any]]:
        """Suggest a pipeline for a given set of commands."""
        if len(commands) < 2:
            return None

        # Check if this matches an existing pattern
        for pattern in self.patterns.values():
            if pattern.commands == commands:
                return {
                    'pipeline_name': f"Automated {commands[0]} workflow",
                    'description': f"Automates the sequence: {' → '.join(commands)}",
                    'steps': [
                        {
                            'id': f'step_{i}',
                            'name': f'Step {i+1}: {cmd.split()[0]}',
                            'type': 'command',
                            'config': {'command': cmd},
                            'depends_on': [f'step_{i-1}'] if i > 0 else [],
                            'timeout_seconds': 300
                        }
                        for i, cmd in enumerate(commands)
                    ],
                    'pattern_id': pattern.pattern_id
                }

        # Generate new pipeline suggestion
        return {
            'pipeline_name': f"Workflow: {commands[0].split()[0]} → {commands[-1].split()[0]}",
            'description': f"Automates {len(commands)} sequential commands",
            'steps': [
                {
                    'id': f'step_{i}',
                    'name': f'Step {i+1}: {cmd.split()[0]}',
                    'type': 'command',
                    'config': {'command': cmd},
                    'depends_on': [f'step_{i-1}'] if i > 0 else [],
                    'timeout_seconds': 300
                }
                for i, cmd in enumerate(commands)
            ]
        }