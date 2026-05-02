"""
Unit tests for performance benchmark tests.
"""

import pytest
from src.layers.hardware.performance import PerformanceTests
from src.layers.hardware.layer import MockHardwareApi


class TestPerformanceTests:
    """Tests for PerformanceTests class."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock hardware API."""
        return MockHardwareApi()

    @pytest.fixture
    def performance_tests(self, mock_api):
        """Create PerformanceTests instance with mock API."""
        return PerformanceTests(mock_api)

    def test_cpu_benchmark_success(self, performance_tests):
        """Test CPU benchmark runs successfully."""
        result = performance_tests.cpu_benchmark()
        assert result["passed"] is True
        assert "score" in result["data"]

    def test_memory_bandwidth_success(self, performance_tests):
        """Test memory bandwidth benchmark runs successfully."""
        result = performance_tests.memory_bandwidth()
        assert result["passed"] is True
        assert "bandwidth_gbps" in result["data"]

    def test_disk_throughput_success(self, performance_tests):
        """Test disk throughput benchmark runs successfully."""
        result = performance_tests.disk_throughput()
        assert result["passed"] is True
        assert "read_mbps" in result["data"]
        assert "write_mbps" in result["data"]

    def test_network_latency_success(self, performance_tests):
        """Test network latency benchmark runs successfully."""
        result = performance_tests.network_latency()
        assert result["passed"] is True
        assert "latency_ms" in result["data"]

    def test_run_tests_all_pass(self, performance_tests):
        """Test run_tests returns aggregate results."""
        results = performance_tests.run_tests()
        assert results["total"] == 4
        assert results["passed"] == 4
        assert results["failed"] == 0
