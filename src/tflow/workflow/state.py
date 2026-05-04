"""工作流状态定义"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import json
from pathlib import Path


class WorkflowType(Enum):
    """工作流类型"""
    STANDARD = "standard"
    FULL = "full"
    INIT = "init"


class WorkflowStatus(Enum):
    """工作流状态

    线性状态机流程：PARSING → VALIDATING → PLANNING → EXECUTING → VERIFYING → COMPLETING → COMPLETED
    """
    IDLE = "idle"
    PARSING = "parsing"
    VALIDATING = "validating"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class WorkflowState:
    """工作流状态"""
    workflow_type: WorkflowType
    session_id: str
    status: WorkflowStatus
    current_phase: str
    workflow_id: str = ""  # 内部工作流标识
    context: dict[str, Any] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_type": self.workflow_type.value,
            "workflow_id": self.workflow_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "current_phase": self.current_phase,
            "context": self.context,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        return cls(
            workflow_type=WorkflowType(data["workflow_type"]),
            workflow_id=data.get("workflow_id", ""),
            session_id=data["session_id"],
            status=WorkflowStatus(data["status"]),
            current_phase=data["current_phase"],
            context=data.get("context", {}),
            result=data.get("result", {}),
            error=data.get("error"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class WorkflowPersistence:
    """工作流持久化"""

    def __init__(self, storage_dir: str | Path = ".workflow/sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_state(self, state: WorkflowState) -> None:
        """保存状态"""
        path = self._get_path(state.session_id)
        with open(path, "w") as f:
            json.dump(state.to_dict(), f, indent=2)

    def load_state(self, session_id: str) -> WorkflowState | None:
        """加载状态"""
        path = self._get_path(session_id)
        if not path.exists():
            return None
        with open(path) as f:
            return WorkflowState.from_dict(json.load(f))

    def _get_path(self, session_id: str) -> Path:
        return self.storage_dir / f"{session_id}.json"

    def list_sessions(self) -> list[str]:
        """列出所有工作流会话"""
        sessions = []
        for filename in self.storage_dir.iterdir():
            if filename.suffix == ".json":
                sessions.append(filename.stem)
        return sessions
