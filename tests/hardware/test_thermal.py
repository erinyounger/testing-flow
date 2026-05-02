"""
Unit tests for thermal monitoring tests.
"""

import pytest
from src.layers.hardware.thermal import ThermalTests
from src.layers.hardware.layer import MockHardwareApi


class TestThermalTests:
    """Tests for ThermalTests class."""

    @pytest.fixture
    def mock_api(self):
        """Create a mock hardware API."""
        return MockHardwareApi()

    @pytest.fixture
    def thermal_tests(self, mock_api):
        """Create ThermalTests instance with mock API."""
        return ThermalTests(mock_api)

    def test_fan_speed_validation_success(self, thermal_tests):
        """Test fan speed validation passes."""
        result = thermal_tests.fan_speed_validation()
        assert result["passed"] is True
        assert "fan_speeds" in result["data"]

    def test_fan_speed_validation_out_of_range(self, thermal_tests, mock_api):
        """Test fan speed validation detects out of range."""
        mock_api._sensors["fan_speed_0"] = 500
        result = thermal_tests.fan_speed_validation()
        assert result["passed"] is False

    def test_fan_speed_validation_no_sensors(self, thermal_tests, mock_api):
        """Test fan speed validation handles no sensors."""
        mock_api._sensors = {}
        result = thermal_tests.fan_speed_validation()
        assert result["passed"] is False

    def test_temperature_sensor_reading_success(self, thermal_tests):
        """Test temperature sensor reading passes."""
        result = thermal_tests.temperature_sensor_reading()
        assert result["passed"] is True
        assert "temperatures" in result["data"]

    def test_temperature_sensor_reading_out_of_range(self, thermal_tests, mock_api):
        """Test temperature sensor reading detects out of range."""
        mock_api._sensors["cpu_temp"] = 150
        result = thermal_tests.temperature_sensor_reading()
        assert result["passed"] is False

    def test_thermal_throttle_detection_success(self, thermal_tests):
        """Test thermal throttle detection passes."""
        result = thermal_tests.thermal_throttle_detection()
        assert result["passed"] is True

    def test_thermal_throttle_detection_high_delta(self, thermal_tests, mock_api):
        """Test thermal throttle detection with high delta."""
        mock_api._sensors["inlet_temp"] = 25
        mock_api._sensors["exhaust_temp"] = 70
        result = thermal_tests.thermal_throttle_detection()
        assert result["passed"] is False

    def test_cooling_efficiency_success(self, thermal_tests):
        """Test cooling efficiency passes."""
        result = thermal_tests.cooling_efficiency()
        assert result["passed"] is True

    def test_run_tests_all_pass(self, thermal_tests):
        """Test run_tests returns aggregate results."""
        results = thermal_tests.run_tests()
        assert results["total"] == 4
        assert results["passed"] == 4
        assert results["failed"] == 0
