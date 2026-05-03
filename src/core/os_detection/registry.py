"""
OS Registry for known distributions.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from src.core.os_detection.models import OSInfo

logger = logging.getLogger(__name__)


class OSRegistry:
    """
    Registry for known OS distributions.

    Maintains a registry of known OS distributions with their metadata.
    Supports loading from YAML configuration and runtime registration.
    """

    def __init__(self):
        self._registry: Dict[str, OSInfo] = {}
        self._config_path: Optional[Path] = None

    def register(self, os_info: OSInfo) -> None:
        """
        Register an OS distribution.

        Args:
            os_info: OS information to register
        """
        self._registry[os_info.id] = os_info
        logger.debug(f"Registered OS: {os_info.id} ({os_info.name})")

    def lookup(self, distro_id: str) -> Optional[OSInfo]:
        """
        Lookup OS info by distro ID.

        Args:
            distro_id: Distribution ID (e.g., 'ubuntu', 'deepin')

        Returns:
            OSInfo if found, None otherwise
        """
        return self._registry.get(distro_id)

    def lookup_by_name(self, name: str) -> Optional[OSInfo]:
        """
        Lookup OS info by name (partial match).

        Args:
            name: OS name to search for

        Returns:
            OSInfo if found, None otherwise
        """
        name_lower = name.lower()
        for os_info in self._registry.values():
            if name_lower in os_info.name.lower() or name_lower in os_info.id.lower():
                return os_info
        return None

    def get_all(self) -> Dict[str, OSInfo]:
        """Return all registered OS distributions."""
        return self._registry.copy()

    def load_config(self, config_path: Path) -> int:
        """
        Load OS registry from YAML configuration.

        Args:
            config_path: Path to YAML config file

        Returns:
            Number of OS entries loaded
        """
        self._config_path = config_path
        count = 0

        if not config_path.exists():
            logger.warning(f"OS config not found: {config_path}")
            return 0

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "os_distributions" not in data:
            logger.warning(f"Invalid OS config format: {config_path}")
            return 0

        for entry in data.get("os_distributions", []):
            try:
                os_info = OSInfo.from_dict(entry)
                self.register(os_info)
                count += 1
            except Exception as e:
                logger.error(f"Failed to parse OS entry: {entry}, error: {e}")

        logger.info(f"Loaded {count} OS distributions from {config_path}")
        return count

    def get_config_path(self) -> Optional[Path]:
        """Return the loaded config path."""
        return self._config_path
