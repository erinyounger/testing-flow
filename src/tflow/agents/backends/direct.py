"""Direct backend for subprocess execution."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List, AsyncIterator
import subprocess
import os
import asyncio


@dataclass
class DirectBackendConfig:
    """Configuration for direct backend."""

    command: List[str]
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    timeout: int = 300
    shell: bool = False


class DirectBackend:
    """Direct subprocess execution backend.

    Executes commands as child processes and returns output streams.
    """

    def __init__(self, config: Optional[DirectBackendConfig] = None):
        """Initialize direct backend.

        Args:
            config: Backend configuration
        """
        self.config = config
        self._process: Optional[asyncio.subprocess.Process] = None

    async def execute(
        self,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> AsyncIterator[str]:
        """Execute a command as subprocess, yielding output progressively.

        Args:
            command: Command to execute
            env: Environment variables
            cwd: Working directory
            timeout: Timeout in seconds

        Yields:
            String output lines from stdout/stderr
        """
        if command is None and self.config:
            command = self.config.command
        if env is None and self.config:
            env = self.config.env
        if cwd is None and self.config:
            cwd = self.config.cwd
        if timeout is None and self.config:
            timeout = self.config.timeout

        if not command:
            raise ValueError("No command provided")

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        try:
            self._process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=exec_env,
                cwd=cwd,
                shell=self.config.shell if self.config else False,
            )

            try:
                # Read stdout in chunks as they arrive
                while True:
                    try:
                        chunk = await asyncio.wait_for(
                            self._process.stdout.read(1024),
                            timeout=0.1,
                        )
                        if chunk:
                            yield chunk.decode(errors="replace")
                        else:
                            break
                    except asyncio.TimeoutError:
                        # Check if process ended
                        if self._process.returncode is not None:
                            break
                        continue

                # Read any remaining stderr
                stderr_bytes = await self._process.stderr.read()
                if stderr_bytes:
                    yield f"\n[stderr] {stderr_bytes.decode(errors='replace')}"

                # Wait for process to complete
                await self._process.wait()
                yield f"\n[exit code: {self._process.returncode}]"

            except asyncio.TimeoutError:
                if self._process:
                    self._process.kill()
                    await self._process.wait()
                yield f"\n[timeout: command timed out after {timeout}s]"
        except Exception as e:
            yield f"\n[error: {str(e)}]"
        finally:
            self._process = None

    def kill(self) -> bool:
        """Kill the currently running process.

        Returns:
            True if killed successfully
        """
        if self._process and self._process.poll() is None:
            try:
                self._process.kill()
                return True
            except Exception:
                return False
        return False

    def is_running(self) -> bool:
        """Check if the process is currently running.

        Returns:
            True if running, False otherwise
        """
        if self._process:
            return self._process.poll() is None
        return False

    def execute_sync(
        self,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Synchronous version of execute.

        Args:
            command: Command to execute
            env: Environment variables
            cwd: Working directory
            timeout: Timeout in seconds

        Returns:
            Dict with returncode, stdout, stderr
        """
        if command is None and self.config:
            command = self.config.command
        if env is None and self.config:
            env = self.config.env
        if cwd is None and self.config:
            cwd = self.config.cwd
        if timeout is None and self.config:
            timeout = self.config.timeout

        if not command:
            raise ValueError("No command provided")

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                env=exec_env,
                cwd=cwd,
                timeout=timeout,
                shell=self.config.shell if self.config else False,
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout.decode() if result.stdout else "",
                "stderr": result.stderr.decode() if result.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e),
            }
