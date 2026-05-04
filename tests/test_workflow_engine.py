"""Tests for workflow engine."""

import pytest
import tempfile
import shutil
from pathlib import Path

from tflow.workflow import WorkflowEngine, WorkflowStatus, WorkflowType, WorkflowPersistence


class TestWorkflowPersistence:
    """Test WorkflowPersistence class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.persistence = WorkflowPersistence(base_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_load(self):
        """Test saving and loading workflow state."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-workflow-1",
            workflow_type=WorkflowType.STANDARD,
            persistence=self.persistence,
        )

        # Save state
        assert self.persistence.save(engine.state)

        # Load state
        loaded = self.persistence.load("test-workflow-1")
        assert loaded is not None
        assert loaded.workflow_id == "test-workflow-1"
        assert loaded.status == WorkflowStatus.IDLE

    def test_exists(self):
        """Test exists check."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-workflow-2",
            persistence=self.persistence,
        )
        self.persistence.save(engine.state)

        assert self.persistence.exists("test-workflow-2")
        assert not self.persistence.exists("nonexistent")

    def test_delete(self):
        """Test deleting workflow state."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-workflow-3",
            persistence=self.persistence,
        )
        self.persistence.save(engine.state)

        assert self.persistence.delete("test-workflow-3")
        assert not self.persistence.exists("test-workflow-3")

    def test_list_workflows(self):
        """Test listing workflows."""
        for i in range(3):
            engine = WorkflowEngine(
                job_manager=None,
                agent_executor=None,
                workflow_id=f"test-workflow-{i}",
                persistence=self.persistence,
            )
            self.persistence.save(engine.state)

        workflows = self.persistence.list_workflows()
        assert len(workflows) == 3


class TestWorkflowState:
    """Test WorkflowState class."""

    def test_can_transition_to(self):
        """Test valid state transitions."""
        from tflow.workflow.state import WorkflowState

        state = WorkflowState(
            workflow_type=WorkflowType.STANDARD,
            session_id="test-session",
            status=WorkflowStatus.IDLE,
            current_phase="idle",
            workflow_id="test",
        )

        assert state.can_transition_to(WorkflowStatus.PARSING)
        assert not state.can_transition_to(WorkflowStatus.COMPLETED)

    def test_transition_to(self):
        """Test state transition."""
        from tflow.workflow.state import WorkflowState

        state = WorkflowState(
            workflow_type=WorkflowType.STANDARD,
            session_id="test-session",
            status=WorkflowStatus.IDLE,
            current_phase="idle",
            workflow_id="test",
        )

        assert state.transition_to(WorkflowStatus.PARSING)
        assert state.status == WorkflowStatus.PARSING

        # Invalid transition
        assert not state.transition_to(WorkflowStatus.COMPLETED)

    def test_to_dict_from_dict(self):
        """Test serialization."""
        from tflow.workflow.state import WorkflowState

        state = WorkflowState(
            workflow_type=WorkflowType.STANDARD,
            session_id="test-session",
            status=WorkflowStatus.EXECUTING,
            current_phase="executing",
            workflow_id="test",
        )
        state.set_context("key", "value")

        data = state.to_dict()
        assert data["workflow_id"] == "test"
        assert data["status"] == "executing"
        assert data["context"]["key"] == "value"

        loaded = WorkflowState.from_dict(data)
        assert loaded.workflow_id == "test"
        assert loaded.status == WorkflowStatus.EXECUTING
        assert loaded.get_context("key") == "value"


class TestWorkflowEngine:
    """Test WorkflowEngine class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.persistence = WorkflowPersistence(base_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """Test engine initialization."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-1",
            workflow_type=WorkflowType.STANDARD,
            persistence=self.persistence,
        )

        assert engine.workflow_id == "test-engine-1"
        assert engine.workflow_type == WorkflowType.STANDARD

    def test_start_transition(self):
        """Test starting workflow."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-2",
            persistence=self.persistence,
        )

        assert engine.status == WorkflowStatus.IDLE
        assert engine.start()
        assert engine.status == WorkflowStatus.PARSING

    def test_full_lifecycle(self):
        """Test full workflow lifecycle."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-3",
            persistence=self.persistence,
        )

        # Start
        assert engine.start()
        assert engine.status == WorkflowStatus.PARSING

        # Parse
        assert engine.parse()
        assert engine.status == WorkflowStatus.VALIDATING

        # Validate
        assert engine.validate()
        assert engine.status == WorkflowStatus.PLANNING

        # Plan
        assert engine.plan()
        assert engine.status == WorkflowStatus.EXECUTING

        # Execute
        assert engine.execute()
        assert engine.status == WorkflowStatus.VERIFYING

        # Verify
        assert engine.verify()
        assert engine.status == WorkflowStatus.COMPLETING

        # Complete
        assert engine.complete()
        assert engine.status == WorkflowStatus.COMPLETED

    def test_invalid_transition(self):
        """Test invalid state transition."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-4",
            persistence=self.persistence,
        )

        # Cannot jump to COMPLETED from IDLE
        assert not engine.complete()

    def test_pause_resume(self):
        """Test pause and resume."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-5",
            persistence=self.persistence,
        )

        engine.start()
        engine.parse()
        engine.validate()
        engine.plan()
        # After plan(), status is EXECUTING
        assert engine.status == WorkflowStatus.EXECUTING

        # Pause from EXECUTING
        assert engine.pause()
        assert engine.status == WorkflowStatus.PAUSED

        # Resume
        assert engine.resume()
        assert engine.status == WorkflowStatus.EXECUTING

    def test_cancel(self):
        """Test cancel workflow."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-6",
            persistence=self.persistence,
        )

        engine.start()
        # After start(), status is PARSING
        assert engine.status == WorkflowStatus.PARSING

        # Cancel from PARSING sets to FAILED
        assert engine.cancel()
        assert engine.status == WorkflowStatus.FAILED

    def test_fail(self):
        """Test fail workflow."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-7",
            persistence=self.persistence,
        )

        engine.start()
        assert engine.fail("Test error")
        assert engine.status == WorkflowStatus.FAILED
        assert engine.state.error == "Test error"

    def test_context(self):
        """Test context management."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-9",
            persistence=self.persistence,
        )

        engine.set_context("key1", "value1")
        engine.set_context("key2", {"nested": "value"})

        assert engine.get_context("key1") == "value1"
        assert engine.get_context("key2") == {"nested": "value"}
        assert engine.get_context("nonexistent", "default") == "default"

    def test_handler_registration(self):
        """Test phase handler registration."""
        engine = WorkflowEngine(
            job_manager=None,
            agent_executor=None,
            workflow_id="test-engine-10",
            persistence=self.persistence,
        )

        handler_called = []

        def handler(eng, state):
            handler_called.append(True)
            return True

        engine.register_handler(WorkflowStatus.PARSING, handler)
        engine.start()

        assert len(handler_called) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
