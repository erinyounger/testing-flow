import pytest
import json
import os
from pathlib import Path
from tflow.state.state_manager import StateManager, ProjectState, WORKFLOW_DIR


class TestStateManager:
    """StateManager TDD tests"""

    def test_load_returns_empty_state_when_file_not_exists(self, tmp_path):
        """RED: When state.json doesn't exist, return empty state"""
        os.chdir(tmp_path)
        sm = StateManager()
        state = sm.load()

        assert state.version == "1.0"
        assert state.status == "idle"
        assert state.artifacts == []

    def test_load_returns_existing_state(self, tmp_path):
        """GREEN: When state.json exists, return existing state"""
        os.chdir(tmp_path)
        os.makedirs(WORKFLOW_DIR, exist_ok=True)
        state_file = Path(WORKFLOW_DIR) / "state.json"
        state_file.write_text(json.dumps({
            "version": "1.0",
            "status": "executing",
            "artifacts": [{"id": "test"}],
            "accumulated_context": {"key_decisions": [], "blockers": [], "deferred": []}
        }))

        sm = StateManager()
        state = sm.load()

        assert state.status == "executing"
        assert len(state.artifacts) == 1

    def test_save_writes_state_to_file(self, tmp_path):
        """GREEN: save method writes to file correctly"""
        os.chdir(tmp_path)
        sm = StateManager()
        state = ProjectState(status="planning")
        sm.save(state)

        state_file = Path(WORKFLOW_DIR) / "state.json"
        assert state_file.exists()

        with open(state_file) as f:
            data = json.load(f)
        assert data["status"] == "planning"

    def test_is_task_done_returns_false_when_not_exists(self, tmp_path):
        """RED: Returns False when task doesn't exist"""
        os.chdir(tmp_path)
        sm = StateManager()
        assert sm.is_task_done("TASK-999") == False

    def test_is_task_done_returns_true_when_completed(self, tmp_path):
        """GREEN: Returns True when task is completed"""
        os.chdir(tmp_path)
        sm = StateManager()
        sm.register_artifact({
            "task_id": "TASK-001",
            "status": "completed"
        })
        assert sm.is_task_done("TASK-001") == True

    def test_register_artifact_adds_to_artifacts_list(self, tmp_path):
        """GREEN: Register artifact"""
        os.chdir(tmp_path)
        sm = StateManager()
        sm.register_artifact({"task_id": "TASK-001", "status": "pending"})

        state = sm.load()
        assert len(state.artifacts) == 1
        assert state.artifacts[0]["task_id"] == "TASK-001"

    def test_add_key_decision_appends_to_context(self, tmp_path):
        """GREEN: Add key decision"""
        os.chdir(tmp_path)
        sm = StateManager()
        sm.add_key_decision("使用增量开发策略")

        state = sm.load()
        assert len(state.accumulated_context["key_decisions"]) == 1
        assert "使用增量开发策略" in state.accumulated_context["key_decisions"][0]["text"]