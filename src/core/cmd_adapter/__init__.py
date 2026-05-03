"""
Command Adapter Layer & YAML Integration

Unified command interface with OS-specific adapters.
"""

from src.core.cmd_adapter.adapter import CommandAdapter, CommandRegistry
from src.core.cmd_adapter.commands import os_cmd

__all__ = [
    "CommandAdapter",
    "CommandRegistry",
    "os_cmd",
]
