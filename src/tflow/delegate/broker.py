"""Delegate broker for task management."""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid


class DelegateStatus(Enum):
    """Delegate task status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DelegateTask:
    """Delegate task dataclass.

    Represents a task to be delegated to an agent.
    """

    task_id: str
    name: str
    description: str
    status: DelegateStatus = DelegateStatus.PENDING
    assigned_agent: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        """Initialize timestamps if not set."""
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DelegateTask":
        """Create task from dictionary."""
        return cls(
            task_id=data["task_id"],
            name=data["name"],
            description=data["description"],
            status=DelegateStatus(data.get("status", "pending")),
            assigned_agent=data.get("assigned_agent"),
            input_data=data.get("input_data", {}),
            output_data=data.get("output_data"),
            error=data.get("error"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
        )

    def start(self) -> bool:
        """Mark task as started.

        Returns True if status was PENDING, False otherwise.
        """
        if self.status == DelegateStatus.PENDING:
            self.status = DelegateStatus.IN_PROGRESS
            self.started_at = datetime.utcnow().isoformat()
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def complete(self, output_data: Optional[Dict[str, Any]] = None) -> bool:
        """Mark task as completed.

        Args:
            output_data: Optional output data from task execution
        """
        if self.status in [DelegateStatus.IN_PROGRESS, DelegateStatus.WAITING_INPUT]:
            self.status = DelegateStatus.COMPLETED
            self.output_data = output_data
            self.completed_at = datetime.utcnow().isoformat()
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def fail(self, error: str) -> bool:
        """Mark task as failed.

        Args:
            error: Error message
        """
        if self.status in [DelegateStatus.IN_PROGRESS, DelegateStatus.WAITING_INPUT]:
            self.status = DelegateStatus.FAILED
            self.error = error
            self.completed_at = datetime.utcnow().isoformat()
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def wait_input(self) -> bool:
        """Mark task as waiting for input.

        Returns True if status was IN_PROGRESS, False otherwise.
        """
        if self.status == DelegateStatus.IN_PROGRESS:
            self.status = DelegateStatus.WAITING_INPUT
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def cancel(self) -> bool:
        """Cancel the task."""
        if self.status in [
            DelegateStatus.PENDING,
            DelegateStatus.IN_PROGRESS,
            DelegateStatus.WAITING_INPUT,
        ]:
            self.status = DelegateStatus.CANCELLED
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def retry(self) -> bool:
        """Retry the task.

        Returns True if retry count not exceeded, False otherwise.
        """
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = DelegateStatus.PENDING
            self.error = None
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False


class DelegateBroker:
    """Broker for managing delegate tasks.

    Provides task lifecycle management: create, update, query tasks.
    """

    def __init__(self):
        """Initialize the delegate broker."""
        self._tasks: Dict[str, DelegateTask] = {}

    def create_task(
        self,
        name: str,
        description: str,
        input_data: Optional[Dict[str, Any]] = None,
        assigned_agent: Optional[str] = None,
        max_retries: int = 3,
    ) -> DelegateTask:
        """Create a new delegate task.

        Args:
            name: Task name
            description: Task description
            input_data: Optional input data
            assigned_agent: Optional agent to assign to
            max_retries: Maximum retry count

        Returns:
            Created DelegateTask
        """
        task = DelegateTask(
            task_id=str(uuid.uuid4()),
            name=name,
            description=description,
            input_data=input_data or {},
            assigned_agent=assigned_agent,
            max_retries=max_retries,
        )
        self._tasks[task.task_id] = task
        return task

    def get_task(self, task_id: str) -> Optional[DelegateTask]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            DelegateTask if found, None otherwise
        """
        return self._tasks.get(task_id)

    def update_task(self, task: DelegateTask) -> bool:
        """Update a task.

        Args:
            task: Task to update

        Returns:
            True if updated, False if not found
        """
        if task.task_id in self._tasks:
            task.updated_at = datetime.utcnow().isoformat()
            self._tasks[task.task_id] = task
            return True
        return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task.

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def list_tasks(
        self,
        status: Optional[DelegateStatus] = None,
        assigned_agent: Optional[str] = None,
    ) -> List[DelegateTask]:
        """List tasks with optional filters.

        Args:
            status: Filter by status
            assigned_agent: Filter by assigned agent

        Returns:
            List of matching tasks
        """
        tasks = list(self._tasks.values())

        if status is not None:
            tasks = [t for t in tasks if t.status == status]

        if assigned_agent is not None:
            tasks = [t for t in tasks if t.assigned_agent == assigned_agent]

        return tasks

    def get_pending_tasks(self) -> List[DelegateTask]:
        """Get all pending tasks."""
        return self.list_tasks(status=DelegateStatus.PENDING)

    def get_active_tasks(self) -> List[DelegateTask]:
        """Get all active (in_progress) tasks."""
        return self.list_tasks(status=DelegateStatus.IN_PROGRESS)

    def assign_task(self, task_id: str, agent_id: str) -> bool:
        """Assign a task to an agent.

        Args:
            task_id: Task ID
            agent_id: Agent ID to assign

        Returns:
            True if assigned, False if not found
        """
        task = self.get_task(task_id)
        if task:
            task.assigned_agent = agent_id
            task.updated_at = datetime.utcnow().isoformat()
            return True
        return False
