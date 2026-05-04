"""Application settings using Pydantic."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import os


class LogConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


class StorageConfig(BaseModel):
    """Storage configuration."""

    base_dir: str = ".workflow"
    jsonl_dir: Optional[str] = None
    sqlite_db: Optional[str] = None
    max_buffer_size: int = 1000


class Settings(BaseModel):
    """Application settings.

    Loads configuration from environment variables.
    """

    # Application
    app_name: str = "tflow"
    app_version: str = "0.1.0"
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # Workflow
    workflow_dir: str = ".workflow/sessions"
    max_concurrent_workflows: int = 10

    # Logging
    log: LogConfig = Field(default_factory=LogConfig)

    # Storage
    storage: StorageConfig = Field(default_factory=StorageConfig)

    # Agents
    agent_timeout: int = 300
    agent_max_retries: int = 3

    # Realtime
    realtime_heartbeat_interval: int = 30
    realtime_buffer_size: int = 1000

    # Paths
    specs_dir: str = "docs/specs"
    data_dir: str = ".data"

    # Environment
    env: str = Field(default_factory=lambda: os.getenv("TFLOW_ENV", "development"))

    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables.

        Returns:
            Settings instance
        """
        # Collect environment variables with TFLOW_ prefix
        env_config: Dict[str, Any] = {}

        for key, value in os.environ.items():
            if key.startswith("TFLOW_"):
                setting_key = key[6:].lower()  # Remove TFLOW_ prefix
                env_config[setting_key] = value

        return cls(**env_config)

    @classmethod
    def from_file(cls, path: str) -> "Settings":
        """Load settings from a YAML file.

        Args:
            path: Path to settings file

        Returns:
            Settings instance
        """
        try:
            import yaml
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except ImportError:
            raise RuntimeError("PyYAML is required to load settings from file")
        except FileNotFoundError:
            raise FileNotFoundError(f"Settings file not found: {path}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary.

        Returns:
            Settings as dictionary
        """
        return self.model_dump()
