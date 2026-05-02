"""
Unit tests for firmware update tests.
"""

import pytest
from src.layers.bmc.firmware import FirmwareTests


class TestFirmwareTests:
    """Tests for FirmwareTests class."""

    @pytest.fixture
    def firmware_tests(self):
        """Create FirmwareTests instance."""
        return FirmwareTests()

    def test_flash_progress_tracking_success(self, firmware_tests):
        """Test flash progress tracking passes."""
        result = firmware_tests.flash_progress_tracking()
        assert result["passed"] is True
        assert "flash_progress_percent" in result["data"]
        assert result["data"]["flash_progress_percent"] == 100

    def test_rollback_detection_success(self, firmware_tests):
        """Test rollback detection passes."""
        result = firmware_tests.rollback_detection()
        assert result["passed"] is True
        assert "rollback_detected" in result["data"]
        assert result["data"]["rollback_detected"] is False

    def test_bic_update_validation_success(self, firmware_tests):
        """Test BIC update validation passes."""
        result = firmware_tests.bic_update_validation()
        assert result["passed"] is True
        assert "bic_version_after" in result["data"]

    def test_bios_update_with_recovery_success(self, firmware_tests):
        """Test BIOS update with recovery passes."""
        result = firmware_tests.bios_update_with_recovery()
        assert result["passed"] is True
        assert result["data"]["update_complete"] is True

    def test_version_verification_post_update_success(self, firmware_tests):
        """Test version verification post update passes."""
        result = firmware_tests.version_verification_post_update()
        assert result["passed"] is True
        assert "version" in result["data"]
        assert result["data"]["major"] == 3

    def test_run_tests_all_pass(self, firmware_tests):
        """Test run_tests returns aggregate results."""
        results = firmware_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0
