"""Terminal backend for tmux-based execution."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
import subprocess
import os


@dataclass
class TerminalBackendConfig:
    """Configuration for terminal backend."""

    session_name: str = "tflow-agent"
    command: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    timeout: int = 300


class TerminalBackend:
    """Terminal backend using tmux.

    Executes commands in a tmux session for session persistence.
    """

    def __init__(self, config: Optional[TerminalBackendConfig] = None):
        """Initialize terminal backend.

        Args:
            config: Backend configuration
        """
        self.config = config

    def _run_tmux(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run tmux command.

        Args:
            args: tmux command arguments

        Returns:
            CompletedProcess result
        """
        cmd = ["tmux"] + args
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

    def create_session(self, session_name: Optional[str] = None) -> bool:
        """Create a new tmux session.

        Args:
            session_name: Session name

        Returns:
            True if created, False if exists
        """
        name = session_name or (self.config.session_name if self.config else "tflow-agent")

        # Check if session exists
        result = self._run_tmux(["has-session", "-t", name])
        if result.returncode == 0:
            return False

        # Create detached session
        result = self._run_tmux(["new-session", "-d", "-s", name])
        return result.returncode == 0

    def send_command(
        self,
        command: str,
        session_name: Optional[str] = None,
    ) -> bool:
        """Send command to tmux session.

        Args:
            command: Command to send
            session_name: Session name

        Returns:
            True if sent successfully
        """
        name = session_name or (self.config.session_name if self.config else "tflow-agent")
        result = self._run_tmux(["send-keys", "-t", name, command, "Enter"])
        return result.returncode == 0

    def capture_pane(
        self,
        session_name: Optional[str] = None,
    ) -> str:
        """Capture pane content.

        Args:
            session_name: Session name

        Returns:
            Pane content
        """
        name = session_name or (self.config.session_name if self.config else "tflow-agent")
        result = self._run_tmux(["capture-pane", "-t", name, "-p"])
        return result.stdout if result.returncode == 0 else ""

    def kill_session(self, session_name: Optional[str] = None) -> bool:
        """Kill a tmux session.

        Args:
            session_name: Session name

        Returns:
            True if killed
        """
        name = session_name or (self.config.session_name if self.config else "tflow-agent")
        result = self._run_tmux(["kill-session", "-t", name])
        return result.returncode == 0

    def execute(
        self,
        command: Optional[str] = None,
        session_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute command in tmux session.

        Args:
            command: Command to execute
            session_name: Session name

        Returns:
            Dict with success, output
        """
        name = session_name or (self.config.session_name if self.config else "tflow-agent")

        # Create session if not exists
        self.create_session(name)

        if command:
            self.send_command(command, name)

        return {
            "success": True,
            "session": name,
            "output": self.capture_pane(name),
        }

    def list_sessions(self) -> List[str]:
        """List all tmux sessions.

        Returns:
            List of session names
        """
        result = self._run_tmux(["list-sessions"])
        if result.returncode != 0:
            return []

        sessions = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split(":")
                if parts:
                    sessions.append(parts[0])
        return sessions
