"""Workflow state definitions and enums."""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


class WorkflowStatus(Enum):
    """Workflow execution status enum."""

    IDLE = "idle"
    PARSING = "parsing"
    VALIDATING = "validating"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class WorkflowType(Enum):
    """Workflow type enum."""

    STANDARD = "standard"
    FULL = "full"
    INIT = "init"


# Valid state transitions
TRANSITIONS: Dict[WorkflowStatus, list[WorkflowStatus]] = {
    WorkflowStatus.IDLE: [WorkflowStatus.PARSING],
    WorkflowStatus.PARSING: [WorkflowStatus.VALIDATING, WorkflowStatus.FAILED],
    WorkflowStatus.VALIDATING: [WorkflowStatus.PLANNING, WorkflowStatus.FAILED],
    WorkflowStatus.PLANNING: [WorkflowStatus.EXECUTING, WorkflowStatus.FAILED],
    WorkflowStatus.EXECUTING: [WorkflowStatus.VERIFYING, WorkflowStatus.FAILED],
    WorkflowStatus.VERIFYING: [WorkflowStatus.COMPLETING, WorkflowStatus.FAILED],
    WorkflowStatus.COMPLETING: [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED],
    WorkflowStatus.COMPLETED: [],
    WorkflowStatus.FAILED: [WorkflowStatus.IDLE],
    WorkflowStatus.PAUSED: [WorkflowStatus.EXECUTING, WorkflowStatus.FAILED],
}


@dataclass
class WorkflowState:
    """Workflow state dataclass.

    Represents the runtime state of a workflow instance.
    """

    workflow_type: WorkflowType
    session_id: str
    status: WorkflowStatus
    current_phase: str
    workflow_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary."""
        return {
            "workflow_type": self.workflow_type.value,
            "session_id": self.session_id,
            "status": self.status.value,
            "current_phase": self.current_phase,
            "workflow_id": self.workflow_id,
            "context": self.context,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowState":
        """Create state from dictionary."""
        return cls(
            workflow_type=WorkflowType(data.get("workflow_type", "standard")),
            session_id=data["session_id"],
            status=WorkflowStatus(data.get("status", "idle")),
            current_phase=data.get("current_phase", ""),
            workflow_id=data.get("workflow_id", ""),
            context=data.get("context", {}),
            result=data.get("result", {}),
            error=data.get("error"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def can_transition_to(self, new_status: WorkflowStatus) -> bool:
        """Check if transition to new status is valid."""
        allowed = TRANSITIONS.get(self.status, [])
        return new_status in allowed

    def transition_to(self, new_status: WorkflowStatus) -> bool:
        """Attempt to transition to new status.

        Returns True if transition was successful, False otherwise.
        """
        if self.can_transition_to(new_status):
            self.status = new_status
            self.updated_at = None  # Will be set by persistence
            return True
        return False

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value."""
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self.context.get(key, default)
