"""
Thermal monitoring and fan control tests.

Tests for fan speeds, temperature readings, and cooling efficiency.
"""

from typing import Any, Dict
import logging


class ThermalTests:
    """
    Thermal monitoring test suite.

    Tests fan speeds, temperature sensors, and cooling efficiency.
    """

    def __init__(self, hardware_api):
        self._api = hardware_api
        self._logger = logging.getLogger(__name__)

    def fan_speed_validation(self) -> Dict[str, Any]:
        """
        Validate fan speeds are within acceptable range.

        Returns dict with test result.
        """
        result = {"test": "fan_speed_validation", "passed": False, "errors": []}

        try:
            sensors = self._api.get_all_sensors()

            # Check all fan speed sensors
            fan_speeds = {}
            for key, value in sensors.items():
                if "fan_speed" in key:
                    fan_speeds[key] = value

            if not fan_speeds:
                result["errors"].append("No fan speed sensors found")
                return result

            # Validate fan speeds are in reasonable range (1000-10000 RPM)
            for name, speed in fan_speeds.items():
                if speed < 1000 or speed > 10000:
                    result["errors"].append(f"Fan {name} speed out of range: {speed} RPM")
                    return result

            result["passed"] = True
            result["data"] = {"fan_speeds": fan_speeds}
            self._logger.info(f"Fan speed validation passed: {fan_speeds}")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Fan speed validation failed: {e}")

        return result

    def temperature_sensor_reading(self) -> Dict[str, Any]:
        """
        Test temperature sensor readings.

        Returns dict with test result.
        """
        result = {"test": "temperature_sensor_reading", "passed": False, "errors": []}

        try:
            sensors = self._api.get_all_sensors()

            # Find temperature sensors
            temp_sensors = {}
            for key, value in sensors.items():
                if "temp" in key.lower():
                    temp_sensors[key] = value

            if not temp_sensors:
                result["errors"].append("No temperature sensors found")
                return result

            # Validate temperatures are in reasonable range
            for name, temp in temp_sensors.items():
                if temp < -20 or temp > 120:
                    result["errors"].append(f"Temperature {name} out of range: {temp}C")
                    return result

            result["passed"] = True
            result["data"] = {"temperatures": temp_sensors}
            self._logger.info(f"Temperature sensor reading passed: {temp_sensors}")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Temperature sensor reading failed: {e}")

        return result

    def thermal_throttle_detection(self) -> Dict[str, Any]:
        """
        Detect if thermal throttling is occurring.

        Returns dict with test result.
        """
        result = {"test": "thermal_throttle_detection", "passed": False, "errors": []}

        try:
            sensors = self._api.get_all_sensors()

            # Check CPU temperature for throttling indication
            cpu_temp = sensors.get("cpu_temp", 0)
            inlet_temp = sensors.get("inlet_temp", 25)
            exhaust_temp = sensors.get("exhaust_temp", 40)

            # Temperature delta between inlet and exhaust
            temp_delta = exhaust_temp - inlet_temp

            # High delta can indicate thermal issues
            if temp_delta > 30:
                result["errors"].append(f"Temperature delta too high: {temp_delta}C")
                return result

            # Check if CPU is near throttling threshold (90C)
            if cpu_temp > 90:
                result["errors"].append(f"CPU temperature ({cpu_temp}C) exceeds throttling threshold")
                return result

            result["passed"] = True
            result["data"] = {
                "cpu_temp": cpu_temp,
                "inlet_temp": inlet_temp,
                "exhaust_temp": exhaust_temp,
                "temp_delta": temp_delta,
            }
            self._logger.info("Thermal throttle detection passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Thermal throttle detection failed: {e}")

        return result

    def cooling_efficiency(self) -> Dict[str, Any]:
        """
        Test cooling system efficiency.

        Returns dict with test result.
        """
        result = {"test": "cooling_efficiency", "passed": False, "errors": []}

        try:
            sensors = self._api.get_all_sensors()

            inlet_temp = sensors.get("inlet_temp", 25)
            cpu_temp = sensors.get("cpu_temp", 45)

            # Calculate cooling efficiency as temperature rise
            temp_rise = cpu_temp - inlet_temp

            # Excessive temperature rise indicates cooling issues
            if temp_rise > 50:
                result["errors"].append(f"Temperature rise too high: {temp_rise}C")
                return result

            result["passed"] = True
            result["data"] = {
                "inlet_temp": inlet_temp,
                "cpu_temp": cpu_temp,
                "temp_rise": temp_rise,
            }
            self._logger.info(f"Cooling efficiency test passed: temp_rise={temp_rise}C")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Cooling efficiency test failed: {e}")

        return result

    def run_tests(self) -> Dict[str, Any]:
        """
        Run all thermal tests.

        Returns aggregate results.
        """
        results = []
        total = 4
        passed = 0
        failed = 0
        all_errors = []

        for test_method in [
            self.fan_speed_validation,
            self.temperature_sensor_reading,
            self.thermal_throttle_detection,
            self.cooling_efficiency,
        ]:
            test_result = test_method()
            results.append(test_result)
            if test_result["passed"]:
                passed += 1
            else:
                failed += 1
                all_errors.extend(test_result.get("errors", []))

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": all_errors,
            "results": results,
        }
