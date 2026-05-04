"""Delegate session management."""

from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid


class DelegateSession:
    """Session for managing delegate interactions.

    A session groups related delegate tasks and maintains
    context across multiple interactions.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize delegate session.

        Args:
            session_id: Unique session ID. Auto-generated if not provided.
            name: Session name.
            context: Optional initial context data.
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.name = name or f"session-{self.session_id[:8]}"
        self.context: Dict[str, Any] = context or {}
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()
        self.task_ids: List[str] = []
        self.metadata: Dict[str, Any] = {}

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

    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value
        self.updated_at = datetime.utcnow().isoformat()

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata.

        Args:
            key: Metadata key
            default: Default value if not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "name": self.name,
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "task_ids": self.task_ids,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DelegateSession":
        """Create session from dictionary."""
        session = cls(
            session_id=data["session_id"],
            name=data.get("name"),
            context=data.get("context"),
        )
        session.created_at = data.get("created_at", session.created_at)
        session.updated_at = data.get("updated_at", session.updated_at)
        session.task_ids = data.get("task_ids", [])
        session.metadata = data.get("metadata", {})
        return session
