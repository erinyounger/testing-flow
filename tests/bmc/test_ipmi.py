"""
Unit tests for IPMI tests.
"""

import pytest
from src.layers.bmc.ipmi import IpmiTests, MockIpmiClient


class TestIpmiTests:
    """Tests for IpmiTests class."""

    @pytest.fixture
    def ipmi_tests(self):
        """Create IpmiTests instance with mock client."""
        return IpmiTests(MockIpmiClient())

    def test_sensor_reading_validation_success(self, ipmi_tests):
        """Test sensor reading validation passes."""
        result = ipmi_tests.sensor_reading_validation()
        assert result["passed"] is True
        assert "sensors_tested" in result["data"]

    def test_sdr_dump_parsing_success(self, ipmi_tests):
        """Test SDR dump parsing passes."""
        result = ipmi_tests.sdr_dump_parsing()
        assert result["passed"] is True
        assert "sdr_entries" in result["data"]

    def test_sel_listing_success(self, ipmi_tests):
        """Test SEL listing passes."""
        result = ipmi_tests.sel_listing()
        assert result["passed"] is True
        assert "sel_entries" in result["data"]

    def test_raw_command_execution_success(self, ipmi_tests):
        """Test raw command execution passes."""
        result = ipmi_tests.raw_command_execution()
        assert result["passed"] is True
        assert "response_length" in result["data"]

    def test_user_management_success(self, ipmi_tests):
        """Test user management passes."""
        result = ipmi_tests.user_management()
        assert result["passed"] is True

    def test_run_tests_all_pass(self, ipmi_tests):
        """Test run_tests returns aggregate results."""
        results = ipmi_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0


class TestMockIpmiClient:
    """Tests for MockIpmiClient."""

    def test_connection(self):
        """Test mock client connection."""
        client = MockIpmiClient()
        assert client.connect() is True
        assert client.is_connected() is True

    def test_disconnect(self):
        """Test mock client disconnect."""
        client = MockIpmiClient()
        client.disconnect()
        assert client.is_connected() is False

    def test_get_sensor_reading(self):
        """Test get sensor reading."""
        client = MockIpmiClient()
        temp = client.get_sensor_reading("CPU Temp")
        assert temp == 45.0

    def test_get_sdr(self):
        """Test get SDR."""
        client = MockIpmiClient()
        sdr = client.get_sdr()
        assert isinstance(sdr, dict)
        assert len(sdr) > 0

    def test_get_sel(self):
        """Test get SEL."""
        client = MockIpmiClient()
        sel = client.get_sel()
        assert isinstance(sel, list)

    def test_run_raw_command(self):
        """Test run raw command."""
        client = MockIpmiClient()
        response = client.run_raw_command(0x06, 0x01)
        assert response is not None
        assert len(response) > 0
