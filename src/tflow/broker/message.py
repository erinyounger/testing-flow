"""消息队列定义"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
import uuid


class MessageDelivery(Enum):
    """消息投递模式"""
    INJECT = "inject"  # 立即注入
    AFTER_COMPLETE = "after_complete"  # 完成后投递


class MessageStatus(Enum):
    """消息状态"""
    PENDING = "pending"
    DISPATCHED = "dispatched"
    FAILED = "failed"


@dataclass
class QueuedMessage:
    """排队消息"""
    message_id: str
    job_id: str
    delivery: MessageDelivery
    payload: dict[str, Any]
    status: MessageStatus = MessageStatus.PENDING
    created_at: str = ""
    dispatched_at: str | None = None
    error: str | None = None

    @classmethod
    def create(
        cls,
        job_id: str,
        delivery: MessageDelivery,
        payload: dict[str, Any],
    ) -> "QueuedMessage":
        """创建新消息"""
        return cls(
            message_id=f"msg-{uuid.uuid4().hex[:12]}",
            job_id=job_id,
            delivery=delivery,
            payload=payload,
            created_at=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "job_id": self.job_id,
            "delivery": self.delivery.value,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at,
            "dispatched_at": self.dispatched_at,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "QueuedMessage":
        """从字典创建"""
        return cls(
            message_id=data["message_id"],
            job_id=data["job_id"],
            delivery=MessageDelivery(data["delivery"]),
            payload=data["payload"],
            status=MessageStatus(data.get("status", "pending")),
            created_at=data.get("created_at", ""),
            dispatched_at=data.get("dispatched_at"),
            error=data.get("error"),
        )
