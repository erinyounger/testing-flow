"""Tests for delegate broker."""

import pytest

from tflow.delegate import DelegateBroker, DelegateStatus, DelegateTask, DelegateSession


class TestDelegateTask:
    """Test DelegateTask class."""

    def test_create(self):
        """Test task creation."""
        task = DelegateTask(
            task_id="test-task-1",
            name="Test Task",
            description="A test task",
        )

        assert task.task_id == "test-task-1"
        assert task.name == "Test Task"
        assert task.status == DelegateStatus.PENDING
        assert task.created_at is not None

    def test_start(self):
        """Test starting a task."""
        task = DelegateTask(
            task_id="test-task-2",
            name="Test Task",
            description="A test task",
        )

        assert task.start()
        assert task.status == DelegateStatus.IN_PROGRESS
        assert task.started_at is not None

        # Cannot start again
        assert not task.start()

    def test_complete(self):
        """Test completing a task."""
        task = DelegateTask(
            task_id="test-task-3",
            name="Test Task",
            description="A test task",
        )

        task.start()
        output = {"result": "success"}
        assert task.complete(output)

        assert task.status == DelegateStatus.COMPLETED
        assert task.output_data == output
        assert task.completed_at is not None

    def test_fail(self):
        """Test failing a task."""
        task = DelegateTask(
            task_id="test-task-4",
            name="Test Task",
            description="A test task",
        )

        task.start()
        assert task.fail("Test error")

        assert task.status == DelegateStatus.FAILED
        assert task.error == "Test error"

    def test_wait_input(self):
        """Test waiting for input."""
        task = DelegateTask(
            task_id="test-task-5",
            name="Test Task",
            description="A test task",
        )

        task.start()
        assert task.wait_input()
        assert task.status == DelegateStatus.WAITING_INPUT

        # Cannot wait again
        assert not task.wait_input()

    def test_cancel(self):
        """Test cancelling a task."""
        task = DelegateTask(
            task_id="test-task-6",
            name="Test Task",
            description="A test task",
        )

        assert task.cancel()
        assert task.status == DelegateStatus.CANCELLED

    def test_retry(self):
        """Test retrying a task."""
        task = DelegateTask(
            task_id="test-task-7",
            name="Test Task",
            description="A test task",
            max_retries=2,
        )

        task.start()
        task.fail("Error")

        # Can retry
        assert task.retry()
        assert task.status == DelegateStatus.PENDING
        assert task.retry_count == 1

        # Can retry again
        assert task.retry()
        assert task.retry_count == 2

        # Cannot retry beyond max
        assert not task.retry()

    def test_to_dict_from_dict(self):
        """Test serialization."""
        task = DelegateTask(
            task_id="test-task-8",
            name="Test Task",
            description="A test task",
            input_data={"key": "value"},
            max_retries=5,
        )

        data = task.to_dict()
        assert data["task_id"] == "test-task-8"
        assert data["input_data"]["key"] == "value"

        loaded = DelegateTask.from_dict(data)
        assert loaded.task_id == "test-task-8"
        assert loaded.input_data["key"] == "value"


class TestDelegateBroker:
    """Test DelegateBroker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.broker = DelegateBroker()

    def test_create_task(self):
        """Test creating a task."""
        task = self.broker.create_task(
            name="New Task",
            description="A new task",
            input_data={"foo": "bar"},
        )

        assert task.name == "New Task"
        assert task.input_data["foo"] == "bar"
        assert self.broker.get_task(task.task_id) is not None

    def test_get_task(self):
        """Test getting a task."""
        task = self.broker.create_task(
            name="Test Task",
            description="A test task",
        )

        found = self.broker.get_task(task.task_id)
        assert found is not None
        assert found.task_id == task.task_id

        # Non-existent
        assert self.broker.get_task("nonexistent") is None

    def test_update_task(self):
        """Test updating a task."""
        task = self.broker.create_task(
            name="Test Task",
            description="A test task",
        )

        task.status = DelegateStatus.IN_PROGRESS
        assert self.broker.update_task(task)

        loaded = self.broker.get_task(task.task_id)
        assert loaded.status == DelegateStatus.IN_PROGRESS

    def test_delete_task(self):
        """Test deleting a task."""
        task = self.broker.create_task(
            name="Test Task",
            description="A test task",
        )

        assert self.broker.delete_task(task.task_id)
        assert self.broker.get_task(task.task_id) is None

    def test_list_tasks(self):
        """Test listing tasks."""
        # Create tasks with different statuses
        self.broker.create_task(name="Task 1", description="Task 1")
        t2 = self.broker.create_task(name="Task 2", description="Task 2")
        t3 = self.broker.create_task(name="Task 3", description="Task 3")

        t2.status = DelegateStatus.IN_PROGRESS
        self.broker.update_task(t2)

        t3.status = DelegateStatus.COMPLETED
        self.broker.update_task(t3)

        # List all
        all_tasks = self.broker.list_tasks()
        assert len(all_tasks) == 3

        # Filter by status
        pending = self.broker.list_tasks(status=DelegateStatus.PENDING)
        assert len(pending) == 1

        in_progress = self.broker.list_tasks(status=DelegateStatus.IN_PROGRESS)
        assert len(in_progress) == 1

        completed = self.broker.list_tasks(status=DelegateStatus.COMPLETED)
        assert len(completed) == 1

    def test_get_pending_tasks(self):
        """Test getting pending tasks."""
        self.broker.create_task(name="Task 1", description="Task 1")
        t2 = self.broker.create_task(name="Task 2", description="Task 2")
        t2.status = DelegateStatus.IN_PROGRESS
        self.broker.update_task(t2)

        pending = self.broker.get_pending_tasks()
        assert len(pending) == 1
        assert pending[0].name == "Task 1"

    def test_get_active_tasks(self):
        """Test getting active tasks."""
        t1 = self.broker.create_task(name="Task 1", description="Task 1")
        t1.status = DelegateStatus.IN_PROGRESS
        self.broker.update_task(t1)

        t2 = self.broker.create_task(name="Task 2", description="Task 2")

        active = self.broker.get_active_tasks()
        assert len(active) == 1
        assert active[0].name == "Task 1"

    def test_assign_task(self):
        """Test assigning a task to an agent."""
        task = self.broker.create_task(
            name="Test Task",
            description="A test task",
        )

        assert self.broker.assign_task(task.task_id, "agent-1")

        loaded = self.broker.get_task(task.task_id)
        assert loaded.assigned_agent == "agent-1"


class TestDelegateSession:
    """Test DelegateSession class."""

    def test_create(self):
        """Test session creation."""
        session = DelegateSession(
            session_id="test-session-1",
            name="Test Session",
        )

        assert session.session_id == "test-session-1"
        assert session.name == "Test Session"
        assert session.created_at is not None

    def test_add_remove_task(self):
        """Test adding and removing tasks."""
        session = DelegateSession(session_id="test-session-2")

        session.add_task("task-1")
        session.add_task("task-2")
        session.add_task("task-1")  # Duplicate - should not add

        assert len(session.task_ids) == 2

        assert session.remove_task("task-1")
        assert len(session.task_ids) == 1
        assert not session.remove_task("nonexistent")

    def test_context(self):
        """Test context management."""
        session = DelegateSession(session_id="test-session-3")

        session.set_context("key1", "value1")
        session.set_context("key2", {"nested": True})

        assert session.get_context("key1") == "value1"
        assert session.get_context("key2") == {"nested": True}
        assert session.get_context("nonexistent", "default") == "default"

    def test_metadata(self):
        """Test metadata management."""
        session = DelegateSession(session_id="test-session-4")

        session.set_metadata("tag", "important")
        session.set_metadata("count", 42)

        assert session.get_metadata("tag") == "important"
        assert session.get_metadata("count") == 42

    def test_to_dict_from_dict(self):
        """Test serialization."""
        session = DelegateSession(
            session_id="test-session-5",
            name="Test Session",
            context={"key": "value"},
        )
        session.add_task("task-1")
        session.set_metadata("meta", "data")

        data = session.to_dict()
        assert data["session_id"] == "test-session-5"
        assert data["context"]["key"] == "value"
        assert "task-1" in data["task_ids"]

        loaded = DelegateSession.from_dict(data)
        assert loaded.session_id == "test-session-5"
        assert loaded.get_context("key") == "value"
        assert "task-1" in loaded.task_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
