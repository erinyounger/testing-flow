"""Workflow persistence layer for saving and loading workflow states."""

import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from tflow.workflow.state import WorkflowState


class WorkflowPersistence:
    """Handles persistence of workflow states to JSON files.

    Saves workflow states to .workflow/sessions/ directory.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize persistence with base directory.

        Args:
            base_dir: Base directory for session storage. Defaults to .workflow/sessions/
        """
        if base_dir is None:
            # Use project root / .workflow/sessions/
            project_root = Path(__file__).parent.parent.parent.parent
            base_dir = project_root / ".workflow" / "sessions"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_path(self, workflow_id: str) -> Path:
        """Get the file path for a workflow session."""
        return self.base_dir / f"{workflow_id}.json"

    def save(self, state: WorkflowState) -> bool:
        """Save workflow state to file.

        Args:
            state: WorkflowState to save

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            path = self._get_session_path(state.workflow_id)
            data = state.to_dict()
            data["updated_at"] = datetime.utcnow().isoformat()
            if not data.get("created_at"):
                data["created_at"] = datetime.utcnow().isoformat()

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save workflow state: {e}")
            return False

    def load(self, workflow_id: str) -> Optional[WorkflowState]:
        """Load workflow state from file.

        Args:
            workflow_id: ID of workflow to load

        Returns:
            WorkflowState if found, None otherwise
        """
        try:
            path = self._get_session_path(workflow_id)
            if not path.exists():
                return None

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            return WorkflowState.from_dict(data)
        except Exception as e:
            print(f"Failed to load workflow state: {e}")
            return None

    def exists(self, workflow_id: str) -> bool:
        """Check if a workflow session exists."""
        path = self._get_session_path(workflow_id)
        return path.exists()

    def delete(self, workflow_id: str) -> bool:
        """Delete a workflow session.

        Args:
            workflow_id: ID of workflow to delete

        Returns:
            True if deleted, False otherwise
        """
        try:
            path = self._get_session_path(workflow_id)
            if path.exists():
                path.unlink()
            return True
        except Exception as e:
            print(f"Failed to delete workflow state: {e}")
            return False

    def list_workflows(self) -> List[str]:
        """List all workflow IDs."""
        try:
            return [p.stem for p in self.base_dir.glob("*.json")]
        except Exception as e:
            print(f"Failed to list workflows: {e}")
            return []
