# tflow.broker package
from tflow.broker.session import Session
from tflow.broker.job import Job
from tflow.broker.event import Event

__all__ = ["Session", "Job", "Event"]


class Broker:
    """Simple in-memory message broker for event-driven execution"""

    def __init__(self):
        self._subscribers: dict[str, list[callable]] = {}
        self._sessions: dict[str, Session] = {}
        self._jobs: dict[str, Job] = {}
        self._events: list[Event] = []

    def subscribe(self, event_type: str, callback: callable) -> None:
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers"""
        self._events.append(event)
        if event.event_type in self._subscribers:
            for callback in self._subscribers[event.event_type]:
                callback(event)

    def create_session(self, session: Session) -> None:
        """Create a new session"""
        self._sessions[session.id] = session

    def get_session(self, session_id: str) -> Session | None:
        """Get session by ID"""
        return self._sessions.get(session_id)

    def update_session(self, session: Session) -> None:
        """Update an existing session"""
        if session.id in self._sessions:
            self._sessions[session.id] = session

    def create_job(self, job: Job) -> None:
        """Create a new job"""
        self._jobs[job.id] = job

    def get_job(self, job_id: str) -> Job | None:
        """Get job by ID"""
        return self._jobs.get(job_id)

    def update_job(self, job: Job) -> None:
        """Update an existing job"""
        if job.id in self._jobs:
            self._jobs[job.id] = job

    def get_events(self, session_id: str | None = None) -> list[Event]:
        """Get events, optionally filtered by session_id"""
        if session_id is None:
            return self._events.copy()
        return [e for e in self._events if e.session_id == session_id]