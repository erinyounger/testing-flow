"""Job 事件定义"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .job import JobStatus


@dataclass
class JobEvent:
    """Job 事件"""
    event_id: int
    sequence: int
    job_id: str
    type: str
    created_at: str
    status: JobStatus | None = None
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        job_id: str,
        event_type: str,
        status: JobStatus | None = None,
        payload: dict[str, Any] | None = None,
        event_id: int = 0,
        sequence: int = 0,
    ) -> "JobEvent":
        """创建新事件"""
        return cls(
            event_id=event_id,
            sequence=sequence,
            job_id=job_id,
            type=event_type,
            created_at=datetime.now().isoformat(),
            status=status,
            payload=payload or {},
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "job_id": self.job_id,
            "type": self.type,
            "created_at": self.created_at,
            "status": self.status.value if self.status else None,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "JobEvent":
        """从字典创建"""
        status = data.get("status")
        if isinstance(status, str):
            status = JobStatus(status)
        return cls(
            event_id=data["event_id"],
            sequence=data["sequence"],
            job_id=data["job_id"],
            type=data["type"],
            created_at=data["created_at"],
            status=status,
            payload=data.get("payload", {}),
        )
