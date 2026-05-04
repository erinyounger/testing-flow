"""Tests for storage modules."""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from tflow.storage import ExecutionStore, ExecutionRecord, SQLiteStore, SQLiteStoreConfig


class TestExecutionRecord:
    """Test ExecutionRecord class."""

    def test_create(self):
        """Test creating execution record."""
        record = ExecutionRecord(
            execution_id="exec-1",
            workflow_id="wf-1",
            task_id="task-1",
            agent_id="agent-1",
            status="completed",
            input_data={"key": "value"},
        )

        assert record.execution_id == "exec-1"
        assert record.workflow_id == "wf-1"
        assert record.started_at is not None

    def test_to_dict_from_dict(self):
        """Test serialization."""
        record = ExecutionRecord(
            execution_id="exec-2",
            workflow_id="wf-1",
            task_id="task-2",
            agent_id="agent-1",
            status="failed",
            input_data={"foo": "bar"},
        )

        data = record.to_dict()
        assert data["execution_id"] == "exec-2"

        loaded = ExecutionRecord.from_dict(data)
        assert loaded.execution_id == "exec-2"


class TestExecutionStore:
    """Test ExecutionStore class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = ExecutionStore(base_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_append(self):
        """Test appending records."""
        record = ExecutionRecord(
            execution_id="exec-1",
            workflow_id="wf-1",
            task_id="task-1",
            agent_id="agent-1",
            status="completed",
            input_data={},
        )

        result = await self.store.append(record)
        assert result is True

    @pytest.mark.asyncio
    async def test_get(self):
        """Test getting records."""
        record = ExecutionRecord(
            execution_id="exec-1",
            workflow_id="wf-1",
            task_id="task-1",
            agent_id="agent-1",
            status="completed",
            input_data={},
        )
        await self.store.append(record)

        records = await self.store.get("wf-1")
        assert len(records) == 1
        assert records[0].execution_id == "exec-1"

    @pytest.mark.asyncio
    async def test_get_latest(self):
        """Test getting latest record."""
        for i in range(3):
            record = ExecutionRecord(
                execution_id=f"exec-{i}",
                workflow_id="wf-1",
                task_id=f"task-{i}",
                agent_id="agent-1",
                status="completed",
                input_data={},
            )
            await self.store.append(record)

        latest = await self.store.get_latest("wf-1")
        assert latest.execution_id == "exec-2"

    @pytest.mark.asyncio
    async def test_get_by_task(self):
        """Test getting records by task."""
        record = ExecutionRecord(
            execution_id="exec-1",
            workflow_id="wf-1",
            task_id="task-x",
            agent_id="agent-1",
            status="completed",
            input_data={},
        )
        await self.store.append(record)

        records = await self.store.get_by_task("wf-1", "task-x")
        assert len(records) == 1

    @pytest.mark.asyncio
    async def test_list_workflows(self):
        """Test listing workflows."""
        for wf_id in ["wf-1", "wf-2", "wf-3"]:
            record = ExecutionRecord(
                execution_id=f"exec-{wf_id}",
                workflow_id=wf_id,
                task_id="task-1",
                agent_id="agent-1",
                status="completed",
                input_data={},
            )
            await self.store.append(record)

        workflows = await self.store.list_workflows()
        assert len(workflows) == 3


class TestSQLiteStore:
    """Test SQLiteStore class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.temp_db.close()
        self.store = SQLiteStore(config=SQLiteStoreConfig(db_path=self.temp_db.name))

    def teardown_method(self):
        """Clean up test fixtures."""
        try:
            self.store = None
            Path(self.temp_db.name).unlink()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_save_session(self):
        """Test saving session."""
        session_data = {
            "session_id": "session-1",
            "name": "Test Session",
            "context": {"key": "value"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "metadata": {},
        }

        result = await self.store.save_session(session_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_session(self):
        """Test getting session."""
        session_data = {
            "session_id": "session-2",
            "name": "Test Session 2",
            "context": {"foo": "bar"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "metadata": {},
        }
        await self.store.save_session(session_data)

        retrieved = await self.store.get_session("session-2")
        assert retrieved is not None
        assert retrieved["session_id"] == "session-2"

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        """Test listing sessions."""
        for i in range(3):
            session_data = {
                "session_id": f"session-{i}",
                "name": f"Session {i}",
                "context": {},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "metadata": {},
            }
            await self.store.save_session(session_data)

        sessions = await self.store.list_sessions()
        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_save_task(self):
        """Test saving task."""
        task_data = {
            "task_id": "task-1",
            "session_id": "session-1",
            "name": "Test Task",
            "description": "A test task",
            "status": "pending",
            "input_data": {"key": "value"},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        result = await self.store.save_task(task_data)
        assert result is True

    @pytest.mark.asyncio
    async def test_get_task(self):
        """Test getting task."""
        task_data = {
            "task_id": "task-2",
            "session_id": "session-1",
            "name": "Test Task 2",
            "description": "Another test task",
            "status": "in_progress",
            "input_data": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        await self.store.save_task(task_data)

        retrieved = await self.store.get_task("task-2")
        assert retrieved is not None
        assert retrieved["task_id"] == "task-2"

    @pytest.mark.asyncio
    async def test_get_tasks(self):
        """Test getting tasks."""
        for i in range(3):
            task_data = {
                "task_id": f"task-{i}",
                "session_id": "session-1",
                "name": f"Task {i}",
                "status": "pending",
                "input_data": {},
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
            }
            await self.store.save_task(task_data)

        tasks = await self.store.get_tasks("session-1")
        assert len(tasks) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
