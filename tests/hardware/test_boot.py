"""
Unit tests for boot sequence tests.
"""

import pytest
from src.layers.hardware.boot import BootTests
from src.layers.hardware.layer import MockHardwareApi


class TestBootTests:
    """Tests for BootTests class."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock hardware API."""
        return MockHardwareApi()

    @pytest.fixture
    def boot_tests(self, mock_api):
        """Create BootTests instance with mock API."""
        return BootTests(mock_api)

    def test_bios_post_check_success(self, boot_tests, mock_api):
        """Test BIOS POST check passes when power is on."""
        mock_api.power_on()
        result = boot_tests.bios_post_check()
        assert result["passed"] is True

    def test_bios_post_check_power_off(self, boot_tests, mock_api):
        """Test BIOS POST check fails when power is off."""
        mock_api.power_off()
        result = boot_tests.bios_post_check()
        assert result["passed"] is False
        assert "power is off" in result["errors"][0]

    def test_bootloader_verification_success(self, boot_tests, mock_api):
        """Test bootloader verification passes."""
        result = boot_tests.bootloader_verification()
        assert result["passed"] is True
        assert result["data"]["boot_device"] == "disk"

    def test_bootloader_verification_invalid_device(self, boot_tests, mock_api):
        """Test bootloader verification with invalid device."""
        mock_api.set_boot_device("invalid")
        result = boot_tests.bootloader_verification()
        assert result["passed"] is False

    def test_os_boot_timeout_success(self, boot_tests, mock_api):
        """Test OS boot timeout passes when power is on."""
        mock_api.power_on()
        result = boot_tests.os_boot_timeout()
        assert result["passed"] is True

    def test_os_boot_timeout_power_off(self, boot_tests, mock_api):
        """Test OS boot timeout fails when power is off."""
        mock_api.power_off()
        result = boot_tests.os_boot_timeout()
        assert result["passed"] is False

    def test_boot_device_order_success(self, boot_tests, mock_api):
        """Test boot device order change."""
        result = boot_tests.boot_device_order()
        assert result["passed"] is True
        assert result["data"]["tested_device"] == "pxe"

    def test_run_tests_all_pass(self, boot_tests, mock_api):
        """Test run_tests returns aggregate results."""
        results = boot_tests.run_tests()
        assert results["total"] == 4
        assert results["passed"] == 4
        assert results["failed"] == 0
