"""Broker 持久化基类"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .job_manager import Job, JobEvent


class BrokerPersistence(ABC):
    """Broker 持久化抽象基类"""

    @abstractmethod
    async def save_job(self, job: "Job") -> None:
        """保存 Job 状态"""
        pass

    @abstractmethod
    async def get_job(self, job_id: str) -> "Job | None":
        """获取 Job"""
        pass

    @abstractmethod
    async def save_event(self, event: "JobEvent") -> None:
        """保存事件"""
        pass

    @abstractmethod
    async def get_events(
        self,
        job_id: str | None = None,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list["JobEvent"]:
        """获取事件"""
        pass

    @abstractmethod
    async def list_jobs(self, status: str | None = None) -> list["Job"]:
        """列出 Jobs"""
        pass
