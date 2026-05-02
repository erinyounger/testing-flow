import subprocess
from pathlib import Path
from typing import List


class GitCommit:
    """Git commit operations"""

    def commit(self, files: List[str], message: str) -> str:
        """Create a git commit with given files and message"""
        try:
            # Add files
            subprocess.run(["git", "add"] + files, check=True, capture_output=True)

            # Create commit
            result = subprocess.run(
                ["git", "commit", "-m", message],
                check=True,
                capture_output=True,
                text=True
            )

            # Get commit hash
            hash_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True
            )
            return hash_result.stdout.strip()

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git commit failed: {e.stderr.decode() if e.stderr else str(e)}")

    def commit_task(self, task_id: str, description: str, files: List[str]) -> str:
        """Create a task commit with proper message format"""
        message = f"{task_id}: {description}"
        return self.commit(files, message)