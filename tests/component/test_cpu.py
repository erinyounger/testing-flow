"""
Unit tests for CPU component tests.
"""

import pytest
from src.layers.component.cpu import CpuTests


class TestCpuTests:
    """Tests for CpuTests class."""

    @pytest.fixture
    def cpu_tests(self):
        """Create CpuTests instance."""
        return CpuTests()

    def test_core_count_validation_success(self, cpu_tests):
        """Test core count validation passes."""
        result = cpu_tests.core_count_validation()
        assert result["passed"] is True
        assert "core_count" in result["data"]

    def test_frequency_check_success(self, cpu_tests):
        """Test frequency check passes."""
        result = cpu_tests.frequency_check()
        assert result["passed"] is True
        assert "base_freq_mhz" in result["data"]

    def test_cache_test_success(self, cpu_tests):
        """Test cache test passes."""
        result = cpu_tests.cache_test()
        assert result["passed"] is True
        assert "cache_info" in result["data"]

    def test_cpu_instruction_support_success(self, cpu_tests):
        """Test instruction support check passes."""
        result = cpu_tests.cpu_instruction_support()
        assert result["passed"] is True
        assert "supported_instructions" in result["data"]

    def test_turbo_boost_verification_success(self, cpu_tests):
        """Test turbo boost verification passes."""
        result = cpu_tests.turbo_boost_verification()
        assert result["passed"] is True
        assert "turbo_boost_enabled" in result["data"]

    def test_run_tests_all_pass(self, cpu_tests):
        """Test run_tests returns aggregate results."""
        results = cpu_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0
