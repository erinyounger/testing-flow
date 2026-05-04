"""Realtime bridge for event streaming."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
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

    event_id: str
    event_type: str
    data: Dict[str, Any]
    timestamp: Optional[str] = None
    source: Optional[str] = None
    delivery: EventDelivery = EventDelivery.ASYNC

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
        self._subscribers: Dict[str, Callable] = {}
        self._event_buffer: List[BridgeEvent] = []
        self._running = False

    def subscribe(
        self,
        subscriber_id: str,
        callback: Callable[[BridgeEvent], None],
    ) -> bool:
        """Subscribe to events.

        Args:
            subscriber_id: Unique subscriber ID
            callback: Callback function for events

        Returns:
            True if subscribed successfully
        """
        if subscriber_id in self._subscribers:
            return False

        self._subscribers[subscriber_id] = callback
        return True

    def unsubscribe(self, subscriber_id: str) -> bool:
        """Unsubscribe from events.

        Args:
            subscriber_id: Subscriber ID

        Returns:
            True if unsubscribed successfully
        """
        if subscriber_id in self._subscribers:
            del self._subscribers[subscriber_id]
            return True
        return False

    def publish(self, event: BridgeEvent) -> bool:
        """Publish an event to all subscribers.

        Args:
            event: Event to publish

        Returns:
            True if published successfully
        """
        # Add to buffer
        self._event_buffer.append(event)

        # Trim buffer if needed
        if len(self._event_buffer) > self.config.buffer_size:
            self._event_buffer = self._event_buffer[-self.config.buffer_size:]

        # Deliver to subscribers
        if event.delivery == EventDelivery.SYNC:
            self._deliver_sync(event)
        elif event.delivery == EventDelivery.ASYNC:
            asyncio.create_task(self._deliver_async(event))
        elif event.delivery == EventDelivery.FIRE_AND_FORGET:
            self._deliver_fire_and_forget(event)

        return True

    def _deliver_sync(self, event: BridgeEvent) -> None:
        """Deliver event synchronously."""
        for subscriber_id, callback in self._subscribers.items():
            try:
                callback(event)
            except Exception as e:
                print(f"Subscriber {subscriber_id} error: {e}")

    async def _deliver_async(self, event: BridgeEvent) -> None:
        """Deliver event asynchronously."""
        for subscriber_id, callback in self._subscribers.items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"Subscriber {subscriber_id} error: {e}")

    def _deliver_fire_and_forget(self, event: BridgeEvent) -> None:
        """Deliver event fire-and-forget style."""
        for subscriber_id, callback in self._subscribers.items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    asyncio.create_task(callback(event))
                else:
                    callback(event)
            except Exception:
                pass  # Ignore errors in fire-and-forget mode

    def broadcast(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Broadcast an event to all subscribers.

        Args:
            event_type: Event type
            data: Event data

        Returns:
            True if broadcast successfully
        """
        import uuid

        event = BridgeEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            data=data,
            delivery=self.config.delivery,
        )
        return self.publish(event)

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
            events = [e for e in events if e.event_type == event_type]

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
                    self.broadcast("heartbeat", {"timestamp": datetime.utcnow().isoformat()})
            except asyncio.CancelledError:
                break

    def stop_heartbeat(self) -> None:
        """Stop heartbeat."""
        self._running = False

    def get_subscriber_count(self) -> int:
        """Get number of subscribers."""
        return len(self._subscribers)

    def format_sse(self, event: BridgeEvent) -> str:
        """Format event as SSE (Server-Sent Events).

        Args:
            event: Event to format

        Returns:
            SSE formatted string
        """
        return f"id: {event.event_id}\nevent: {event.event_type}\ndata: {event.data}\n\n"
