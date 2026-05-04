"""Workflow engine with state machine implementation."""

from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
import uuid

from tflow.workflow.state import (
    WorkflowState,
    WorkflowStatus,
    WorkflowType,
    TRANSITIONS,
)
from tflow.workflow.persistence import WorkflowPersistence


# Phase handler type
PhaseHandler = Callable[["WorkflowEngine", WorkflowState], bool]


class WorkflowEngine:
    """Workflow engine with simple state machine.

    Manages workflow execution through phases:
    IDLE -> PARSING -> VALIDATING -> PLANNING -> EXECUTING -> VERIFYING -> COMPLETING -> COMPLETED
    """

    def __init__(
        self,
        workflow_id: Optional[str] = None,
        name: Optional[str] = None,
        workflow_type: WorkflowType = WorkflowType.STANDARD,
        persistence: Optional[WorkflowPersistence] = None,
    ):
        """Initialize workflow engine.

        Args:
            workflow_id: Unique workflow ID. Auto-generated if not provided.
            name: Workflow name.
            workflow_type: Type of workflow.
            persistence: Persistence layer. Created if not provided.
        """
        self.workflow_id = workflow_id or str(uuid.uuid4())
        self.name = name or f"workflow-{self.workflow_id[:8]}"
        self.workflow_type = workflow_type

        self._persistence = persistence or WorkflowPersistence()
        self._state: Optional[WorkflowState] = None
        self._handlers: Dict[WorkflowStatus, List[PhaseHandler]] = {}

        # Load existing state or create new
        self._load_or_create_state()

    def _load_or_create_state(self) -> None:
        """Load existing state or create new one."""
        existing = self._persistence.load(self.workflow_id)
        if existing:
            self._state = existing
        else:
            self._state = WorkflowState(
                workflow_id=self.workflow_id,
                name=self.name,
                status=WorkflowStatus.IDLE,
                workflow_type=self.workflow_type,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
            )
            self._persistence.save(self._state)

    @property
    def state(self) -> WorkflowState:
        """Get current workflow state."""
        return self._state

    @property
    def status(self) -> WorkflowStatus:
        """Get current workflow status."""
        return self._state.status

    def register_handler(self, status: WorkflowStatus, handler: PhaseHandler) -> None:
        """Register a handler for a specific workflow status.

        Args:
            status: Workflow status to handle
            handler: Callable that takes (WorkflowEngine, WorkflowState) and returns bool
        """
        if status not in self._handlers:
            self._handlers[status] = []
        self._handlers[status].append(handler)

    def _execute_handlers(self, status: WorkflowStatus) -> bool:
        """Execute all handlers for a status.

        Returns True if all handlers succeed, False otherwise.
        """
        handlers = self._handlers.get(status, [])
        for handler in handlers:
            try:
                result = handler(self, self._state)
                if not result:
                    return False
            except Exception as e:
                print(f"Handler error for {status.value}: {e}")
                self._state.error = str(e)
                return False
        return True

    def transition_to(self, new_status: WorkflowStatus) -> bool:
        """Transition to a new status.

        Args:
            new_status: Target status

        Returns:
            True if transition successful, False otherwise
        """
        if not self._state.can_transition_to(new_status):
            print(
                f"Invalid transition: {self._state.status.value} -> {new_status.value}"
            )
            return False

        old_status = self._state.status
        self._state.status = new_status
        self._state.updated_at = datetime.utcnow().isoformat()

        # Execute handlers for the new status
        if not self._execute_handlers(new_status):
            # Handler failed, revert
            self._state.status = old_status
            return False

        # Save state
        self._persistence.save(self._state)
        return True

    def start(self) -> bool:
        """Start the workflow (IDLE -> PARSING)."""
        return self.transition_to(WorkflowStatus.PARSING)

    def parse(self) -> bool:
        """Parse phase (PARSING -> VALIDATING)."""
        return self.transition_to(WorkflowStatus.VALIDATING)

    def validate(self) -> bool:
        """Validate phase (VALIDATING -> PLANNING)."""
        return self.transition_to(WorkflowStatus.PLANNING)

    def plan(self) -> bool:
        """Plan phase (PLANNING -> EXECUTING)."""
        return self.transition_to(WorkflowStatus.EXECUTING)

    def execute(self) -> bool:
        """Execute phase (EXECUTING -> VERIFYING)."""
        return self.transition_to(WorkflowStatus.VERIFYING)

    def verify(self) -> bool:
        """Verify phase (VERIFYING -> COMPLETING)."""
        return self.transition_to(WorkflowStatus.COMPLETING)

    def complete(self) -> bool:
        """Complete phase (COMPLETING -> COMPLETED)."""
        return self.transition_to(WorkflowStatus.COMPLETED)

    def fail(self, error: Optional[str] = None) -> bool:
        """Mark workflow as failed.

        Args:
            error: Optional error message
        """
        if error:
            self._state.error = error
        return self.transition_to(WorkflowStatus.FAILED)

    def pause(self) -> bool:
        """Pause the workflow (only from EXECUTING)."""
        if self._state.status == WorkflowStatus.EXECUTING:
            self._state.status = WorkflowStatus.PAUSED
            self._state.updated_at = datetime.utcnow().isoformat()
            self._persistence.save(self._state)
            return True
        return False

    def resume(self) -> bool:
        """Resume a paused workflow (PAUSED -> EXECUTING)."""
        if self._state.status == WorkflowStatus.PAUSED:
            self._state.status = WorkflowStatus.EXECUTING
            self._state.updated_at = datetime.utcnow().isoformat()
            self._persistence.save(self._state)
            return True
        return False

    def cancel(self) -> bool:
        """Cancel the workflow (any -> CANCELLED -> IDLE)."""
        if self._state.status in [
            WorkflowStatus.PAUSED,
            WorkflowStatus.EXECUTING,
            WorkflowStatus.PARSING,
            WorkflowStatus.VALIDATING,
            WorkflowStatus.PLANNING,
        ]:
            self._state.status = WorkflowStatus.CANCELLED
            self._state.updated_at = datetime.utcnow().isoformat()
            self._persistence.save(self._state)
            return True
        return False

    def reset(self) -> bool:
        """Reset workflow to IDLE state."""
        self._state.status = WorkflowStatus.IDLE
        self._state.error = None
        self._state.updated_at = datetime.utcnow().isoformat()
        self._persistence.save(self._state)
        return True

    def set_progress(self, progress: float) -> None:
        """Set workflow progress (0.0 - 1.0)."""
        self._state.progress = max(0.0, min(1.0, progress))
        self._state.updated_at = datetime.utcnow().isoformat()
        self._persistence.save(self._state)

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value."""
        self._state.context[key] = value
        self._state.updated_at = datetime.utcnow().isoformat()
        self._persistence.save(self._state)

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self._state.context.get(key, default)
