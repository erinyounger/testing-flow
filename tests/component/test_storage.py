"""
Unit tests for storage component tests.
"""

import pytest
from src.layers.component.storage import StorageTests


class TestStorageTests:
    """Tests for StorageTests class."""

    @pytest.fixture
    def storage_tests(self):
        """Create StorageTests instance."""
        return StorageTests()

    def test_drive_detection_success(self, storage_tests):
        """Test drive detection passes."""
        result = storage_tests.drive_detection()
        assert result["passed"] is True
        assert "detected_drives" in result["data"]

    def test_smart_attribute_check_success(self, storage_tests):
        """Test SMART attribute check passes."""
        result = storage_tests.smart_attribute_check()
        assert result["passed"] is True
        assert "smart_data" in result["data"]

    def test_raid_config_validation_success(self, storage_tests):
        """Test RAID configuration validation passes."""
        result = storage_tests.raid_config_validation()
        assert result["passed"] is True
        assert "raid_info" in result["data"]

    def test_fio_benchmark_integration_success(self, storage_tests):
        """Test fio benchmark integration passes."""
        result = storage_tests.fio_benchmark_integration()
        assert result["passed"] is True
        assert "fio_results" in result["data"]

    def test_nvme_namespace_validation_success(self, storage_tests):
        """Test NVMe namespace validation passes."""
        result = storage_tests.nvme_namespace_validation()
        assert result["passed"] is True
        assert "nvme_info" in result["data"]

    def test_run_tests_all_pass(self, storage_tests):
        """Test run_tests returns aggregate results."""
        results = storage_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0
