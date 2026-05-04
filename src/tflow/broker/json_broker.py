"""JSON Broker 实现 - 基于 JSONL 的事件持久化"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import asyncio
import json
import os

from .persistence import BrokerPersistence
from .job_manager import Job, JobEvent, JobStatus


@dataclass
class JsonBrokerConfig:
    """JSON Broker 配置"""
    data_dir: Path = Path(".tflow/data")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    flush_interval: int = 5  # 秒


class JsonBroker(BrokerPersistence):
    """JSON Broker - JSONL 存储实现"""

    def __init__(self, config: JsonBrokerConfig | None = None):
        self.config = config or JsonBrokerConfig()
        self._jobs_file = self.config.data_dir / "jobs.jsonl"
        self._events_dir = self.config.data_dir / "events"
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._init_storage()

    def _init_storage(self) -> None:
        """初始化存储目录"""
        self.config.data_dir.mkdir(parents=True, exist_ok=True)
        self._events_dir.mkdir(parents=True, exist_ok=True)
        if self._jobs_file.exists():
            self._load_jobs()

    def _load_jobs(self) -> None:
        """加载 jobs"""
        with open(self._jobs_file, "r") as f:
            for line in f:
                if line.strip():
                    job_dict = json.loads(line)
                    # 转换 status 字符串为 JobStatus 枚举
                    if isinstance(job_dict.get("status"), str):
                        job_dict["status"] = JobStatus(job_dict["status"])
                    job = Job(**job_dict)
                    self._jobs[job.job_id] = job

    async def save_job(self, job: Job) -> None:
        """保存 Job"""
        async with self._lock:
            self._jobs[job.job_id] = job
            with open(self._jobs_file, "a") as f:
                f.write(json.dumps(job.__dict__, default=str) + "\n")

    async def get_job(self, job_id: str) -> Job | None:
        """获取 Job"""
        return self._jobs.get(job_id)

    async def save_event(self, event: JobEvent) -> None:
        """保存事件到 JSONL 文件"""
        async with self._lock:
            events_file = self._events_dir / f"{event.job_id}.jsonl"
            with open(events_file, "a") as f:
                f.write(json.dumps(event.__dict__, default=str) + "\n")

            # 检查文件大小，必要时轮转
            if events_file.exists() and events_file.stat().st_size > self.config.max_file_size:
                await self._rotate_events_file(event.job_id)

    async def _rotate_events_file(self, job_id: str) -> None:
        """轮转事件文件"""
        events_file = self._events_dir / f"{job_id}.jsonl"
        if not events_file.exists():
            return
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        rotated = self._events_dir / f"{job_id}_{timestamp}.jsonl"
        events_file.rename(rotated)

    async def get_events(
        self,
        job_id: str | None = None,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list[JobEvent]:
        """获取事件"""
        if job_id:
            return await self._get_job_events(job_id, after_event_id, limit)
        else:
            # 获取所有 jobs 的最新事件
            all_events = []
            for jid in self._jobs:
                all_events.extend(await self._get_job_events(jid, after_event_id, limit))
            return sorted(all_events, key=lambda e: e.event_id)[:limit]

    async def _get_job_events(
        self,
        job_id: str,
        after_event_id: int,
        limit: int,
    ) -> list[JobEvent]:
        """获取指定 job 的事件"""
        events_file = self._events_dir / f"{job_id}.jsonl"
        if not events_file.exists():
            return []

        events = []
        with open(events_file, "r") as f:
            for line in f:
                if line.strip():
                    event_dict = json.loads(line)
                    if event_dict["event_id"] > after_event_id:
                        # 转换 status 字符串为 JobStatus 枚举
                        if isinstance(event_dict.get("status"), str):
                            event_dict["status"] = JobStatus(event_dict["status"])
                        events.append(JobEvent(**event_dict))
                    if len(events) >= limit:
                        break
        return events

    async def list_jobs(self, status: str | None = None) -> list[Job]:
        """列出 Jobs"""
        if status:
            return [j for j in self._jobs.values() if j.status.value == status]
        return list(self._jobs.values())

    # 与 JobManager 的集成方法
    async def handle_job_event(self, event: JobEvent) -> None:
        """处理 Job 事件"""
        await self.save_event(event)
        if event.status:
            job = await self.get_job(event.job_id)
            if job:
                job.status = event.status
                job.last_event_id = event.event_id
                job.last_event_type = event.type
                await self.save_job(job)
