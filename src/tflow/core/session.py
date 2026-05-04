"""Session management for workflow-level coordination.

This module provides Session class for managing workflow execution context,
and SessionManager for creating and tracking sessions.
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid


class SessionStatus:
    """Session status constants."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Session:
    """Workflow-level session for managing workflow execution context.

    A session tracks the overall workflow execution including:
    - workflow_id: Associated workflow identifier
    - session_id: Unique session identifier
    - status: Current session status
    - context: Execution context (goal, scope, plan, tasks)
    - task_ids: List of associated task identifiers
    """

    def __init__(
        self,
        workflow_id: str,
        session_id: Optional[str] = None,
        status: str = SessionStatus.PENDING,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize session.

        Args:
            workflow_id: Associated workflow ID
            session_id: Unique session ID. Auto-generated if not provided.
            status: Initial session status.
            context: Optional initial context data.
        """
        self.workflow_id = workflow_id
        self.session_id = session_id or str(uuid.uuid4())
        self.status = status
        self.context: Dict[str, Any] = context or {}
        self.task_ids: List[str] = []
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()

    def add_task(self, task_id: str) -> None:
        """Add a task ID to this session.

        Args:
            task_id: Task ID to add
        """
        if task_id not in self.task_ids:
            self.task_ids.append(task_id)
            self.updated_at = datetime.utcnow().isoformat()

    def remove_task(self, task_id: str) -> bool:
        """Remove a task ID from this session.

        Args:
            task_id: Task ID to remove

        Returns:
            True if removed, False if not found
        """
        if task_id in self.task_ids:
            self.task_ids.remove(task_id)
            self.updated_at = datetime.utcnow().isoformat()
            return True
        return False

    def set_context(self, key: str, value: Any) -> None:
        """Set a context value.

        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value
        self.updated_at = datetime.utcnow().isoformat()

    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value.

        Args:
            key: Context key
            default: Default value if not found

        Returns:
            Context value or default
        """
        return self.context.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for persistence.

        Returns:
            Dictionary representation of the session
        """
        return {
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "status": self.status,
            "context": self.context,
            "task_ids": self.task_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary.

        Args:
            data: Dictionary representation of session

        Returns:
            New Session instance
        """
        session = cls(
            workflow_id=data["workflow_id"],
            session_id=data.get("session_id"),
            status=data.get("status", SessionStatus.PENDING),
            context=data.get("context"),
        )
        session.task_ids = data.get("task_ids", [])
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        return session


class SessionManager:
    """Manager for creating and tracking workflow sessions.

    Provides centralized session management for coordinating
    multiple workflow executions.
    """

    def __init__(self):
        """Initialize session manager."""
        self._sessions: Dict[str, Session] = {}
        self._workflow_sessions: Dict[str, List[str]] = {}

    def create_session(
        self,
        workflow_id: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Session:
        """Create a new session.

        Args:
            workflow_id: Associated workflow ID
            session_id: Optional session ID
            context: Optional initial context

        Returns:
            New Session instance
        """
        session = Session(
            workflow_id=workflow_id,
            session_id=session_id,
            context=context,
        )
        self._sessions[session.session_id] = session

        if workflow_id not in self._workflow_sessions:
            self._workflow_sessions[workflow_id] = []
        self._workflow_sessions[workflow_id].append(session.session_id)

        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID.

        Args:
            session_id: Session ID to find

        Returns:
            Session if found, None otherwise
        """
        return self._sessions.get(session_id)

    def get_workflow_sessions(self, workflow_id: str) -> List[Session]:
        """Get all sessions for a workflow.

        Args:
            workflow_id: Workflow ID to find sessions for

        Returns:
            List of sessions for the workflow
        """
        session_ids = self._workflow_sessions.get(workflow_id, [])
        return [self._sessions[sid] for sid in session_ids if sid in self._sessions]

    def remove_session(self, session_id: str) -> bool:
        """Remove a session.

        Args:
            session_id: Session ID to remove

        Returns:
            True if removed, False if not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        workflow_id = session.workflow_id
        del self._sessions[session_id]

        if workflow_id in self._workflow_sessions:
            self._workflow_sessions[workflow_id].remove(session_id)
            if not self._workflow_sessions[workflow_id]:
                del self._workflow_sessions[workflow_id]

        return True

    def list_sessions(self) -> List[Session]:
        """List all active sessions.

        Returns:
            List of all sessions
        """
        return list(self._sessions.values())

    def clear(self) -> None:
        """Clear all sessions."""
        self._sessions.clear()
        self._workflow_sessions.clear()
