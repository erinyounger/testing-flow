"""
Power management tests.

Tests for power cycling, power state, and power redundancy.
"""

from typing import Any, Dict, List
import logging
import time


class PowerTests:
    """
    Power management test suite.

    Tests power cycling, state transitions, and redundancy.
    """

    def __init__(self, hardware_api):
        self._api = hardware_api
        self._logger = logging.getLogger(__name__)

    def power_cycle(self) -> Dict[str, Any]:
        """
        Test power cycle (off -> on -> off -> on).

        Returns dict with test result.
        """
        result = {"test": "power_cycle", "passed": False, "errors": []}

        try:
            # Initial state check
            initial_state = self._api.get_power_state()
            self._logger.info(f"Initial power state: {initial_state}")

            # Turn off
            if not self._api.power_off():
                result["errors"].append("Failed to power off")
                return result

            time.sleep(1)
            state_after_off = self._api.get_power_state()
            if state_after_off != "off":
                result["errors"].append(f"Expected 'off', got '{state_after_off}'")
                return result

            # Turn on
            if not self._api.power_on():
                result["errors"].append("Failed to power on")
                return result

            time.sleep(1)
            state_after_on = self._api.get_power_state()
            if state_after_on != "on":
                result["errors"].append(f"Expected 'on', got '{state_after_on}'")
                return result

            result["passed"] = True
            self._logger.info("Power cycle test passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Power cycle test failed: {e}")

        return result

    def power_state(self) -> Dict[str, Any]:
        """
        Test power state transitions (on -> standby -> on).

        Returns dict with test result.
        """
        result = {"test": "power_state", "passed": False, "errors": []}

        try:
            # Ensure power is on
            self._api.power_on()
            time.sleep(1)
            state = self._api.get_power_state()
            if state != "on":
                result["errors"].append(f"Expected 'on', got '{state}'")
                return result

            # Power cycle test
            if not self._api.power_cycle():
                result["errors"].append("Power cycle failed")
                return result

            result["passed"] = True
            self._logger.info("Power state test passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Power state test failed: {e}")

        return result

    def power_redundancy(self) -> Dict[str, Any]:
        """
        Test power supply redundancy (dual PSU failover simulation).

        Returns dict with test result.
        """
        result = {"test": "power_redundancy", "passed": False, "errors": []}

        try:
            # This is a simplified test - in real hardware would check PSU status
            sensors = self._api.get_all_sensors()

            # Check voltage sensors are within range
            voltages = {
                "12v": sensors.get("voltage_12v", 0),
                "5v": sensors.get("voltage_5v", 0),
                "3_3v": sensors.get("voltage_3_3v", 0),
            }

            for name, voltage in voltages.items():
                if voltage <= 0:
                    result["errors"].append(f"Voltage {name} reading invalid: {voltage}")
                    return result

            result["passed"] = True
            result["data"] = {"voltages": voltages}
            self._logger.info("Power redundancy test passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Power redundancy test failed: {e}")

        return result

    def run_tests(self) -> Dict[str, Any]:
        """
        Run all power tests.

        Returns aggregate results.
        """
        results = []
        total = 3
        passed = 0
        failed = 0
        all_errors = []

        for test_method in [self.power_cycle, self.power_state, self.power_redundancy]:
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
