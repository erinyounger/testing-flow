"""
Unit tests for network component tests.
"""

import pytest
from src.layers.component.network import NetworkTests


class TestNetworkTests:
    """Tests for NetworkTests class."""

    @pytest.fixture
    def network_tests(self):
        """Create NetworkTests instance."""
        return NetworkTests()

    def test_interface_enumeration_success(self, network_tests):
        """Test interface enumeration passes."""
        result = network_tests.interface_enumeration()
        assert result["passed"] is True
        assert "interfaces" in result["data"]

    def test_link_speed_detection_success(self, network_tests):
        """Test link speed detection passes."""
        result = network_tests.link_speed_detection()
        assert result["passed"] is True
        assert "link_speeds" in result["data"]

    def test_throughput_test_success(self, network_tests):
        """Test throughput test passes."""
        result = network_tests.throughput_test()
        assert result["passed"] is True
        assert "throughput" in result["data"]

    def test_offload_capabilities_success(self, network_tests):
        """Test offload capabilities passes."""
        result = network_tests.offload_capabilities()
        assert result["passed"] is True
        assert "offload_features" in result["data"]

    def test_vlan_configuration_success(self, network_tests):
        """Test VLAN configuration passes."""
        result = network_tests.vlan_configuration()
        assert result["passed"] is True
        assert "vlan_config" in result["data"]

    def test_run_tests_all_pass(self, network_tests):
        """Test run_tests returns aggregate results."""
        results = network_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0
