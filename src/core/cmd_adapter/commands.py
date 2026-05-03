"""
Unified command interface for OS-specific commands.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.core.cmd_adapter.adapter import CommandAdapter, CommandRegistry, CommandResult
from src.core.cmd_adapter.adapters.linux import GenericLinuxAdapter
from src.core.cmd_adapter.adapters.domestic import DomesticOSAdapter
from src.core.os_detection.detector import OSDetector
from src.core.os_detection.registry import OSRegistry

logger = logging.getLogger(__name__)

# Global registry instance
_registry: Optional[CommandRegistry] = None
_detector: Optional[OSDetector] = None


def _get_registry() -> CommandRegistry:
    """Get or create the global command registry."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
        _init_registry(_registry)
    return _registry


def _get_detector() -> OSDetector:
    """Get or create the global OS detector."""
    global _detector
    if _detector is None:
        _detector = OSDetector()
    return _detector


def _init_registry(registry: CommandRegistry) -> None:
    """
    Initialize command registry with built-in adapters.

    Args:
        registry: Command registry to initialize
    """
    # Register generic Linux adapter
    generic_adapter = GenericLinuxAdapter()
    registry.set_generic_adapter(generic_adapter)
    registry.register(generic_adapter)

    # Register domestic OS adapter
    domestic_adapter = DomesticOSAdapter()
    registry.register(domestic_adapter)

    # Load YAML configuration for command overrides
    config_path = Path(__file__).parent / "commands.yaml"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if config and "command_overrides" in config:
                    registry.load_command_overrides(config["command_overrides"])
                if config and "default_os" in config:
                    default_os = config["default_os"]
                    registry.set_os(default_os)
                    logger.info(f"Default OS set to: {default_os}")
        except Exception as e:
            logger.error(f"Failed to load commands.yaml: {e}")


def init_with_os_detection() -> None:
    """Initialize command registry with OS detection."""
    detector = _get_detector()
    result = detector.detect()
    registry = _get_registry()
    registry.set_os(result.os_info.id)
    logger.info(f"Command registry initialized for OS: {result.os_info.id}")


def set_os(os_id: str) -> None:
    """
    Set the OS for command routing.

    Args:
        os_id: OS identifier (e.g., 'ubuntu', 'deepin', 'anolis')
    """
    registry = _get_registry()
    registry.set_os(os_id)


def os_cmd(cmd_name: str, **kwargs) -> CommandResult:
    """
    Execute a unified command through the appropriate OS adapter.

    Args:
        cmd_name: Command name (e.g., 'info', 'ls', 'df', 'cpu_info')
        **kwargs: Additional arguments for the command

    Returns:
        CommandResult with execution outcome

    Examples:
        >>> result = os_cmd('info')
        >>> print(result.stdout)
        >>> result = os_cmd('df', path='/home')
    """
    registry = _get_registry()
    return registry.execute(cmd_name, **kwargs)


def get_os_info() -> Dict[str, Any]:
    """
    Get OS information through the info command.

    Returns:
        Dict with OS information
    """
    result = os_cmd("info")
    if result.success:
        import json
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw": result.stdout}
    return {"error": result.stderr}
