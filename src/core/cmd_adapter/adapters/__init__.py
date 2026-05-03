"""
Command adapters for OS-specific commands.
"""

from src.core.cmd_adapter.adapters.linux import GenericLinuxAdapter
from src.core.cmd_adapter.adapters.domestic import DomesticOSAdapter

__all__ = [
    "GenericLinuxAdapter",
    "DomesticOSAdapter",
]
