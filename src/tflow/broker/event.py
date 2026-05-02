from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class Event:
    """Broker event data structure"""
    id: str
    session_id: str
    event_type: str  # job_started, job_completed, job_failed, session_started, session_completed
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "data": self.data,
            "timestamp": self.timestamp
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        return cls(
            id=data.get("id", ""),
            session_id=data.get("session_id", ""),
            event_type=data.get("event_type", ""),
            data=data.get("data", {}),
            timestamp=data.get("timestamp", "")
        )