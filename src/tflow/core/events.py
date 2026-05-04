"""Core event definitions for unified event handling.

This module provides foundational event classes and utilities:
- EventType: Enum of common event types
- CoreEvent: Base class for all events
- EventEmitter: Mixin for publish-subscribe pattern
- Re-exports JobEvent from broker.event for compatibility
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import uuid


class EventType(Enum):
    """Core event types for workflow and task lifecycle.

    These events provide a unified event vocabulary across
    the entire tflow system.
    """
    # Workflow lifecycle events
    WORKFLOW_CREATED = "workflow.created"
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_PARSING = "workflow.parsing"
    WORKFLOW_VALIDATING = "workflow.validating"
    WORKFLOW_PLANNING = "workflow.planning"
    WORKFLOW_EXECUTING = "workflow.executing"
    WORKFLOW_VERIFYING = "workflow.verifying"
    WORKFLOW_COMPLETING = "workflow.completing"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_CANCELLED = "workflow.cancelled"

    # Task lifecycle events
    TASK_CREATED = "task.created"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_CANCELLED = "task.cancelled"
    TASK_RETRY = "task.retry"

    # Session events
    SESSION_CREATED = "session.created"
    SESSION_STARTED = "session.started"
    SESSION_COMPLETED = "session.completed"
    SESSION_FAILED = "session.failed"

    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"

    # Generic events
    UNKNOWN = "unknown"


@dataclass
class CoreEvent:
    """Base class for all core events.

    Provides common attributes and serialization methods
    for all events in the tflow system.

    Attributes:
        event_id: Unique event identifier
        event_type: Type of the event (EventType enum value)
        timestamp: ISO format timestamp when event occurred
        payload: Additional event data
    """

    event_id: str
    event_type: EventType
    timestamp: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        event_type: EventType,
        event_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ):
        """Initialize core event.

        Args:
            event_type: Type of the event
            event_id: Unique event ID. Auto-generated if not provided.
            timestamp: Event timestamp. Current time if not provided.
            payload: Additional event data.
        """
        self.event_id = event_id or str(uuid.uuid4())
        self.event_type = event_type
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.payload = payload or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization.

        Returns:
            Dictionary representation of the event
        """
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            "timestamp": self.timestamp,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CoreEvent":
        """Create event from dictionary.

        Args:
            data: Dictionary representation of event

        Returns:
            New CoreEvent instance
        """
        event_type = data["event_type"]
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                event_type = EventType.UNKNOWN

        return cls(
            event_id=data.get("event_id"),
            event_type=event_type,
            timestamp=data.get("timestamp"),
            payload=data.get("payload", {}),
        )


class EventEmitter:
    """Mixin class for publish-subscribe event handling.

    Provides methods for emitting events and registering
    event handlers. Classes inheriting from EventEmitter
    can emit events and register listeners.
    """

    def __init__(self):
        """Initialize event emitter."""
        self._handlers: Dict[EventType, List[Callable[["CoreEvent"], None]]] = {}
        self._all_handlers: List[Callable[["CoreEvent"], None]] = []

    def on(self, event_type: EventType, handler: Callable[["CoreEvent"], None]) -> None:
        """Register a handler for a specific event type.

        Args:
            event_type: Type of event to listen for
            handler: Callable that handles the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def off(self, event_type: EventType, handler: Callable[["CoreEvent"], None]) -> None:
        """Unregister a handler for a specific event type.

        Args:
            event_type: Type of event
            handler: Handler to remove
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)

    def on_any(self, handler: Callable[["CoreEvent"], None]) -> None:
        """Register a handler for all events.

        Args:
            handler: Callable that handles any event
        """
        self._all_handlers.append(handler)

    def emit(self, event: CoreEvent) -> None:
        """Emit an event to all registered handlers.

        Args:
            event: CoreEvent to emit
        """
        # Call type-specific handlers
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Event handler error: {e}")

        # Call all-handlers
        for handler in self._all_handlers:
            try:
                handler(event)
            except Exception as e:
                print(f"Event handler error (on_any): {e}")

    def clear_handlers(self) -> None:
        """Clear all registered handlers."""
        self._handlers.clear()
        self._all_handlers.clear()


# Re-export JobEvent from broker.event for compatibility
from tflow.broker.event import JobEvent

__all__ = [
    "EventType",
    "CoreEvent",
    "EventEmitter",
    "JobEvent",
]
