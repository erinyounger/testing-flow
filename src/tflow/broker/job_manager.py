"""Job 状态管理 + 事件 Broker"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable
import asyncio
import json
import sqlite3
from pathlib import Path
import uuid

from .job import Job, JobStatus
from .event import JobEvent
from .message import QueuedMessage, MessageDelivery, MessageStatus


@dataclass
class JobManager:
    """Job 状态管理和事件 Broker"""

    def __init__(self, db_path: str | Path | None = None):
        if db_path is None:
            db_path = ".tflow/jobs.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._subscribers: list[Callable[[JobEvent], None]] = []

    def _init_db(self) -> None:
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_event_id INTEGER DEFAULT 0,
                    last_event_type TEXT DEFAULT '',
                    latest_snapshot TEXT,
                    metadata TEXT
                );

                CREATE TABLE IF NOT EXISTS events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sequence INTEGER NOT NULL,
                    job_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    status TEXT,
                    payload TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                );

                CREATE INDEX IF NOT EXISTS idx_events_job ON events(job_id);
            """)

    async def create_job(
        self,
        job_type: str,
        payload: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Job:
        """创建新 Job"""
        now = datetime.now().isoformat()
        job = Job(
            job_id=f"job-{uuid.uuid4().hex[:12]}",
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
            metadata=metadata or {"type": job_type},
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO jobs (job_id, status, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (job.job_id, job.status.value, job.created_at, job.updated_at, json.dumps(job.metadata)))

        await self._publish_event(job.job_id, "job_created", {"job_id": job.job_id})

        return job

    async def update_status(
        self,
        job_id: str,
        status: str | JobStatus,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> JobEvent:
        """更新 Job 状态"""
        now = datetime.now().isoformat()

        # 转换状态字符串到 JobStatus
        if isinstance(status, str):
            status = JobStatus(status)

        with sqlite3.connect(self.db_path) as conn:
            # 获取序列号
            row = conn.execute(
                "SELECT COALESCE(MAX(sequence), 0) FROM events WHERE job_id = ?",
                (job_id,)
            ).fetchone()
            sequence = (row[0] or 0) + 1

            # 插入事件
            cursor = conn.execute("""
                INSERT INTO events (sequence, job_id, type, created_at, status, payload)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sequence, job_id, event_type, now, status.value, json.dumps(payload or {})))
            event_id = cursor.lastrowid

            # 更新 Job
            conn.execute("""
                UPDATE jobs SET updated_at = ?, status = ?, last_event_id = ?, last_event_type = ?
                WHERE job_id = ?
            """, (now, status.value, event_id, event_type, job_id))

        event = JobEvent(
            event_id=event_id,
            sequence=sequence,
            job_id=job_id,
            type=event_type,
            created_at=now,
            status=status,
            payload=payload or {},
        )

        # 通知订阅者
        for subscriber in self._subscribers:
            await subscriber(event)

        # 检查是否需要触发后续消息
        if status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            await self._dispatch_queued_messages(job_id, status)

        return event

    async def poll_events(
        self,
        session_id: str,
        job_id: str | None = None,
        after_event_id: int = 0,
        limit: int = 100,
    ) -> list[JobEvent]:
        """轮询事件"""
        with sqlite3.connect(self.db_path) as conn:
            if job_id:
                rows = conn.execute("""
                    SELECT event_id, sequence, job_id, type, created_at, status, payload
                    FROM events
                    WHERE job_id = ? AND event_id > ?
                    ORDER BY event_id
                    LIMIT ?
                """, (job_id, after_event_id, limit)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT event_id, sequence, job_id, type, created_at, status, payload
                    FROM events
                    WHERE event_id > ?
                    ORDER BY event_id
                    LIMIT ?
                """, (after_event_id, limit)).fetchall()

        return [
            JobEvent(
                event_id=row[0],
                sequence=row[1],
                job_id=row[2],
                type=row[3],
                created_at=row[4],
                status=JobStatus(row[5]) if row[5] else None,
                payload=json.loads(row[6]) if row[6] else {},
            )
            for row in rows
        ]

    async def subscribe(
        self,
        callback: Callable[[JobEvent], None],
    ) -> Callable[[], None]:
        """订阅事件"""
        self._subscribers.append(callback)
        return lambda: self._subscribers.remove(callback)

    async def _publish_event(self, job_id: str, event_type: str, payload: dict) -> JobEvent:
        """发布事件"""
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO events (sequence, job_id, type, created_at, payload)
                VALUES (
                    COALESCE((SELECT MAX(sequence) FROM events WHERE job_id = ?), 0) + 1,
                    ?, ?, ?, ?
                )
            """, (job_id, job_id, event_type, now, json.dumps(payload)))
            event_id = cursor.lastrowid

            conn.execute("""
                UPDATE jobs
                SET updated_at = ?, last_event_id = ?, last_event_type = ?
                WHERE job_id = ?
            """, (now, event_id, event_type, job_id))

        return JobEvent(
            event_id=event_id,
            sequence=0,
            job_id=job_id,
            type=event_type,
            created_at=now,
            payload=payload,
        )

    async def _dispatch_queued_messages(self, job_id: str, final_status: JobStatus) -> None:
        """分发排队的消息"""
        # 从数据库获取该 job 的排队消息
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("""
                SELECT message_id, delivery, payload
                FROM message_queue
                WHERE job_id = ? AND status = 'pending'
            """, (job_id,)).fetchall()

        for row in rows:
            message_id, delivery, payload = row
            # 只分发 AFTER_COMPLETE 类型的消息
            if delivery == MessageDelivery.AFTER_COMPLETE.value:
                # 实际实现时会调用相应的处理器
                # 这里只是标记消息已被处理
                pass

            # 更新消息状态
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE message_queue
                    SET status = 'dispatched', dispatched_at = ?
                    WHERE message_id = ?
                """, (datetime.now().isoformat(), message_id))
