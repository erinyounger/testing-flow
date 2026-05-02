import pytest
from tflow.agents.subprocess_agent import SubprocessAgent, ExecResult


class TestSubprocessAgent:
    """SubprocessAgent TDD tests"""

    def test_run_executes_shell_command(self):
        """RED: Execute shell command"""
        agent = SubprocessAgent()
        result = agent.run("echo 'hello'", agent_type="shell")

        assert result.success == True
        assert "hello" in result.output

    def test_run_returns_error_on_failure(self):
        """GREEN: Command failure returns error"""
        agent = SubprocessAgent()
        result = agent.run("exit 1", agent_type="shell")

        assert result.success == False
        assert result.error is not None

    def test_run_respects_timeout(self):
        """GREEN: Timeout control"""
        agent = SubprocessAgent()
        result = agent.run("sleep 10", agent_type="shell", timeout=1)

        assert result.success == False
        assert "Timeout" in result.error

    def test_run_parses_json_output(self):
        """GREEN: Parse JSON output"""
        agent = SubprocessAgent()
        result = agent.run('echo \'{"key": "value"}\'', agent_type="shell")

        assert result.success == True
        parsed = agent.parse_output(result.output)
        assert parsed == {"key": "value"}

    def test_build_command_for_claude(self):
        """GREEN: Build claude command"""
        agent = SubprocessAgent()
        cmd = agent._build_command("test prompt", agent_type="claude")

        assert "claude" in cmd
        assert "test prompt" in cmd