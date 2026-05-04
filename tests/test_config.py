"""Tests for config settings module."""

import pytest
from tflow.config.settings import Settings, LogConfig, StorageConfig


class TestSettings:
    """Test Settings functionality."""

    def test_settings_creation(self):
        """Test Settings can be created."""
        settings = Settings()
        assert settings is not None

    def test_settings_defaults(self):
        """Test default settings values."""
        settings = Settings()
        assert settings.app_name == "tflow"
        assert settings.debug is False
        assert settings.log.level == "INFO"
        assert settings.storage.base_dir == ".workflow"

    def test_log_config(self):
        """Test LogConfig."""
        log_config = LogConfig(level="DEBUG", format="json")
        assert log_config.level == "DEBUG"
        assert log_config.format == "json"

    def test_storage_config(self):
        """Test StorageConfig."""
        storage_config = StorageConfig(
            base_dir=".tflow/data",
            jsonl_dir=".tflow/data/jsonl",
        )
        assert storage_config.base_dir == ".tflow/data"
        assert storage_config.jsonl_dir == ".tflow/data/jsonl"

    def test_settings_nested_access(self):
        """Test accessing nested config."""
        settings = Settings()
        assert settings.log.level == "INFO"
        assert settings.storage.max_buffer_size == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
