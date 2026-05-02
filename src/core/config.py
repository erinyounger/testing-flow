"""
Configuration management with YAML support.

Loads configuration from server-test.yaml with environment variable overrides.
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


logger = logging.getLogger(__name__)


class Config:
    """
    Configuration management class.

    Loads from YAML file and supports environment variable overrides.
    Environment variables take precedence over file values.
    """

    DEFAULT_CONFIG_FILE = "server-test.yaml"

    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._config_file: Optional[str] = config_path
        self._logger = logging.getLogger(__name__)

        if config_path:
            self.load(config_path)
        else:
            self._load_default()

    def _load_default(self) -> None:
        """Load default configuration if no file specified."""
        default_path = Path(self.DEFAULT_CONFIG_FILE)
        if default_path.exists():
            self.load(str(default_path))
        else:
            self._config = self._get_defaults()

    def load(self, config_path: str) -> None:
        """
        Load configuration from a YAML file.

        Args:
            config_path: Path to the YAML configuration file
        """
        try:
            with open(config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
            self._config_file = config_path
            self._logger.info(f"Loaded configuration from {config_path}")
            self._apply_env_overrides()
        except FileNotFoundError:
            self._logger.error(f"Configuration file not found: {config_path}")
            self._config = self._get_defaults()
        except yaml.YAMLError as e:
            self._logger.error(f"Failed to parse YAML: {e}")
            self._config = self._get_defaults()

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides.

        Environment variables use prefix SERVER_TEST_ with uppercase keys.
        Example: SERVER_TEST_LOG_LEVEL=debug
        """
        env_prefix = "SERVER_TEST_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                self.set(config_key, self._parse_env_value(value))
                self._logger.debug(f"Override from env: {config_key} = {value}")

    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Boolean
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False

        # Numeric
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass

        # String
        return value

    def _get_defaults(self) -> Dict[str, Any]:
        """Return default configuration values."""
        return {
            "log_level": "INFO",
            "layers": {
                "hardware": {"enabled": True, "timeout": 3600},
                "component": {"enabled": True, "timeout": 1800},
                "bmc": {"enabled": True, "timeout": 1800},
            },
            "plugins": {
                "enabled": [],
                "discovery": True,
            },
            "hardware": {
                "ipmi_host": "192.168.1.1",
                "ipmi_user": "admin",
                "ipmi_password": "",
                "bmc_host": "192.168.1.2",
                "bmc_user": "admin",
                "bmc_password": "",
            },
            "test": {
                "output_dir": "test-results",
                "parallel_workers": 4,
                "retry_count": 0,
            },
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'layers.hardware.enabled')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value by dot-notation key.

        Args:
            key: Configuration key (e.g., 'layers.hardware.enabled')
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def get_layer_config(self, layer_name: str) -> Dict[str, Any]:
        """Get configuration for a specific layer."""
        return self.get(f"layers.{layer_name}", {})

    def is_layer_enabled(self, layer_name: str) -> bool:
        """Check if a layer is enabled."""
        return self.get(f"layers.{layer_name}.enabled", True)

    def get_hardware_config(self) -> Dict[str, Any]:
        """Get hardware configuration."""
        return self.get("hardware", {})

    def get_plugin_config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self.get("plugins", {})

    def get_test_config(self) -> Dict[str, Any]:
        """Get test execution configuration."""
        return self.get("test", {})

    def to_dict(self) -> Dict[str, Any]:
        """Return configuration as dictionary."""
        return self._config.copy()

    def save(self, config_path: Optional[str] = None) -> None:
        """
        Save configuration to a YAML file.

        Args:
            config_path: Path to save to (uses current path if None)
        """
        path = config_path or self._config_file
        if not path:
            raise ValueError("No configuration file path specified")

        with open(path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False)
        self._logger.info(f"Saved configuration to {path}")


def load_config(config_path: Optional[str] = None) -> Config:
    """Load a configuration from file or defaults."""
    return Config(config_path)
