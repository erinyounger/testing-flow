"""SQLite storage for sessions and tasks."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any
import sqlite3
import json
import asyncio


@dataclass
class SQLiteStoreConfig:
    """Configuration for SQLite store."""

    db_path: Optional[str] = None
    timeout: int = 5
    wal_mode: bool = True  # Write-Ahead Logging mode


class SQLiteStore:
    """SQLite storage for sessions and tasks.

    Provides structured storage using SQLite.
    """

    def __init__(self, config: Optional[SQLiteStoreConfig] = None):
        """Initialize SQLite store.

        Args:
            config: Store configuration
        """
        if config is None:
            config = SQLiteStoreConfig()

        self.config = config

        if config.db_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            db_path = project_root / ".workflow" / "tflow.db"
        else:
            db_path = Path(config.db_path)

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self._lock = asyncio.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.

        Returns:
            SQLite connection
        """
        conn = sqlite3.connect(self.db_path, timeout=self.config.timeout)
        conn.row_factory = sqlite3.Row
        if self.config.wal_mode:
            conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        """Initialize database schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    context TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT
                )
            """)

            # Tasks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    input_data TEXT,
                    output_data TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    metadata TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
                )
            """)

            conn.commit()
        finally:
            conn.close()

    async def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save a session.

        Args:
            session_data: Session data dictionary

        Returns:
            True if successful
        """
        async with self._lock:
            return await asyncio.to_thread(self._save_session_sync, session_data)

    def _save_session_sync(self, session_data: Dict[str, Any]) -> bool:
        """Synchronous save session."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Serialize context and metadata
            context_json = json.dumps(session_data.get("context", {}))
            metadata_json = json.dumps(session_data.get("metadata", {}))

            cursor.execute("""
                INSERT OR REPLACE INTO sessions
                (session_id, name, context, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_data["session_id"],
                session_data["name"],
                context_json,
                session_data["created_at"],
                session_data["updated_at"],
                metadata_json,
            ))

            conn.commit()
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
        finally:
            conn.close()

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session data or None
        """
        async with self._lock:
            return await asyncio.to_thread(self._get_session_sync, session_id)

    def _get_session_sync(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous get session."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_session(row)
            return None
        finally:
            conn.close()

    async def list_sessions(self, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """List all sessions.

        Args:
            status: Filter by status
            limit: Maximum number of results

        Returns:
            List of session data
        """
        async with self._lock:
            return await asyncio.to_thread(self._list_sessions_sync, status, limit)

    def _list_sessions_sync(self, status: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Synchronous list sessions."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if status:
                cursor.execute(
                    "SELECT * FROM sessions WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status, limit)
                )
            else:
                cursor.execute("SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [self._row_to_session(row) for row in rows]
        finally:
            conn.close()

    def _row_to_session(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert row to session dict."""
        return {
            "session_id": row["session_id"],
            "name": row["name"],
            "context": json.loads(row["context"] or "{}"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "metadata": json.loads(row["metadata"] or "{}"),
        }

    async def save_task(self, task_data: Dict[str, Any]) -> bool:
        """Save a task.

        Args:
            task_data: Task data dictionary

        Returns:
            True if successful
        """
        async with self._lock:
            return await asyncio.to_thread(self._save_task_sync, task_data)

    def _save_task_sync(self, task_data: Dict[str, Any]) -> bool:
        """Synchronous save task."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Serialize complex fields
            input_json = json.dumps(task_data.get("input_data", {}))
            output_json = json.dumps(task_data.get("output_data"))
            metadata_json = json.dumps(task_data.get("metadata", {}))

            cursor.execute("""
                INSERT OR REPLACE INTO tasks
                (task_id, session_id, name, description, status,
                 input_data, output_data, error, created_at, updated_at,
                 started_at, completed_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data["task_id"],
                task_data.get("session_id"),
                task_data["name"],
                task_data.get("description"),
                task_data["status"],
                input_json,
                output_json,
                task_data.get("error"),
                task_data["created_at"],
                task_data["updated_at"],
                task_data.get("started_at"),
                task_data.get("completed_at"),
                metadata_json,
            ))

            conn.commit()
            return True
        except Exception as e:
            print(f"Failed to save task: {e}")
            return False
        finally:
            conn.close()

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task data or None
        """
        async with self._lock:
            return await asyncio.to_thread(self._get_task_sync, task_id)

    def _get_task_sync(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous get task."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM tasks WHERE task_id = ?",
                (task_id,),
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_task(row)
            return None
        finally:
            conn.close()

    async def get_tasks(self, session_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get tasks for a session.

        Args:
            session_id: Session ID
            status: Filter by status

        Returns:
            List of task data
        """
        async with self._lock:
            return await asyncio.to_thread(self._get_tasks_sync, session_id, status)

    def _get_tasks_sync(self, session_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Synchronous get tasks."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if status:
                cursor.execute(
                    "SELECT * FROM tasks WHERE session_id = ? AND status = ? ORDER BY created_at",
                    (session_id, status)
                )
            else:
                cursor.execute(
                    "SELECT * FROM tasks WHERE session_id = ? ORDER BY created_at",
                    (session_id,)
                )
            rows = cursor.fetchall()
            return [self._row_to_task(row) for row in rows]
        finally:
            conn.close()

    def _row_to_task(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert row to task dict."""
        return {
            "task_id": row["task_id"],
            "session_id": row["session_id"],
            "name": row["name"],
            "description": row["description"],
            "status": row["status"],
            "input_data": json.loads(row["input_data"] or "{}"),
            "output_data": json.loads(row["output_data"] or "null"),
            "error": row["error"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "started_at": row["started_at"],
            "completed_at": row["completed_at"],
            "metadata": json.loads(row["metadata"] or "{}"),
        }

    async def close(self) -> None:
        """Close the store connection."""
        pass  # SQLite connections are closed per-operation
