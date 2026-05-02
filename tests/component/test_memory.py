"""
Unit tests for memory component tests.
"""

import pytest
from src.layers.component.memory import MemoryTests


class TestMemoryTests:
    """Tests for MemoryTests class."""

    @pytest.fixture
    def memory_tests(self):
        """Create MemoryTests instance."""
        return MemoryTests()

    def test_capacity_verification_success(self, memory_tests):
        """Test capacity verification passes."""
        result = memory_tests.capacity_verification()
        assert result["passed"] is True
        assert "total_memory_gb" in result["data"]

    def test_ecc_support_check_success(self, memory_tests):
        """Test ECC support check passes."""
        result = memory_tests.ecc_support_check()
        assert result["passed"] is True
        assert "ecc_enabled" in result["data"]

    def test_memory_stress_patterns_success(self, memory_tests):
        """Test memory stress patterns passes."""
        result = memory_tests.memory_stress_patterns()
        assert result["passed"] is True
        assert "test_patterns" in result["data"]

    def test_error_injection_handling_success(self, memory_tests):
        """Test error injection handling passes."""
        result = memory_tests.error_injection_handling()
        assert result["passed"] is True

    def test_memory_bandwidth_measurement_success(self, memory_tests):
        """Test memory bandwidth measurement passes."""
        result = memory_tests.memory_bandwidth_measurement()
        assert result["passed"] is True
        assert "bandwidth_gbps" in result["data"]

    def test_run_tests_all_pass(self, memory_tests):
        """Test run_tests returns aggregate results."""
        results = memory_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0
