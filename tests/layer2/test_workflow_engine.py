import pytest
from pathlib import Path
from tflow.engine.workflow_engine import WorkflowEngine


class TestWorkflowEngine:
    """WorkflowEngine TDD tests"""

    def test_load_reads_workflow_template(self, tmp_path):
        """RED: Load workflow template"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text("## {{task}}\nStep: prepare\n")

        engine = WorkflowEngine(workflow_dir=str(tmp_path))
        workflow = engine.load("quick")

        assert "task" in workflow
        assert "Step: prepare" in workflow

    def test_run_substitutes_variables(self, tmp_path):
        """GREEN: Variable substitution"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text("Task: {{task}}\nStatus: {{status}}")

        engine = WorkflowEngine(workflow_dir=str(tmp_path))
        result = engine.run({
            "task": "实现登录",
            "status": "pending"
        })

        assert "Task: 实现登录" in result["prepared"]
        assert "Status: pending" in result["prepared"]

    def test_run_respects_conditional_branch(self, tmp_path):
        """GREEN: Conditional branch"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text(
            "{{#if discuss}}\n"
            "讨论阶段\n"
            "{{/if}}\n"
            "执行阶段"
        )

        engine = WorkflowEngine(workflow_dir=str(tmp_path))

        # discuss=True
        result = engine.run({"discuss": True})
        assert "讨论阶段" in result["steps"]
        assert "执行阶段" in result["steps"]

        # discuss=False
        result = engine.run({"discuss": False})
        assert "讨论阶段" not in result["steps"]
        assert "执行阶段" in result["steps"]

    def test_run_skips_completed_steps_on_resume(self, tmp_path):
        """GREEN: Skip completed steps on resume"""
        workflow_file = tmp_path / "quick.md"
        workflow_file.write_text("prepare\nplan\nexecute")

        engine = WorkflowEngine(workflow_dir=str(tmp_path))

        # Simulate completed prepare
        result = engine.run({"discuss": False}, skip_steps=["prepare"])

        assert "prepare" not in result["steps"]
        assert "plan" in result["steps"]
        assert "execute" in result["steps"]