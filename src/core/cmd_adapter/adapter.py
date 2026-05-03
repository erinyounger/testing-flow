"""
Command adapter base class and registry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging
import subprocess


@dataclass
class CommandResult:
    """
    Result from command execution.

    Attributes:
        success: Whether command succeeded
        stdout: Standard output
        stderr: Standard error
        returncode: Process return code
        command: The command that was executed
    """
    success: bool
    stdout: str
    stderr: str
    returncode: int
    command: str
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "returncode": self.returncode,
            "command": self.command,
            "error": self.error,
        }


class CommandAdapter(ABC):
    """
    Abstract base class for OS-specific command adapters.

    Each adapter implements commands specific to an OS distribution.
    """

    @property
    @abstractmethod
    def os_id(self) -> str:
        """Return the OS identifier this adapter supports."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the adapter name."""
        pass

    @abstractmethod
    def execute(self, cmd_name: str, **kwargs) -> CommandResult:
        """
        Execute a named command.

        Args:
            cmd_name: Command name (e.g., 'info', 'ls', 'df')
            **kwargs: Additional arguments for the command

        Returns:
            CommandResult with execution outcome
        """
        pass

    @abstractmethod
    def get_supported_commands(self) -> List[str]:
        """Return list of supported command names."""
        pass

    def _run_command(self, cmd: List[str], timeout: int = 30) -> CommandResult:
        """
        Run a shell command and return result.

        Args:
            cmd: Command as list of strings
            timeout: Command timeout in seconds

        Returns:
            CommandResult
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return CommandResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                command=" ".join(cmd),
            )
        except subprocess.TimeoutExpired:
            return CommandResult(
                success=False,
                stdout="",
                stderr=f"Command timed out after {timeout}s",
                returncode=-1,
                command=" ".join(cmd),
                error="timeout",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-1,
                command=" ".join(cmd),
                error=str(e),
            )


class CommandRegistry:
    """
    Registry for command adapters.

    Maintains a mapping of OS IDs to command adapters and
    routes commands to the appropriate adapter.
    """

    def __init__(self):
        self._adapters: Dict[str, CommandAdapter] = {}
        self._current_os: Optional[str] = None
        self._generic_adapter: Optional[CommandAdapter] = None
        self._command_overrides: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, adapter: CommandAdapter) -> None:
        """
        Register a command adapter.

        Args:
            adapter: Command adapter instance
        """
        self._adapters[adapter.os_id] = adapter
        self._logger.debug(f"Registered command adapter: {adapter.os_id}")

    def set_generic_adapter(self, adapter: CommandAdapter) -> None:
        """
        Set the fallback generic adapter.

        Args:
            adapter: Generic command adapter
        """
        self._generic_adapter = adapter
        self._logger.debug("Set generic command adapter")

    def set_os(self, os_id: str) -> None:
        """
        Set the current OS for command routing.

        Args:
            os_id: OS identifier
        """
        self._current_os = os_id
        self._logger.info(f"Command registry OS set to: {os_id}")

    def get_adapter(self) -> Optional[CommandAdapter]:
        """
        Get the adapter for the current OS.

        Returns:
            Command adapter or None
        """
        if self._current_os and self._current_os in self._adapters:
            return self._adapters[self._current_os]
        if self._generic_adapter:
            return self._generic_adapter
        return None

    def load_command_overrides(self, overrides: Dict[str, Dict[str, Any]]) -> None:
        """
        Load command overrides from configuration.

        Args:
            overrides: Dict mapping OS IDs to command overrides
        """
        self._command_overrides = overrides
        self._logger.info(f"Loaded command overrides for {len(overrides)} OSes")

    def execute(self, cmd_name: str, **kwargs) -> CommandResult:
        """
        Execute a command using the current OS adapter.

        Args:
            cmd_name: Command name
            **kwargs: Additional arguments

        Returns:
            CommandResult
        """
        adapter = self.get_adapter()
        if not adapter:
            return CommandResult(
                success=False,
                stdout="",
                stderr="No command adapter available",
                returncode=-1,
                command=cmd_name,
                error="no_adapter",
            )
        return adapter.execute(cmd_name, **kwargs)

    def get_current_os(self) -> Optional[str]:
        """Return current OS ID."""
        return self._current_os
