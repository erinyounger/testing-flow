import pytest
import subprocess
from pathlib import Path
from tflow.state.git_commit import GitCommit


class TestGitCommit:
    """GitCommit TDD tests"""

    def test_commit_creates_git_commit(self, tmp_path, git_repo):
        """RED: git commit should create commit"""
        gc = GitCommit()

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello")

        commit_hash = gc.commit(["test.txt"], "test commit")

        assert commit_hash is not None
        assert len(commit_hash) == 40  # git hash length

    def test_commit_raises_on_failure(self, tmp_path, git_repo):
        """GREEN: Commit failure should raise exception"""
        gc = GitCommit()

        with pytest.raises(RuntimeError, match="Git commit failed"):
            gc.commit(["nonexistent.txt"], "test")

    def test_commit_task_uses_proper_message(self, tmp_path, git_repo):
        """GREEN: task commit uses correct format"""
        gc = GitCommit()

        test_file = tmp_path / "task.py"
        test_file.write_text("# task")

        commit_hash = gc.commit_task("TASK-001", "实现登录功能", ["task.py"])

        result = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            capture_output=True,
            text=True
        )
        assert "TASK-001" in result.stdout
        assert "实现登录功能" in result.stdout