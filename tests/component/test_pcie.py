"""
Unit tests for PCIe component tests.
"""

import pytest
from src.layers.component.pcie import PCIeTests


class TestPCIeTests:
    """Tests for PCIeTests class."""

    @pytest.fixture
    def pcie_tests(self):
        """Create PCIeTests instance."""
        return PCIeTests()

    def test_device_enumeration_success(self, pcie_tests):
        """Test device enumeration passes."""
        result = pcie_tests.device_enumeration()
        assert result["passed"] is True
        assert "devices" in result["data"]

    def test_slot_bandwidth_success(self, pcie_tests):
        """Test slot bandwidth passes."""
        result = pcie_tests.slot_bandwidth()
        assert result["passed"] is True
        assert "slot_info" in result["data"]

    def test_endpoint_bar_validation_success(self, pcie_tests):
        """Test endpoint BAR validation passes."""
        result = pcie_tests.endpoint_bar_validation()
        assert result["passed"] is True
        assert "bar_info" in result["data"]

    def test_correctable_error_counting_success(self, pcie_tests):
        """Test correctable error counting passes."""
        result = pcie_tests.correctable_error_counting()
        assert result["passed"] is True
        assert "error_counts" in result["data"]

    def test_run_tests_all_pass(self, pcie_tests):
        """Test run_tests returns aggregate results."""
        results = pcie_tests.run_tests()
        assert results["total"] == 4
        assert results["passed"] == 4
        assert results["failed"] == 0
