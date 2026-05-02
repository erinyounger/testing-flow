"""
Unit tests for BIOS configuration tests.
"""

import pytest
from src.layers.bmc.bios_config import BiosConfigTests


class TestBiosConfigTests:
    """Tests for BiosConfigTests class."""

    @pytest.fixture
    def bios_config_tests(self):
        """Create BiosConfigTests instance."""
        return BiosConfigTests()

    def test_setting_enumeration_success(self, bios_config_tests):
        """Test setting enumeration passes."""
        result = bios_config_tests.setting_enumeration()
        assert result["passed"] is True
        assert "settings_count" in result["data"]

    def test_setting_value_validation_success(self, bios_config_tests):
        """Test setting value validation passes."""
        result = bios_config_tests.setting_value_validation()
        assert result["passed"] is True
        assert "validated_settings" in result["data"]

    def test_profile_export_import_success(self, bios_config_tests):
        """Test profile export/import passes."""
        result = bios_config_tests.profile_export_import()
        assert result["passed"] is True
        assert "profile_name" in result["data"]

    def test_secure_boot_status_success(self, bios_config_tests):
        """Test secure boot status passes."""
        result = bios_config_tests.secure_boot_status()
        assert result["passed"] is True
        assert "secure_boot" in result["data"]

    def test_tpm_status_success(self, bios_config_tests):
        """Test TPM status passes."""
        result = bios_config_tests.tpm_status()
        assert result["passed"] is True
        assert "tpm" in result["data"]

    def test_run_tests_all_pass(self, bios_config_tests):
        """Test run_tests returns aggregate results."""
        results = bios_config_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0
