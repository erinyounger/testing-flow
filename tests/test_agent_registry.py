"""Tests for agent registry."""

import pytest

from tflow.agents import (
    AgentType,
    AgentConfig,
    AgentProcess,
    AgentRegistry,
    ClaudeAgent,
    GeminiAgent,
    QwenAgent,
    CodexAgent,
    OpencodeAgent,
)


class TestAgentConfig:
    """Test AgentConfig class."""

    def test_create(self):
        """Test creating agent config."""
        config = AgentConfig(
            agent_type=AgentType.CLAUDE,
            name="test-agent",
            description="A test agent",
        )

        assert config.agent_type == AgentType.CLAUDE
        assert config.name == "test-agent"
        assert config.command == "claude"

    def test_default_command(self):
        """Test default commands for agent types."""
        config = AgentConfig(
            agent_type=AgentType.GEMINI,
            name="gemini-agent",
            description="Gemini agent",
        )
        assert config.command == "gemini"

        config = AgentConfig(
            agent_type=AgentType.QWEN,
            name="qwen-agent",
            description="Qwen agent",
        )
        assert config.command == "qwen"


class TestAgentProcess:
    """Test AgentProcess class."""

    def test_create(self):
        """Test creating agent process."""
        import subprocess

        proc = subprocess.Popen(["echo", "test"])
        agent_proc = AgentProcess(
            pid=proc.pid,
            process=proc,
            command=["echo", "test"],
        )

        assert agent_proc.is_alive()
        agent_proc.stop()


class TestAgentRegistry:
    """Test AgentRegistry singleton."""

    def setup_method(self):
        """Set up test fixtures."""
        # Reset singleton
        AgentRegistry._instance = None
        self.registry = AgentRegistry()

    def test_singleton(self):
        """Test singleton pattern."""
        registry1 = AgentRegistry()
        registry2 = AgentRegistry()
        assert registry1 is registry2

    def test_register_and_get(self):
        """Test registering and getting agents."""
        config = AgentConfig(
            agent_type=AgentType.CLAUDE,
            name="claude-agent",
            description="Claude agent",
        )
        agent = ClaudeAgent(config)
        self.registry.register(agent)

        retrieved = self.registry.get("claude-agent")
        assert retrieved is not None
        assert retrieved.name == "claude-agent"

    def test_get_config(self):
        """Test getting agent config."""
        config = AgentConfig(
            agent_type=AgentType.GEMINI,
            name="gemini-agent",
            description="Gemini agent",
        )
        agent = GeminiAgent(config)
        self.registry.register(agent)

        retrieved_config = self.registry.get_config("gemini-agent")
        assert retrieved_config is not None
        assert retrieved_config.agent_type == AgentType.GEMINI

    def test_list_agents(self):
        """Test listing agents."""
        config1 = AgentConfig(agent_type=AgentType.CLAUDE, name="agent1", description="Agent 1")
        config2 = AgentConfig(agent_type=AgentType.GEMINI, name="agent2", description="Agent 2")

        self.registry.create_agent(config1)
        self.registry.create_agent(config2)

        agents = self.registry.list_agents()
        assert len(agents) == 2
        assert "agent1" in agents
        assert "agent2" in agents

    def test_create_agent(self):
        """Test creating agents via registry."""
        config = AgentConfig(
            agent_type=AgentType.CLAUDE,
            name="claude-test",
            description="Claude test",
        )

        agent = self.registry.create_agent(config)
        assert agent is not None
        assert agent.name == "claude-test"
        assert isinstance(agent, ClaudeAgent)

        # Verify registered
        assert self.registry.get("claude-test") is not None


class TestBaseAgent:
    """Test base agent functionality."""

    def test_claude_agent(self):
        """Test ClaudeAgent creation."""
        config = AgentConfig(
            agent_type=AgentType.CLAUDE,
            name="claude-agent",
            description="Claude agent",
        )
        agent = ClaudeAgent(config)
        assert agent.name == "claude-agent"
        assert agent.agent_type == AgentType.CLAUDE

    def test_gemini_agent(self):
        """Test GeminiAgent creation."""
        config = AgentConfig(
            agent_type=AgentType.GEMINI,
            name="gemini-agent",
            description="Gemini agent",
        )
        agent = GeminiAgent(config)
        assert agent.name == "gemini-agent"
        assert agent.agent_type == AgentType.GEMINI

    def test_qwen_agent(self):
        """Test QwenAgent creation."""
        config = AgentConfig(
            agent_type=AgentType.QWEN,
            name="qwen-agent",
            description="Qwen agent",
        )
        agent = QwenAgent(config)
        assert agent.name == "qwen-agent"
        assert agent.agent_type == AgentType.QWEN

    def test_codex_agent(self):
        """Test CodexAgent creation."""
        config = AgentConfig(
            agent_type=AgentType.CODEX,
            name="codex-agent",
            description="Codex agent",
        )
        agent = CodexAgent(config)
        assert agent.name == "codex-agent"
        assert agent.agent_type == AgentType.CODEX

    def test_opencode_agent(self):
        """Test OpencodeAgent creation."""
        config = AgentConfig(
            agent_type=AgentType.OPENCODE,
            name="opencode-agent",
            description="Opencode agent",
        )
        agent = OpencodeAgent(config)
        assert agent.name == "opencode-agent"
        assert agent.agent_type == AgentType.OPENCODE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
