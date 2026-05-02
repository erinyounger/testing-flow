import pytest
import json
from pathlib import Path
from tflow.artifacts.plan import PlanArtifact, Plan


class TestPlanArtifact:
    """PlanArtifact TDD tests"""

    def test_create_initializes_plan_file(self, tmp_path):
        """RED: create method should create plan.json"""
        pa = PlanArtifact(str(tmp_path))
        plan = pa.create("实现登录功能", {})

        plan_file = tmp_path / "plan.json"
        assert plan_file.exists()

        with open(plan_file) as f:
            data = json.load(f)
        assert data["task"] == "实现登录功能"
        assert data["id"] is not None

    def test_add_task_creates_task_file_and_updates_plan(self, tmp_path):
        """GREEN: Add task"""
        pa = PlanArtifact(str(tmp_path))
        pa.create("实现登录功能", {})

        task = {
            "id": "TASK-001",
            "title": "创建登录页面",
            "scope": ["src/login.py"],
            "status": "pending",
            "wave": 0,
            "convergence": {"criteria": []}
        }
        pa.add_task(task)

        # Check task file
        task_file = tmp_path / ".task" / "TASK-001.json"
        assert task_file.exists()

        # Check plan.json update
        with open(tmp_path / "plan.json") as f:
            plan = json.load(f)
        assert "TASK-001" in plan["task_ids"]

    def test_get_tasks_returns_sorted_tasks(self, tmp_path):
        """GREEN: Get sorted task list"""
        pa = PlanArtifact(str(tmp_path))
        pa.create("实现登录功能", {})

        pa.add_task({"id": "TASK-002", "title": "B", "scope": [], "status": "pending", "wave": 0, "convergence": {"criteria": []}})
        pa.add_task({"id": "TASK-001", "title": "A", "scope": [], "status": "pending", "wave": 0, "convergence": {"criteria": []}})

        tasks = pa.get_tasks()
        assert tasks[0]["id"] == "TASK-001"
        assert tasks[1]["id"] == "TASK-002"

    def test_mark_done_updates_task_status(self, tmp_path):
        """GREEN: Mark task done"""
        pa = PlanArtifact(str(tmp_path))
        pa.create("实现登录功能", {})
        pa.add_task({"id": "TASK-001", "title": "创建登录页面", "scope": [], "status": "pending", "wave": 0, "convergence": {"criteria": []}})

        pa.mark_done("TASK-001", "summaries/TASK-001-summary.md", "abc123")

        with open(tmp_path / ".task" / "TASK-001.json") as f:
            task = json.load(f)
        assert task["status"] == "completed"
        assert task["summary"] == "summaries/TASK-001-summary.md"
        assert task["commit"] == "abc123"