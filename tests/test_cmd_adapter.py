"""
Unit tests for Command Adapter Layer.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.core.cmd_adapter.adapter import CommandAdapter, CommandRegistry, CommandResult
from src.core.cmd_adapter.adapters.linux import GenericLinuxAdapter
from src.core.cmd_adapter.adapters.domestic import DomesticOSAdapter
from src.core.cmd_adapter import commands


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_success(self):
        result = CommandResult(
            success=True,
            stdout="output",
            stderr="",
            returncode=0,
            command="ls",
        )
        assert result.success is True
        assert result.stdout == "output"
        assert result.returncode == 0

    def test_command_result_failure(self):
        result = CommandResult(
            success=False,
            stdout="",
            stderr="error",
            returncode=1,
            command="ls",
            error="permission denied",
        )
        assert result.success is False
        assert result.error == "permission denied"

    def test_to_dict(self):
        result = CommandResult(
            success=True,
            stdout="test",
            stderr="",
            returncode=0,
            command="echo",
        )
        d = result.to_dict()
        assert d["success"] is True
        assert d["command"] == "echo"


class TestCommandAdapter:
    """Tests for CommandAdapter abstract class."""

    def test_generic_linux_adapter_properties(self):
        adapter = GenericLinuxAdapter()
        assert adapter.os_id == "linux"
        assert adapter.name == "Generic Linux Adapter"

    def test_domestic_adapter_properties(self):
        adapter = DomesticOSAdapter()
        assert adapter.os_id == "domestic"
        assert "Domestic" in adapter.name

    def test_generic_adapter_supported_commands(self):
        adapter = GenericLinuxAdapter()
        commands_list = adapter.get_supported_commands()
        assert "info" in commands_list
        assert "ls" in commands_list
        assert "df" in commands_list
        assert "cpu_info" in commands_list

    def test_domestic_adapter_extended_commands(self):
        adapter = DomesticOSAdapter()
        commands_list = adapter.get_supported_commands()
        assert "deepin_version" in commands_list
        assert "kylin_version" in commands_list


class TestCommandRegistry:
    """Tests for CommandRegistry."""

    def test_registry_register(self):
        registry = CommandRegistry()
        adapter = GenericLinuxAdapter()
        registry.register(adapter)
        # Verify adapter is registered by getting it
        registry.set_os(adapter.os_id)
        retrieved = registry.get_adapter()
        assert retrieved is adapter

    def test_registry_set_os(self):
        registry = CommandRegistry()
        registry.set_os("ubuntu")
        assert registry.get_current_os() == "ubuntu"

    def test_registry_get_adapter(self):
        registry = CommandRegistry()
        adapter = GenericLinuxAdapter()
        registry.register(adapter)
        registry.set_os("linux")
        retrieved = registry.get_adapter()
        assert retrieved is adapter

    def test_registry_fallback_to_generic(self):
        registry = CommandRegistry()
        generic = GenericLinuxAdapter()
        registry.set_generic_adapter(generic)
        registry.set_os("unknown-os")
        retrieved = registry.get_adapter()
        assert retrieved is generic

    def test_registry_no_adapter_available(self):
        registry = CommandRegistry()
        # Don't set generic adapter
        result = registry.execute("test")
        assert result.success is False
        assert "no_adapter" in result.error


class TestGenericLinuxAdapter:
    """Tests for GenericLinuxAdapter command execution."""

    def test_info_command(self):
        adapter = GenericLinuxAdapter()
        result = adapter.execute("info")
        # Info should succeed even without real /etc/os-release in test
        assert result.command == "info"

    def test_unknown_command(self):
        adapter = GenericLinuxAdapter()
        result = adapter.execute("nonexistent_command")
        assert result.success is False
        assert "unknown_command" in result.error

    @patch("subprocess.run")
    def test_ls_command(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="total 64\ndrwxr-xr-x  2 root root 4096 May  3 00:00 .",
            stderr="",
        )
        adapter = GenericLinuxAdapter()
        result = adapter.execute("ls", path="/tmp")
        assert result.success is True


class TestDomesticOSAdapter:
    """Tests for DomesticOSAdapter."""

    def test_domestic_inherits_linux_commands(self):
        adapter = DomesticOSAdapter()
        # Should have all Linux commands
        linux_adapter = GenericLinuxAdapter()
        for cmd in linux_adapter.get_supported_commands():
            assert cmd in adapter.get_supported_commands()

    def test_domestic_specific_commands(self):
        adapter = DomesticOSAdapter()
        assert "deepin_version" in adapter.get_supported_commands()
        assert "kylin_version" in adapter.get_supported_commands()


class TestOsCmd:
    """Tests for the os_cmd unified interface."""

    def test_os_cmd_info_returns_structured_result(self):
        result = commands.os_cmd("info")
        assert isinstance(result, CommandResult)
        assert result.command == "info"

    def test_os_cmd_unknown_returns_error(self):
        result = commands.os_cmd("nonexistent_cmd_xyz")
        assert result.success is False

    def test_set_os_changes_routing(self):
        commands.set_os("linux")
        # Should not raise
        result = commands.os_cmd("info")
        assert isinstance(result, CommandResult)


class TestIntegration:
    """Integration tests for command adapter layer."""

    def test_registry_lookup_with_os_detection(self):
        """Test that registry correctly routes to OS-specific adapter."""
        from src.core.os_detection.detector import OSDetector
        from src.core.os_detection.registry import OSRegistry

        os_registry = OSRegistry()
        detector = OSDetector(registry=os_registry)

        # Test with explicit OS from config
        detector.set_explicit_os("ubuntu")
        result = detector.detect()
        assert result.os_info.id == "ubuntu"

    def test_adapter_registration(self):
        """Test that adapters can be registered and retrieved."""
        registry = CommandRegistry()
        adapter = GenericLinuxAdapter()
        registry.register(adapter)
        registry.set_os("linux")

        retrieved = registry.get_adapter()
        assert retrieved is adapter


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
