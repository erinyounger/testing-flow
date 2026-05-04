"""Direct backend for subprocess execution."""

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
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

    async def execute(
        self,
        command: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute a command as subprocess.

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
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=exec_env,
                cwd=cwd,
                shell=self.config.shell if self.config else False,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
                return {
                    "returncode": process.returncode,
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                }
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
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
