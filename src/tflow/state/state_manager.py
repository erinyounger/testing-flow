import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

WORKFLOW_DIR = ".workflow"


@dataclass
class ProjectState:
    """Project state data structure"""
    version: str = "1.0"
    status: str = "idle"  # idle, planning, executing, verifying
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    accumulated_context: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: {
        "key_decisions": [],
        "blockers": [],
        "deferred": []
    })

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectState":
        return cls(
            version=data.get("version", "1.0"),
            status=data.get("status", "idle"),
            artifacts=data.get("artifacts", []),
            accumulated_context=data.get("accumulated_context", {
                "key_decisions": [],
                "blockers": [],
                "deferred": []
            })
        )


class StateManager:
    """Manages project state persistence"""

    def __init__(self, workflow_dir: str = WORKFLOW_DIR):
        self.workflow_dir = Path(workflow_dir)

    def _get_state_file(self) -> Path:
        return self.workflow_dir / "state.json"

    def load(self) -> ProjectState:
        """Load state from file, return empty state if not exists"""
        state_file = self._get_state_file()
        if not state_file.exists():
            return ProjectState()

        with open(state_file) as f:
            data = json.load(f)
        return ProjectState.from_dict(data)

    def save(self, state: ProjectState) -> None:
        """Save state to file"""
        self.workflow_dir.mkdir(parents=True, exist_ok=True)
        state_file = self._get_state_file()

        with open(state_file, "w") as f:
            json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

    def is_task_done(self, task_id: str) -> bool:
        """Check if task is completed"""
        state = self.load()
        for artifact in state.artifacts:
            if artifact.get("task_id") == task_id and artifact.get("status") == "completed":
                return True
        return False

    def register_artifact(self, artifact: Dict[str, Any]) -> None:
        """Register an artifact"""
        state = self.load()
        state.artifacts.append(artifact)
        self.save(state)

    def add_key_decision(self, text: str) -> None:
        """Add a key decision to accumulated context"""
        state = self.load()
        state.accumulated_context["key_decisions"].append({
            "text": text,
            "timestamp": datetime.now().isoformat()
        })
        self.save(state)