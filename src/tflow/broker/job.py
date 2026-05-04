"""Job 状态管理"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class JobStatus(Enum):
    """Job 状态枚举"""
    QUEUED = "queued"
    RUNNING = "running"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Job:
    """Job 数据类"""
    job_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    last_event_id: int = 0
    last_event_type: str = ""
    latest_snapshot: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, job_type: str, metadata: dict[str, Any] | None = None) -> "Job":
        """创建新 Job"""
        now = datetime.now().isoformat()
        return cls(
            job_id=f"job-{uuid.uuid4().hex[:12]}",
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
            metadata=metadata or {"type": job_type},
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_event_id": self.last_event_id,
            "last_event_type": self.last_event_type,
            "latest_snapshot": self.latest_snapshot,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        """从字典创建"""
        status = data.get("status")
        if isinstance(status, str):
            status = JobStatus(status)
        return cls(
            job_id=data["job_id"],
            status=status,
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            last_event_id=data.get("last_event_id", 0),
            last_event_type=data.get("last_event_type", ""),
            latest_snapshot=data.get("latest_snapshot"),
            metadata=data.get("metadata", {}),
        )
