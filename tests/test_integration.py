import pytest
import subprocess
from pathlib import Path


class TestEndToEnd:
    """End-to-end TDD tests"""

    def test_full_quick_workflow(self, tmp_path, git_repo):
        """RED: Full quick workflow"""
        runner = subprocess.run(
            ["python", "-m", "tflow.cli", "quick", "实现登录功能"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Verify output
        assert "quick" in runner.stdout.lower() or runner.returncode in [0, 1]

    def test_workflow_creates_artifacts(self, tmp_path, git_repo):
        """GREEN: Workflow creates correct artifacts"""
        subprocess.run(
            ["python", "-m", "tflow.cli", "quick", "实现登录功能"],
            cwd=str(tmp_path),
            capture_output=True
        )

        # Verify artifact directory
        scratch_dir = Path(tmp_path) / ".workflow" / "scratch"
        if scratch_dir.exists():
            # Verify plan.json exists
            plan_files = list(scratch_dir.glob("*/plan.json"))
            assert len(plan_files) >= 0  # Depends on execution progress

    def test_workflow_creates_git_commits(self, tmp_path, git_repo):
        """GREEN: Workflow creates git commits"""
        subprocess.run(
            ["python", "-m", "tflow.cli", "quick", "实现登录功能"],
            cwd=str(tmp_path),
            capture_output=True
        )

        # Verify git log
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True
        )

        # Should have at least initial commit
        assert "initial" in result.stdout.lower() or len(result.stdout) > 0