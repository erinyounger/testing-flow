import subprocess
import json
import shlex
from dataclasses import dataclass
from typing import Optional, Any
from tflow.agents.base import BaseAgent, AgentResult


@dataclass
class ExecResult:
    """Execution result"""
    success: bool
    output: str = ""
    error: Optional[str] = None


class SubprocessAgent(BaseAgent):
    """Agent that executes commands in subprocess"""

    def run(self, command: str, agent_type: str = "shell", timeout: int = 30, **kwargs) -> AgentResult:
        """Execute a command in subprocess"""
        try:
            if agent_type == "shell":
                return self._run_shell(command, timeout)
            elif agent_type == "claude":
                return self._run_claude(command, timeout)
            else:
                return AgentResult(success=False, error=f"Unknown agent type: {agent_type}")
        except subprocess.TimeoutExpired:
            return AgentResult(success=False, error=f"Timeout after {timeout} seconds")
        except Exception as e:
            return AgentResult(success=False, error=str(e))

    def _run_shell(self, command: str, timeout: int) -> AgentResult:
        """Run shell command"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return AgentResult(success=True, output=result.stdout)
            else:
                return AgentResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr or f"Command failed with code {result.returncode}"
                )
        except subprocess.TimeoutExpired:
            return AgentResult(success=False, error=f"Timeout after {timeout} seconds")

    def _run_claude(self, prompt: str, timeout: int) -> AgentResult:
        """Run claude command"""
        cmd = self._build_command(prompt, agent_type="claude")

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            if result.returncode == 0:
                return AgentResult(success=True, output=result.stdout)
            else:
                return AgentResult(
                    success=False,
                    output=result.stdout,
                    error=result.stderr or f"Command failed with code {result.returncode}"
                )
        except subprocess.TimeoutExpired:
            return AgentResult(success=False, error=f"Timeout after {timeout} seconds")

    def _build_command(self, prompt: str, agent_type: str = "claude") -> str:
        """Build command for the agent"""
        if agent_type == "claude":
            # Escape prompt for shell
            escaped_prompt = shlex.quote(prompt)
            return f"claude {escaped_prompt}"
        return prompt

    def parse_output(self, output: str) -> Any:
        """Parse JSON output"""
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output