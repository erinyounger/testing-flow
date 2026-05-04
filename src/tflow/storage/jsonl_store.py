"""JSONL storage for execution records."""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
from datetime import datetime


@dataclass
class ExecutionRecord:
    """Execution record dataclass."""

    execution_id: str
    workflow_id: str
    task_id: str
    agent_id: str
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        """Initialize metadata if not set."""
        if self.metadata is None:
            self.metadata = {}
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionRecord":
        """Create from dictionary."""
        return cls(**data)


class ExecutionStore:
    """JSONL storage for execution records.

    Appends records to a JSONL file for sequential storage.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize execution store.

        Args:
            base_dir: Base directory for storage. Defaults to .workflow/executions/
        """
        if base_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            base_dir = project_root / ".workflow" / "executions"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, workflow_id: str) -> Path:
        """Get file path for workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            File path
        """
        return self.base_dir / f"{workflow_id}.jsonl"

    def append(self, record: ExecutionRecord) -> bool:
        """Append a record to the store.

        Args:
            record: Execution record to append

        Returns:
            True if successful
        """
        try:
            path = self._get_file_path(record.workflow_id)
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            print(f"Failed to append record: {e}")
            return False

    def get(self, workflow_id: str) -> List[ExecutionRecord]:
        """Get all records for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            List of execution records
        """
        records = []
        path = self._get_file_path(workflow_id)

        if not path.exists():
            return records

        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        records.append(ExecutionRecord.from_dict(data))
        except Exception as e:
            print(f"Failed to read records: {e}")

        return records

    def get_latest(self, workflow_id: str) -> Optional[ExecutionRecord]:
        """Get the latest record for a workflow.

        Args:
            workflow_id: Workflow ID

        Returns:
            Latest record or None
        """
        records = self.get(workflow_id)
        return records[-1] if records else None

    def get_by_task(
        self,
        workflow_id: str,
        task_id: str,
    ) -> List[ExecutionRecord]:
        """Get records for a specific task.

        Args:
            workflow_id: Workflow ID
            task_id: Task ID

        Returns:
            List of matching records
        """
        records = self.get(workflow_id)
        return [r for r in records if r.task_id == task_id]

    def list_workflows(self) -> List[str]:
        """List all workflow IDs with records.

        Returns:
            List of workflow IDs
        """
        try:
            return [p.stem for p in self.base_dir.glob("*.jsonl")]
        except Exception as e:
            print(f"Failed to list workflows: {e}")
            return []
