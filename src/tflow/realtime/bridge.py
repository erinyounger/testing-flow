"""Realtime bridge for event streaming."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Callable, AsyncIterator
from datetime import datetime
import asyncio


class EventDelivery(Enum):
    """Event delivery method."""

    SYNC = "sync"
    ASYNC = "async"
    FIRE_AND_FORGET = "fire_and_forget"


@dataclass
class BridgeEvent:
    """Bridge event dataclass."""

    type: str
    session_id: str
    data: Dict[str, Any]
    timestamp: str = ""

    def __post_init__(self):
        """Initialize timestamp if not set."""
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class RealtimeBridgeConfig:
    """Configuration for realtime bridge."""

    name: str = "default"
    buffer_size: int = 1000
    heartbeat_interval: int = 30
    max_queue_size: int = 100
    delivery: EventDelivery = EventDelivery.ASYNC


class RealtimeBridge:
    """Realtime event bridge.

    Supports SSE (Server-Sent Events) subscription and publishing.
    """

    def __init__(self, config: Optional[RealtimeBridgeConfig] = None):
        """Initialize realtime bridge.

        Args:
            config: Bridge configuration
        """
        if config is None:
            config = RealtimeBridgeConfig()

        self.config = config
        self._subscribers: Dict[str, List[asyncio.Queue]] = {}
        self._event_buffer: List[BridgeEvent] = []
        self._running = False
        self._lock = asyncio.Lock()

    async def subscribe(self, session_id: str) -> AsyncIterator[BridgeEvent]:
        """Subscribe to events.

        Args:
            session_id: Session ID to subscribe to

        Yields:
            BridgeEvent as they occur
        """
        queue: asyncio.Queue[BridgeEvent] = asyncio.Queue(maxsize=self.config.max_queue_size)
        async with self._lock:
            if session_id not in self._subscribers:
                self._subscribers[session_id] = []
            self._subscribers[session_id].append(queue)

        try:
            while self._running:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=1.0)
                    yield event
                except asyncio.TimeoutError:
                    continue
        finally:
            async with self._lock:
                if session_id in self._subscribers and queue in self._subscribers[session_id]:
                    self._subscribers[session_id].remove(queue)

    async def publish(self, session_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event to subscribers.

        Args:
            session_id: Session ID
            event_type: Event type
            data: Event data
        """
        event = BridgeEvent(
            type=event_type,
            session_id=session_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
        )

        # Add to buffer
        self._event_buffer.append(event)
        if len(self._event_buffer) > self.config.buffer_size:
            self._event_buffer = self._event_buffer[-self.config.buffer_size:]

        # Deliver to subscribers
        async with self._lock:
            queues = self._subscribers.get(session_id, [])

        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast an event to all subscribers.

        Args:
            event_type: Event type
            data: Event data
        """
        event = BridgeEvent(
            type=event_type,
            session_id="*",
            timestamp=datetime.utcnow().isoformat(),
            data=data,
        )

        # Add to buffer
        self._event_buffer.append(event)
        if len(self._event_buffer) > self.config.buffer_size:
            self._event_buffer = self._event_buffer[-self.config.buffer_size:]

        # Broadcast to all
        async with self._lock:
            all_queues = [q for queues in self._subscribers.values() for q in queues]

        for queue in all_queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    async def attach_to_job_manager(self, job_manager: Any) -> None:
        """Attach to JobManager to receive job events.

        Args:
            job_manager: JobManager instance to attach to
        """
        async def on_job_event(event: Any) -> None:
            await self.publish(
                event.job_id,
                event.type,
                {
                    "status": event.status.value if event.status else None,
                    "payload": event.payload,
                }
            )
        await job_manager.subscribe(on_job_event)

    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[BridgeEvent]:
        """Get buffered events.

        Args:
            event_type: Filter by event type
            limit: Maximum number of events

        Returns:
            List of events
        """
        events = self._event_buffer

        if event_type:
            events = [e for e in events if e.type == event_type]

        return events[-limit:]

    def clear_events(self) -> None:
        """Clear the event buffer."""
        self._event_buffer.clear()

    async def start_heartbeat(self) -> None:
        """Start sending heartbeat events."""
        self._running = True
        while self._running:
            try:
                await asyncio.sleep(self.config.heartbeat_interval)
                if self._running:
                    await self.broadcast("heartbeat", {"timestamp": datetime.utcnow().isoformat()})
            except asyncio.CancelledError:
                break

    def stop_heartbeat(self) -> None:
        """Stop heartbeat."""
        self._running = False

    def get_subscriber_count(self) -> int:
        """Get number of subscribers."""
        return sum(len(qs) for qs in self._subscribers.values())

    def format_sse(self, event: BridgeEvent) -> str:
        """Format event as SSE (Server-Sent Events).

        Args:
            event: Event to format

        Returns:
            SSE formatted string
        """
        return f"id: {event.session_id}\nevent: {event.type}\ndata: {event.data}\n\n"
