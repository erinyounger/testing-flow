import json
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class Plan:
    """Plan artifact data structure"""
    id: str
    task: str
    approach: str = ""
    complexity: str = "medium"
    task_ids: List[str] = field(default_factory=list)
    waves: List[List[str]] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Plan":
        return cls(
            id=data.get("id", ""),
            task=data.get("task", ""),
            approach=data.get("approach", ""),
            complexity=data.get("complexity", "medium"),
            task_ids=data.get("task_ids", []),
            waves=data.get("waves", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", "")
        )


class PlanArtifact:
    """Plan artifact manager"""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.plan_file = self.base_dir / "plan.json"
        self.task_dir = self.base_dir / ".task"

    def create(self, task: str, config: Dict[str, Any]) -> Plan:
        """Create a new plan"""
        import datetime
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        plan = Plan(
            id=plan_id,
            task=task,
            approach=config.get("approach", ""),
            complexity=config.get("complexity", "medium"),
            created_at=datetime.datetime.now().isoformat(),
            updated_at=datetime.datetime.now().isoformat()
        )

        self._ensure_dirs()
        with open(self.plan_file, "w") as f:
            json.dump(plan.to_dict(), f, indent=2, ensure_ascii=False)

        return plan

    def add_task(self, task: Dict[str, Any]) -> None:
        """Add a task to the plan"""
        task_id = task["id"]

        # Create task file
        self.task_dir.mkdir(parents=True, exist_ok=True)
        task_file = self.task_dir / f"{task_id}.json"
        with open(task_file, "w") as f:
            json.dump(task, f, indent=2, ensure_ascii=False)

        # Update plan.json task_ids
        if self.plan_file.exists():
            with open(self.plan_file) as f:
                plan_data = json.load(f)
        else:
            plan_data = {"task_ids": []}

        if task_id not in plan_data.get("task_ids", []):
            plan_data.setdefault("task_ids", []).append(task_id)

        with open(self.plan_file, "w") as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)

    def get_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks sorted by id"""
        if not self.task_dir.exists():
            return []

        tasks = []
        for task_file in self.task_dir.glob("TASK-*.json"):
            with open(task_file) as f:
                tasks.append(json.load(f))

        return sorted(tasks, key=lambda t: t["id"])

    def mark_done(self, task_id: str, summary: str, commit: str) -> None:
        """Mark task as done"""
        task_file = self.task_dir / f"{task_id}.json"
        if task_file.exists():
            with open(task_file) as f:
                task = json.load(f)

            task["status"] = "completed"
            task["summary"] = summary
            task["commit"] = commit

            with open(task_file, "w") as f:
                json.dump(task, f, indent=2, ensure_ascii=False)

    def _ensure_dirs(self) -> None:
        """Ensure required directories exist"""
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.task_dir.mkdir(parents=True, exist_ok=True)