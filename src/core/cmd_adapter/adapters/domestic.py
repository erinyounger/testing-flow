"""
Domestic OS command adapter.

Adapters for Chinese domestic OS distributions.
"""

from src.core.cmd_adapter.adapter import CommandAdapter, CommandResult
from src.core.cmd_adapter.adapters.linux import GenericLinuxAdapter


class DomesticOSAdapter(GenericLinuxAdapter):
    """
    Command adapter for Chinese domestic OS distributions.

    Extends GenericLinuxAdapter with OS-specific command overrides
    for distributions like Ubuntu Kylin, Deepin, Anolis, StartOS, etc.
    """

    @property
    def os_id(self) -> str:
        return "domestic"

    @property
    def name(self) -> str:
        return "Domestic OS Adapter (Chinese Distributions)"

    def get_supported_commands(self) -> list:
        base_commands = super().get_supported_commands()
        return base_commands + ["deepin_version", "kylin_version", "anolis_version", "startos_info"]

    def execute(self, cmd_name: str, **kwargs) -> CommandResult:
        """Execute a command with domestic OS-specific handling."""
        if cmd_name == "deepin_version":
            return self._cmd_deepin_version(**kwargs)
        elif cmd_name == "kylin_version":
            return self._cmd_kylin_version(**kwargs)
        elif cmd_name == "anolis_version":
            return self._cmd_anolis_version(**kwargs)
        elif cmd_name == "startos_info":
            return self._cmd_startos_info(**kwargs)
        return super().execute(cmd_name, **kwargs)

    def _cmd_deepin_version(self, **kwargs) -> CommandResult:
        """Get Deepin version information."""
        return self._run_command(["deepin-version"])

    def _cmd_kylin_version(self, **kwargs) -> CommandResult:
        """Get Kylin version information."""
        return self._run_command(["cat", "/etc/kylin-release"])

    def _cmd_anolis_version(self, **kwargs) -> CommandResult:
        """Get Anolis version information."""
        return self._run_command(["cat", "/etc/anolis-release"])

    def _cmd_startos_info(self, **kwargs) -> CommandResult:
        """Get StartOS information."""
        return self._run_command(["ctl", "sys", "info"])
