"""
Task Division System - Phase 4.2
Intelligent task division between AI and human for simultaneous work.
"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
import uuid

from isaac.core.session_manager import SessionManager


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskAssignee(Enum):
    """Who is assigned to the task."""
    ISAAC = "isaac"
    HUMAN = "human"
    BOTH = "both"
    UNASSIGNED = "unassigned"


@dataclass
class Task:
    """A task in the pair programming session."""
    id: str
    session_id: str
    title: str
    description: str
    assignee: str
    status: str
    priority: str
    created_at: float
    started_at: Optional[float]
    completed_at: Optional[float]
    estimated_minutes: Optional[int]
    dependencies: List[str]  # Task IDs this task depends on
    context: Dict[str, Any]
    result: Optional[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.context is None:
            self.context = {}


class TaskDivider:
    """Intelligent task division between AI and human."""

    def __init__(self, session_manager: SessionManager):
        """Initialize task divider.

        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.data_dir = Path.home() / '.isaac' / 'pairing'
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Database for task storage
        self.db_path = self.data_dir / 'tasks.db'
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for task storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    session_id TEXT,
                    title TEXT,
                    description TEXT,
                    assignee TEXT,
                    status TEXT,
                    priority TEXT,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL,
                    estimated_minutes INTEGER,
                    dependencies TEXT,
                    context TEXT,
                    result TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session ON tasks(session_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_assignee ON tasks(assignee)')

    def create_task(
        self,
        session_id: str,
        title: str,
        description: str,
        assignee: TaskAssignee = TaskAssignee.UNASSIGNED,
        priority: TaskPriority = TaskPriority.MEDIUM,
        estimated_minutes: Optional[int] = None,
        dependencies: Optional[List[str]] = None
    ) -> Task:
        """Create a new task.

        Args:
            session_id: Pairing session ID
            title: Task title
            description: Task description
            assignee: Who should do this task
            priority: Task priority
            estimated_minutes: Estimated time in minutes
            dependencies: List of task IDs this depends on

        Returns:
            Created task
        """
        task = Task(
            id=str(uuid.uuid4()),
            session_id=session_id,
            title=title,
            description=description,
            assignee=assignee.value,
            status=TaskStatus.PENDING.value,
            priority=priority.value,
            created_at=datetime.now().timestamp(),
            started_at=None,
            completed_at=None,
            estimated_minutes=estimated_minutes,
            dependencies=dependencies or [],
            context={}
        )

        self._save_task(task)
        return task

    def suggest_task_division(
        self,
        overall_task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Task]:
        """Suggest how to divide a large task between Isaac and human.

        Args:
            overall_task: Description of the overall task
            context: Additional context (files, codebase info, etc.)

        Returns:
            List of suggested subtasks
        """
        # Generate a session ID for this task group
        session_id = str(uuid.uuid4())
        tasks = []

        # Simple heuristic-based task division
        # In a real implementation, this would use AI to intelligently divide tasks

        # Common task patterns
        if "refactor" in overall_task.lower():
            tasks.extend(self._divide_refactoring_task(session_id, overall_task, context))
        elif "feature" in overall_task.lower() or "implement" in overall_task.lower():
            tasks.extend(self._divide_feature_task(session_id, overall_task, context))
        elif "bug" in overall_task.lower() or "fix" in overall_task.lower():
            tasks.extend(self._divide_bug_fix_task(session_id, overall_task, context))
        elif "test" in overall_task.lower():
            tasks.extend(self._divide_testing_task(session_id, overall_task, context))
        else:
            # Generic division
            tasks.extend(self._divide_generic_task(session_id, overall_task, context))

        return tasks

    def _divide_refactoring_task(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Task]:
        """Divide a refactoring task."""
        return [
            self.create_task(
                session_id,
                "Analyze current code structure",
                "Review the code to understand current architecture and identify refactoring opportunities",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Write tests for existing behavior",
                "Ensure current behavior is well-tested before refactoring",
                assignee=TaskAssignee.BOTH,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Refactor implementation",
                "Apply refactoring changes to improve code structure",
                assignee=TaskAssignee.HUMAN,
                priority=TaskPriority.MEDIUM
            ),
            self.create_task(
                session_id,
                "Update documentation",
                "Update docs to reflect refactored code",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.LOW
            ),
        ]

    def _divide_feature_task(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Task]:
        """Divide a feature implementation task."""
        return [
            self.create_task(
                session_id,
                "Design feature architecture",
                "Plan the feature's architecture and integration points",
                assignee=TaskAssignee.BOTH,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Implement core logic",
                "Write the main feature implementation",
                assignee=TaskAssignee.HUMAN,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Write unit tests",
                "Create comprehensive unit tests for the feature",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.MEDIUM
            ),
            self.create_task(
                session_id,
                "Integration and testing",
                "Integrate feature and run integration tests",
                assignee=TaskAssignee.BOTH,
                priority=TaskPriority.MEDIUM
            ),
        ]

    def _divide_bug_fix_task(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Task]:
        """Divide a bug fix task."""
        return [
            self.create_task(
                session_id,
                "Reproduce the bug",
                "Create a minimal reproduction of the issue",
                assignee=TaskAssignee.BOTH,
                priority=TaskPriority.CRITICAL
            ),
            self.create_task(
                session_id,
                "Root cause analysis",
                "Investigate and identify the root cause",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Implement fix",
                "Apply the fix to resolve the bug",
                assignee=TaskAssignee.HUMAN,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Write regression test",
                "Create test to prevent bug from recurring",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.MEDIUM
            ),
        ]

    def _divide_testing_task(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Task]:
        """Divide a testing task."""
        return [
            self.create_task(
                session_id,
                "Identify test scenarios",
                "List all scenarios that need testing",
                assignee=TaskAssignee.BOTH,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Write unit tests",
                "Implement unit tests for individual components",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.MEDIUM
            ),
            self.create_task(
                session_id,
                "Write integration tests",
                "Implement integration tests for system workflows",
                assignee=TaskAssignee.HUMAN,
                priority=TaskPriority.MEDIUM
            ),
            self.create_task(
                session_id,
                "Review test coverage",
                "Analyze coverage and identify gaps",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.LOW
            ),
        ]

    def _divide_generic_task(
        self,
        session_id: str,
        task: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Task]:
        """Divide a generic task."""
        return [
            self.create_task(
                session_id,
                "Research and planning",
                "Understand requirements and plan approach",
                assignee=TaskAssignee.BOTH,
                priority=TaskPriority.HIGH
            ),
            self.create_task(
                session_id,
                "Implementation",
                f"Implement: {task}",
                assignee=TaskAssignee.HUMAN,
                priority=TaskPriority.MEDIUM
            ),
            self.create_task(
                session_id,
                "Testing and validation",
                "Test the implementation",
                assignee=TaskAssignee.ISAAC,
                priority=TaskPriority.MEDIUM
            ),
        ]

    def start_task(self, task_id: str) -> bool:
        """Mark a task as in progress.

        Args:
            task_id: Task ID

        Returns:
            True if successful
        """
        task = self.get_task(task_id)
        if not task:
            return False

        # Check dependencies
        if not self._dependencies_completed(task):
            return False

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE tasks
                SET status = ?, started_at = ?
                WHERE id = ?
            ''', (TaskStatus.IN_PROGRESS.value, datetime.now().timestamp(), task_id))

        return True

    def complete_task(self, task_id: str, result: Optional[str] = None) -> bool:
        """Mark a task as completed.

        Args:
            task_id: Task ID
            result: Optional result description

        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE tasks
                SET status = ?, completed_at = ?, result = ?
                WHERE id = ?
            ''', (TaskStatus.COMPLETED.value, datetime.now().timestamp(), result, task_id))

        return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, session_id, title, description, assignee, status, priority,
                       created_at, started_at, completed_at, estimated_minutes,
                       dependencies, context, result
                FROM tasks
                WHERE id = ?
            ''', (task_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return Task(
                id=row[0],
                session_id=row[1],
                title=row[2],
                description=row[3],
                assignee=row[4],
                status=row[5],
                priority=row[6],
                created_at=row[7],
                started_at=row[8],
                completed_at=row[9],
                estimated_minutes=row[10],
                dependencies=json.loads(row[11]) if row[11] else [],
                context=json.loads(row[12]) if row[12] else {},
                result=row[13]
            )

    def get_session_tasks(self, session_id: str) -> List[Task]:
        """Get all tasks for a session.

        Args:
            session_id: Session ID

        Returns:
            List of tasks
        """
        tasks = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT id, session_id, title, description, assignee, status, priority,
                       created_at, started_at, completed_at, estimated_minutes,
                       dependencies, context, result
                FROM tasks
                WHERE session_id = ?
                ORDER BY priority DESC, created_at ASC
            ''', (session_id,))

            for row in cursor:
                task = Task(
                    id=row[0],
                    session_id=row[1],
                    title=row[2],
                    description=row[3],
                    assignee=row[4],
                    status=row[5],
                    priority=row[6],
                    created_at=row[7],
                    started_at=row[8],
                    completed_at=row[9],
                    estimated_minutes=row[10],
                    dependencies=json.loads(row[11]) if row[11] else [],
                    context=json.loads(row[12]) if row[12] else {},
                    result=row[13]
                )
                tasks.append(task)

        return tasks

    def _dependencies_completed(self, task: Task) -> bool:
        """Check if all task dependencies are completed.

        Args:
            task: Task to check

        Returns:
            True if all dependencies are completed
        """
        if not task.dependencies:
            return True

        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(task.dependencies))
            cursor = conn.execute(f'''
                SELECT COUNT(*) FROM tasks
                WHERE id IN ({placeholders})
                AND status = ?
            ''', (*task.dependencies, TaskStatus.COMPLETED.value))

            completed_count = cursor.fetchone()[0]
            return completed_count == len(task.dependencies)

    def _save_task(self, task: Task):
        """Save task to database.

        Args:
            task: Task to save
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO tasks
                (id, session_id, title, description, assignee, status, priority,
                 created_at, started_at, completed_at, estimated_minutes,
                 dependencies, context, result)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id,
                task.session_id,
                task.title,
                task.description,
                task.assignee,
                task.status,
                task.priority,
                task.created_at,
                task.started_at,
                task.completed_at,
                task.estimated_minutes,
                json.dumps(task.dependencies),
                json.dumps(task.context),
                task.result
            ))
