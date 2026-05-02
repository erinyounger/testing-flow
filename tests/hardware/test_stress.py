"""
Unit tests for stress tests.
"""

import pytest
from src.layers.hardware.stress import StressTests
from src.layers.hardware.layer import MockHardwareApi


class TestStressTests:
    """Tests for StressTests class."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock hardware API."""
        return MockHardwareApi()

    @pytest.fixture
    def stress_tests(self, mock_api):
        """Create StressTests instance with mock API."""
        return StressTests(mock_api)

    def test_cpu_stress_success(self, stress_tests):
        """Test CPU stress runs successfully."""
        result = stress_tests.cpu_stress(cores=2, duration_seconds=1)
        assert result["passed"] is True
        assert result["data"]["cores"] == 2

    def test_cpu_stress_invalid_duration(self, stress_tests):
        """Test CPU stress fails with invalid duration."""
        result = stress_tests.cpu_stress(cores=2, duration_seconds=0)
        assert result["passed"] is False

    def test_memory_stress_success(self, stress_tests):
        """Test memory stress runs successfully."""
        result = stress_tests.memory_stress(percent=50, duration_seconds=1)
        assert result["passed"] is True
        assert result["data"]["percent"] == 50

    def test_memory_stress_invalid_percent(self, stress_tests):
        """Test memory stress fails with invalid percent."""
        result = stress_tests.memory_stress(percent=0, duration_seconds=1)
        assert result["passed"] is False
        result = stress_tests.memory_stress(percent=101, duration_seconds=1)
        assert result["passed"] is False

    def test_io_stress_success(self, stress_tests):
        """Test IO stress runs successfully."""
        result = stress_tests.io_stress(size_mb=100, duration_seconds=1)
        assert result["passed"] is True
        assert result["data"]["size_mb"] == 100

    def test_io_stress_invalid_size(self, stress_tests):
        """Test IO stress fails with invalid size."""
        result = stress_tests.io_stress(size_mb=0, duration_seconds=1)
        assert result["passed"] is False

    def test_run_tests_all_pass(self, stress_tests):
        """Test run_tests returns aggregate results."""
        results = stress_tests.run_tests()
        assert results["total"] == 3
        assert results["passed"] == 3
        assert results["failed"] == 0

    def test_stop_all(self, stress_tests):
        """Test stop_all does not raise."""
        stress_tests.stop_all()
        # Should complete without error
