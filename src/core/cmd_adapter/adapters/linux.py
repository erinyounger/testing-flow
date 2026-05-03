"""
Generic Linux command adapter.
"""

import platform
import subprocess
from typing import Any, Dict, List

from src.core.cmd_adapter.adapter import CommandAdapter, CommandResult


class GenericLinuxAdapter(CommandAdapter):
    """
    Generic Linux command adapter.

    Provides standard Linux commands that work across most distributions.
    """

    @property
    def os_id(self) -> str:
        return "linux"

    @property
    def name(self) -> str:
        return "Generic Linux Adapter"

    def get_supported_commands(self) -> List[str]:
        return [
            "info", "ls", "cat", "df", "du", "free", "uptime",
            "uname", "hostname", "ip", "netstat", "ps", "top",
            "cpu_info", "mem_info", "disk_info", "network_info",
        ]

    def execute(self, cmd_name: str, **kwargs) -> CommandResult:
        """
        Execute a Linux command.

        Args:
            cmd_name: Command name
            **kwargs: Additional arguments

        Returns:
            CommandResult
        """
        command_map = {
            "info": self._cmd_info,
            "ls": self._cmd_ls,
            "cat": self._cmd_cat,
            "df": self._cmd_df,
            "du": self._cmd_du,
            "free": self._cmd_free,
            "uptime": self._cmd_uptime,
            "uname": self._cmd_uname,
            "hostname": self._cmd_hostname,
            "ip": self._cmd_ip,
            "netstat": self._cmd_netstat,
            "ps": self._cmd_ps,
            "top": self._cmd_top,
            "cpu_info": self._cmd_cpu_info,
            "mem_info": self._cmd_mem_info,
            "disk_info": self._cmd_disk_info,
            "network_info": self._cmd_network_info,
        }

        handler = command_map.get(cmd_name)
        if handler:
            return handler(**kwargs)
        return CommandResult(
            success=False,
            stdout="",
            stderr=f"Unknown command: {cmd_name}",
            returncode=-1,
            command=cmd_name,
            error="unknown_command",
        )

    def _cmd_info(self, **kwargs) -> CommandResult:
        """Get system information."""
        import json
        import shutil

        info = {
            "os": "Linux",
            "hostname": self._get_hostname(),
            "kernel": self._get_kernel(),
            "architecture": platform.machine(),
            "python_version": "3",
        }

        # Try to read os-release for more info
        try:
            with open("/etc/os-release", "r") as f:
                for line in f:
                    if "=" in line:
                        key, _, value = line.strip().partition("=")
                        value = value.strip('"')
                        if key in ("NAME", "VERSION", "ID"):
                            info[key.lower()] = value
        except FileNotFoundError:
            pass

        return CommandResult(
            success=True,
            stdout=json.dumps(info, indent=2),
            stderr="",
            returncode=0,
            command="info",
        )

    def _cmd_ls(self, path: str = "/", **kwargs) -> CommandResult:
        """List directory contents."""
        return self._run_command(["ls", "-la", path])

    def _cmd_cat(self, path: str, **kwargs) -> CommandResult:
        """Read file contents."""
        return self._run_command(["cat", path])

    def _cmd_df(self, **kwargs) -> CommandResult:
        """Disk space usage."""
        return self._run_command(["df", "-h"])

    def _cmd_du(self, path: str = "/", **kwargs) -> CommandResult:
        """Disk usage."""
        return self._run_command(["du", "-sh", path])

    def _cmd_free(self, **kwargs) -> CommandResult:
        """Memory usage."""
        return self._run_command(["free", "-h"])

    def _cmd_uptime(self, **kwargs) -> CommandResult:
        """System uptime."""
        return self._run_command(["uptime"])

    def _cmd_uname(self, **kwargs) -> CommandResult:
        """Kernel information."""
        return self._run_command(["uname", "-a"])

    def _cmd_hostname(self, **kwargs) -> CommandResult:
        """Get hostname."""
        return self._run_command(["hostname"])

    def _cmd_ip(self, **kwargs) -> CommandResult:
        """IP address information."""
        return self._run_command(["ip", "addr"])

    def _cmd_netstat(self, **kwargs) -> CommandResult:
        """Network connections."""
        return self._run_command(["netstat", "-tuln"])

    def _cmd_ps(self, **kwargs) -> CommandResult:
        """Process list."""
        return self._run_command(["ps", "aux"])

    def _cmd_top(self, **kwargs) -> CommandResult:
        """Top processes (non-interactive)."""
        return self._run_command(["top", "-bn1"])

    def _cmd_cpu_info(self, **kwargs) -> CommandResult:
        """CPU information."""
        return self._run_command(["cat", "/proc/cpuinfo"])

    def _cmd_mem_info(self, **kwargs) -> CommandResult:
        """Memory information."""
        return self._run_command(["cat", "/proc/meminfo"])

    def _cmd_disk_info(self, **kwargs) -> CommandResult:
        """Disk information."""
        return self._run_command(["lsblk", "-J"])

    def _cmd_network_info(self, **kwargs) -> CommandResult:
        """Network interface information."""
        return self._run_command(["ip", "addr"])

    def _get_hostname(self) -> str:
        try:
            result = subprocess.run(
                ["hostname"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"

    def _get_kernel(self) -> str:
        try:
            result = subprocess.run(
                ["uname", "-r"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"
