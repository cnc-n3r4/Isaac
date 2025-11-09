"""
Intelligent Pipeline Builder - Automated workflow creation and execution
Isaac's pipeline system for workflow automation
"""

import json
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Union
from abc import ABC, abstractmethod


class PipelineStatus(Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepType(Enum):
    """Types of pipeline steps."""
    COMMAND = "command"
    SCRIPT = "script"
    CONDITION = "condition"
    WAIT = "wait"
    NOTIFICATION = "notification"
    PARALLEL = "parallel"
    LOOP = "loop"


@dataclass
class PipelineStep:
    """A single step in a pipeline."""
    id: str
    name: str
    type: StepType
    config: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    retry_delay_seconds: int = 5
    on_failure: str = "stop"  # stop, continue, retry
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate step configuration."""
        if not self.id:
            raise ValueError("Step ID cannot be empty")
        if not self.name:
            raise ValueError("Step name cannot be empty")


@dataclass
class PipelineExecution:
    """Result of a pipeline execution."""
    pipeline_id: str
    execution_id: str
    start_time: float
    end_time: Optional[float] = None
    status: PipelineStatus = PipelineStatus.PENDING
    steps_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """Get execution duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def is_complete(self) -> bool:
        """Check if execution is complete."""
        return self.status in [PipelineStatus.SUCCESS, PipelineStatus.FAILED, PipelineStatus.CANCELLED]


@dataclass
class Pipeline:
    """A complete pipeline definition."""
    id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    steps: List[PipelineStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    max_parallel_steps: int = 3
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate pipeline configuration."""
        if not self.id:
            raise ValueError("Pipeline ID cannot be empty")
        if not self.name:
            raise ValueError("Pipeline name cannot be empty")

        # Validate step dependencies
        step_ids = {step.id for step in self.steps}
        for step in self.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    raise ValueError(f"Step {step.id} depends on unknown step {dep}")

    def get_step(self, step_id: str) -> Optional[PipelineStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_roots(self) -> List[PipelineStep]:
        """Get steps with no dependencies."""
        return [step for step in self.steps if not step.depends_on]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'steps': [self._step_to_dict(step) for step in self.steps],
            'variables': self.variables,
            'triggers': self.triggers,
            'timeout_seconds': self.timeout_seconds,
            'max_parallel_steps': self.max_parallel_steps,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Pipeline':
        """Create from dictionary."""
        steps = [cls._step_from_dict(step_data) for step_data in data['steps']]
        return cls(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            steps=steps,
            variables=data.get('variables', {}),
            triggers=data.get('triggers', []),
            timeout_seconds=data.get('timeout_seconds'),
            max_parallel_steps=data.get('max_parallel_steps', 3),
            created_at=data.get('created_at', time.time()),
            updated_at=data.get('updated_at', time.time()),
            metadata=data.get('metadata', {})
        )

    @staticmethod
    def _step_to_dict(step: PipelineStep) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            'id': step.id,
            'name': step.name,
            'type': step.type.value,
            'config': step.config,
            'depends_on': step.depends_on,
            'timeout_seconds': step.timeout_seconds,
            'retry_count': step.retry_count,
            'retry_delay_seconds': step.retry_delay_seconds,
            'on_failure': step.on_failure,
            'metadata': step.metadata
        }

    @staticmethod
    def _step_from_dict(data: Dict[str, Any]) -> PipelineStep:
        """Create step from dictionary."""
        return PipelineStep(
            id=data['id'],
            name=data['name'],
            type=StepType(data['type']),
            config=data.get('config', {}),
            depends_on=data.get('depends_on', []),
            timeout_seconds=data.get('timeout_seconds'),
            retry_count=data.get('retry_count', 0),
            retry_delay_seconds=data.get('retry_delay_seconds', 5),
            on_failure=data.get('on_failure', 'stop'),
            metadata=data.get('metadata', {})
        )