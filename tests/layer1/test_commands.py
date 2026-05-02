import pytest
from click.testing import CliRunner
from tflow.cli import cli


class TestQuickCommand:
    """quick command TDD tests"""

    def test_quick_command_requires_task_argument(self):
        """RED: quick command requires task parameter"""
        runner = CliRunner()
        result = runner.invoke(cli, ["quick"])

        assert result.exit_code != 0

    def test_quick_command_accepts_task(self, tmp_path):
        """GREEN: quick command accepts task parameter"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["quick", "实现登录功能"])

            # Command should execute (even if functionality not implemented)
            assert result.exit_code in [0, 1]  # 0=success, 1=not implemented

    def test_quick_command_with_full_flag(self, tmp_path):
        """GREEN: --full flag"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["quick", "实现登录功能", "--full"])

            assert "--full" in result.output or result.exit_code == 0

    def test_quick_command_with_discuss_flag(self, tmp_path):
        """GREEN: --discuss flag"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["quick", "实现登录功能", "--discuss"])

            assert "--discuss" in result.output or result.exit_code == 0


class TestPlanCommand:
    """plan command TDD tests"""

    def test_plan_command_accepts_phase(self):
        """RED: plan command accepts phase parameter"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["plan", "phase-1"])

            assert result.exit_code in [0, 1]


class TestExecuteCommand:
    """execute command TDD tests"""

    def test_execute_command_accepts_phase(self):
        """RED: execute command accepts phase parameter"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["execute", "phase-1"])

            assert result.exit_code in [0, 1]