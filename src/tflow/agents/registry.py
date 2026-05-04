"""Agent registry and base agent classes."""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
import subprocess
import signal
import os


class AgentType(Enum):
    """Agent type enum."""

    CLAUDE_CODE = "claude-code"
    GEMINI = "gemini"
    QWEN = "qwen"
    CODEX = "codex"
    OPENCODE = "opencode"


class ExecutionMode(Enum):
    """Agent execution mode."""

    DIRECT = "direct"
    TERMINAL = "terminal"
    MCP = "mcp"


@dataclass
class AgentConfig:
    """Agent configuration dataclass."""

    agent_type: AgentType
    name: str
    description: str
    execution_mode: ExecutionMode = ExecutionMode.DIRECT
    command: Optional[str] = None
    env: Dict[str, str] = field(default_factory=dict)
    working_dir: Optional[str] = None
    timeout: int = 300
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set default command based on agent type."""
        if not self.command:
            self.command = self._default_command()

    def _default_command(self) -> Optional[str]:
        """Get default command for agent type."""
        commands = {
            AgentType.CLAUDE_CODE: "claude",
            AgentType.GEMINI: "gemini",
            AgentType.QWEN: "qwen",
            AgentType.CODEX: "codex",
            AgentType.OPENCODE: "opencode",
        }
        return commands.get(self.agent_type)


@dataclass
class AgentProcess:
    """Subprocess wrapper for agent execution."""

    pid: int
    process: subprocess.Popen
    command: List[str]
    started_at: Optional[str] = None

    def is_alive(self) -> bool:
        """Check if process is still running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self, timeout: int = 5) -> bool:
        """Stop the process gracefully.

        Args:
            timeout: Seconds to wait for graceful shutdown

        Returns:
            True if stopped, False if force killed
        """
        if self.process is None:
            return True

        try:
            self.process.terminate()
            self.process.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            self.process.kill()
            return False
        except Exception:
            return False

    def send_input(self, data: str) -> bool:
        """Send input to process stdin."""
        if self.process and self.process.stdin:
            try:
                self.process.stdin.write(data + "\n")
                self.process.stdin.flush()
                return True
            except Exception:
                return False
        return False


class BaseAgent(ABC):
    """Abstract base agent class."""

    def __init__(self, config: AgentConfig):
        """Initialize agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self._process: Optional[AgentProcess] = None

    @property
    def name(self) -> str:
        """Get agent name."""
        return self.config.name

    @property
    def agent_type(self) -> AgentType:
        """Get agent type."""
        return self.config.agent_type

    @abstractmethod
    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        """Spawn agent for task.

        Args:
            task: Task data

        Returns:
            AgentProcess instance
        """
        pass

    @abstractmethod
    def on_entry(self, task: Dict[str, Any]) -> None:
        """Called when agent is assigned a task.

        Args:
            task: Task data
        """
        pass

    def stop(self) -> bool:
        """Stop the agent process.

        Returns:
            True if stopped successfully
        """
        if self._process:
            return self._process.stop()
        return True

    def get_process(self) -> Optional[AgentProcess]:
        """Get current process."""
        return self._process


class ClaudeAgent(BaseAgent):
    """Claude agent implementation."""

    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        """Spawn Claude agent."""
        cmd = [self.config.command or "claude"]
        if task.get("prompt"):
            cmd.extend(["--prompt", task["prompt"]])

        env = os.environ.copy()
        env.update(self.config.env)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=env,
            cwd=self.config.working_dir,
        )

        self._process = AgentProcess(
            pid=process.pid,
            process=process,
            command=cmd,
        )
        return self._process

    def on_entry(self, task: Dict[str, Any]) -> None:
        """Handle task entry."""
        pass


class GeminiAgent(BaseAgent):
    """Gemini agent implementation."""

    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        """Spawn Gemini agent."""
        cmd = [self.config.command or "gemini"]
        if task.get("prompt"):
            cmd.extend(["--prompt", task["prompt"]])

        env = os.environ.copy()
        env.update(self.config.env)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=env,
            cwd=self.config.working_dir,
        )

        self._process = AgentProcess(
            pid=process.pid,
            process=process,
            command=cmd,
        )
        return self._process

    def on_entry(self, task: Dict[str, Any]) -> None:
        """Handle task entry."""
        pass


class QwenAgent(BaseAgent):
    """Qwen agent implementation."""

    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        """Spawn Qwen agent."""
        cmd = [self.config.command or "qwen"]
        if task.get("prompt"):
            cmd.extend(["--prompt", task["prompt"]])

        env = os.environ.copy()
        env.update(self.config.env)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=env,
            cwd=self.config.working_dir,
        )

        self._process = AgentProcess(
            pid=process.pid,
            process=process,
            command=cmd,
        )
        return self._process

    def on_entry(self, task: Dict[str, Any]) -> None:
        """Handle task entry."""
        pass


class CodexAgent(BaseAgent):
    """Codex agent implementation."""

    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        """Spawn Codex agent."""
        cmd = [self.config.command or "codex"]
        if task.get("prompt"):
            cmd.extend(["--prompt", task["prompt"]])

        env = os.environ.copy()
        env.update(self.config.env)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=env,
            cwd=self.config.working_dir,
        )

        self._process = AgentProcess(
            pid=process.pid,
            process=process,
            command=cmd,
        )
        return self._process

    def on_entry(self, task: Dict[str, Any]) -> None:
        """Handle task entry."""
        pass


class OpencodeAgent(BaseAgent):
    """Opencode agent implementation."""

    def spawn(self, task: Dict[str, Any]) -> AgentProcess:
        """Spawn Opencode agent."""
        cmd = [self.config.command or "opencode"]
        if task.get("prompt"):
            cmd.extend(["--prompt", task["prompt"]])

        env = os.environ.copy()
        env.update(self.config.env)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            env=env,
            cwd=self.config.working_dir,
        )

        self._process = AgentProcess(
            pid=process.pid,
            process=process,
            command=cmd,
        )
        return self._process

    def on_entry(self, task: Dict[str, Any]) -> None:
        """Handle task entry."""
        pass


class AgentRegistry:
    """Singleton registry for agent instances.

    Manages agent registration and retrieval.
    """

    _instance: Optional["AgentRegistry"] = None

    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: Dict[str, BaseAgent] = {}
            cls._instance._configs: Dict[str, AgentConfig] = {}
        return cls._instance

    def register(self, agent: BaseAgent) -> None:
        """Register an agent.

        Args:
            agent: Agent instance to register
        """
        self._agents[agent.name] = agent
        self._configs[agent.name] = agent.config

    def get(self, name: str) -> Optional[BaseAgent]:
        """Get agent by name.

        Args:
            name: Agent name

        Returns:
            Agent instance or None
        """
        return self._agents.get(name)

    def get_config(self, name: str) -> Optional[AgentConfig]:
        """Get agent config by name.

        Args:
            name: Agent name

        Returns:
            AgentConfig or None
        """
        return self._configs.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent names.

        Returns:
            List of agent names
        """
        return list(self._agents.keys())

    def create_agent(self, config: AgentConfig) -> BaseAgent:
        """Create and register an agent from config.

        Args:
            config: Agent configuration

        Returns:
            Created agent instance
        """
        agent_classes = {
            AgentType.CLAUDE_CODE: ClaudeAgent,
            AgentType.GEMINI: GeminiAgent,
            AgentType.QWEN: QwenAgent,
            AgentType.CODEX: CodexAgent,
            AgentType.OPENCODE: OpencodeAgent,
        }

        agent_class = agent_classes.get(config.agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {config.agent_type}")

        agent = agent_class(config)
        self.register(agent)
        return agent


# Global singleton instance
agent_registry = AgentRegistry()
