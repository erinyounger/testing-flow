"""Tests for realtime bridge module."""

import pytest
import asyncio
from tflow.realtime.bridge import (
    RealtimeBridge,
    BridgeEvent,
    EventDelivery,
    RealtimeBridgeConfig,
)


class TestRealtimeBridge:
    """Test RealtimeBridge functionality."""

    def test_bridge_creation(self):
        """Test bridge can be created."""
        bridge = RealtimeBridge()
        assert bridge is not None

    def test_bridge_with_config(self):
        """Test bridge with custom config."""
        config = RealtimeBridgeConfig(
            name="test",
            buffer_size=500,
            heartbeat_interval=60,
            delivery=EventDelivery.ASYNC,
        )
        bridge = RealtimeBridge(config)
        assert bridge.config.heartbeat_interval == 60
        assert bridge.config.buffer_size == 500

    def test_event_delivery_enum(self):
        """Test EventDelivery enum values."""
        assert EventDelivery.SYNC.value == "sync"
        assert EventDelivery.ASYNC.value == "async"
        assert EventDelivery.FIRE_AND_FORGET.value == "fire_and_forget"

    def test_bridge_event_creation(self):
        """Test BridgeEvent can be created."""
        event = BridgeEvent(
            type="test_event",
            session_id="test-session",
            data={"key": "value"},
        )
        assert event.type == "test_event"
        assert event.session_id == "test-session"
        assert event.data["key"] == "value"

    @pytest.mark.asyncio
    async def test_bridge_subscribe(self):
        """Test subscribing to events."""
        bridge = RealtimeBridge()
        bridge._running = True
        received = []

        async def collector():
            async for event in bridge.subscribe("test-session"):
                received.append(event)

        task = asyncio.create_task(collector())

        # Give subscription time to set up
        await asyncio.sleep(0.05)

        # Publish an event
        await bridge.publish("test-session", "test", {"msg": "hello"})

        # Give time for event to be delivered
        await asyncio.sleep(0.1)

        assert len(received) == 1
        assert received[0].type == "test"

        bridge._running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_bridge_publish(self):
        """Test publishing events."""
        bridge = RealtimeBridge()
        bridge._running = True
        received = []

        async def collector():
            async for event in bridge.subscribe("test-session"):
                received.append(event)

        task = asyncio.create_task(collector())
        await asyncio.sleep(0.05)

        await bridge.publish("test-session", "test", {"msg": "hello"})
        await asyncio.sleep(0.1)

        assert len(received) == 1

        bridge._running = False
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
