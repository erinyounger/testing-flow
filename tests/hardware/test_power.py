"""
Unit tests for power management tests.
"""

import pytest
from src.layers.hardware.power import PowerTests
from src.layers.hardware.layer import MockHardwareApi


class TestPowerTests:
    """Tests for PowerTests class."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock hardware API."""
        return MockHardwareApi()

    @pytest.fixture
    def power_tests(self, mock_api):
        """Create PowerTests instance with mock API."""
        return PowerTests(mock_api)

    def test_power_cycle_success(self, power_tests, mock_api):
        """Test power cycle executes successfully."""
        result = power_tests.power_cycle()
        assert result["passed"] is True
        assert mock_api.get_power_state() == "on"

    def test_power_cycle_off_phase(self, power_tests, mock_api):
        """Test power cycle includes off phase."""
        mock_api.power_off()
        assert mock_api.get_power_state() == "off"

    def test_power_state_on_to_on(self, power_tests, mock_api):
        """Test power state transitions."""
        result = power_tests.power_state()
        assert result["passed"] is True

    def test_power_redundancy_voltage_check(self, power_tests, mock_api):
        """Test power redundancy checks voltages."""
        result = power_tests.power_redundancy()
        assert result["passed"] is True
        assert "voltages" in result["data"]

    def test_power_redundancy_invalid_voltage(self, power_tests, mock_api):
        """Test power redundancy detects invalid voltage."""
        mock_api._sensors["voltage_12v"] = 0
        result = power_tests.power_redundancy()
        assert result["passed"] is False
        assert len(result["errors"]) > 0

    def test_run_tests_all_pass(self, power_tests):
        """Test run_tests returns aggregate results."""
        results = power_tests.run_tests()
        assert results["total"] == 3
        assert results["passed"] == 3
        assert results["failed"] == 0


class TestMockHardwareApi:
    """Tests for MockHardwareApi."""

    def test_initial_power_state(self):
        """Test initial power state is on."""
        api = MockHardwareApi()
        assert api.get_power_state() == "on"

    def test_power_cycle(self):
        """Test power cycle changes state."""
        api = MockHardwareApi()
        api.power_off()
        assert api.get_power_state() == "off"
        api.power_on()
        assert api.get_power_state() == "on"

    def test_power_on(self):
        """Test power on."""
        api = MockHardwareApi()
        api.power_off()
        api.power_on()
        assert api.get_power_state() == "on"

    def test_power_off(self):
        """Test power off."""
        api = MockHardwareApi()
        api.power_off()
        assert api.get_power_state() == "off"

    def test_get_boot_device(self):
        """Test get boot device."""
        api = MockHardwareApi()
        assert api.get_boot_device() == "disk"

    def test_set_boot_device(self):
        """Test set boot device."""
        api = MockHardwareApi()
        result = api.set_boot_device("pxe")
        assert result is True
        assert api.get_boot_device() == "pxe"

    def test_read_sensor(self):
        """Test read sensor."""
        api = MockHardwareApi()
        temp = api.read_sensor("cpu_temp")
        assert temp == 45.0

    def test_read_invalid_sensor(self):
        """Test read invalid sensor returns 0."""
        api = MockHardwareApi()
        temp = api.read_sensor("invalid_sensor")
        assert temp == 0.0

    def test_get_all_sensors(self):
        """Test get all sensors."""
        api = MockHardwareApi()
        sensors = api.get_all_sensors()
        assert "cpu_temp" in sensors
        assert "fan_speed_0" in sensors
