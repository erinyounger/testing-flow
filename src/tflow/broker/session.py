from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Session:
    """Broker session data structure"""
    id: str
    task: str
    status: str = "created"  # created, running, completed, failed
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "task": self.task,
            "status": self.status,
            "context": self.context,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            id=data.get("id", ""),
            task=data.get("task", ""),
            status=data.get("status", "created"),
            context=data.get("context", {}),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )