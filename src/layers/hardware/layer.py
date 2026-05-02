"""
HardwareLayer class implementing LayerProtocol.

Tests the server as a complete whole machine system.
"""

from typing import Any, Dict, List
import logging

from src.core.layer import LayerContext, LayerProtocol, LayerResult, TestStatus
from src.layers.hardware.power import PowerTests
from src.layers.hardware.boot import BootTests
from src.layers.hardware.stress import StressTests
from src.layers.hardware.thermal import ThermalTests
from src.layers.hardware.performance import PerformanceTests


class HardwareApiError(Exception):
    """Exception raised by hardware API failures."""
    pass


class HardwareApi:
    """
    Abstract interface for hardware operations.

    Provides a common interface for IPMI, Redfish, or vendor-specific SDKs.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
        self._logger = logging.getLogger(__name__)

    def power_cycle(self) -> bool:
        """Power cycle the server (off -> on)."""
        raise NotImplementedError

    def power_on(self) -> bool:
        """Turn on the server."""
        raise NotImplementedError

    def power_off(self) -> bool:
        """Turn off the server."""
        raise NotImplementedError

    def get_power_state(self) -> str:
        """Get current power state ('on', 'off', 'standby')."""
        raise NotImplementedError

    def get_boot_device(self) -> str:
        """Get current boot device."""
        raise NotImplementedError

    def set_boot_device(self, device: str) -> bool:
        """Set boot device."""
        raise NotImplementedError

    def read_sensor(self, sensor_name: str) -> float:
        """Read a sensor value by name."""
        raise NotImplementedError

    def get_all_sensors(self) -> Dict[str, float]:
        """Get all sensor readings."""
        raise NotImplementedError


class MockHardwareApi(HardwareApi):
    """
    Mock hardware API for testing without real hardware.

    Simulates power states, sensors, and boot sequences.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self._power_state = "on"
        self._boot_device = "disk"
        self._sensors = {
            "cpu_temp": 45.0,
            "memory_temp": 38.0,
            "fan_speed_0": 5000,
            "fan_speed_1": 5100,
            "fan_speed_2": 4900,
            "fan_speed_3": 5200,
            "voltage_12v": 12.1,
            "voltage_5v": 5.0,
            "voltage_3_3v": 3.3,
            "inlet_temp": 25.0,
            "exhaust_temp": 40.0,
        }
        self._stress_active = False

    def power_cycle(self) -> bool:
        self._power_state = "off"
        self._logger.info("Power state: off")
        self._power_state = "on"
        self._logger.info("Power state: on")
        return True

    def power_on(self) -> bool:
        self._power_state = "on"
        self._logger.info("Power state: on")
        return True

    def power_off(self) -> bool:
        self._power_state = "off"
        self._logger.info("Power state: off")
        return True

    def get_power_state(self) -> str:
        return self._power_state

    def get_boot_device(self) -> str:
        return self._boot_device

    def set_boot_device(self, device: str) -> bool:
        self._boot_device = device
        return True

    def read_sensor(self, sensor_name: str) -> float:
        return self._sensors.get(sensor_name, 0.0)

    def get_all_sensors(self) -> Dict[str, float]:
        return self._sensors.copy()


class HardwareLayer(LayerProtocol):
    """
    Hardware layer for whole machine testing.

    Implements tests for power management, boot sequence, stress testing,
    thermal monitoring, and performance benchmarks.
    """

    def __init__(self, hardware_api: HardwareApi = None):
        self._name = "hardware"
        self._description = "Hardware layer for whole machine testing"
        self._api = hardware_api or MockHardwareApi()
        self._power_tests = PowerTests(self._api)
        self._boot_tests = BootTests(self._api)
        self._stress_tests = StressTests(self._api)
        self._thermal_tests = ThermalTests(self._api)
        self._performance_tests = PerformanceTests(self._api)
        self._logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def setup(self, context: LayerContext) -> None:
        """Initialize hardware layer."""
        self._logger.info("Hardware layer setup")
        context.set_test_data("hardware_layer_ready", True)

    def execute(self, context: LayerContext) -> LayerResult:
        """Execute all hardware tests."""
        self._logger.info("Executing hardware layer tests")

        all_passed = True
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        errors = []
        results_data = {}

        # Power tests
        power_result = self._power_tests.run_tests()
        total_tests += power_result.get("total", 0)
        passed_tests += power_result.get("passed", 0)
        failed_tests += power_result.get("failed", 0)
        results_data["power"] = power_result
        if power_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(power_result.get("errors", []))

        # Boot tests
        boot_result = self._boot_tests.run_tests()
        total_tests += boot_result.get("total", 0)
        passed_tests += boot_result.get("passed", 0)
        failed_tests += boot_result.get("failed", 0)
        results_data["boot"] = boot_result
        if boot_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(boot_result.get("errors", []))

        # Stress tests
        stress_result = self._stress_tests.run_tests()
        total_tests += stress_result.get("total", 0)
        passed_tests += stress_result.get("passed", 0)
        failed_tests += stress_result.get("failed", 0)
        results_data["stress"] = stress_result
        if stress_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(stress_result.get("errors", []))

        # Thermal tests
        thermal_result = self._thermal_tests.run_tests()
        total_tests += thermal_result.get("total", 0)
        passed_tests += thermal_result.get("passed", 0)
        failed_tests += thermal_result.get("failed", 0)
        results_data["thermal"] = thermal_result
        if thermal_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(thermal_result.get("errors", []))

        # Performance tests
        perf_result = self._performance_tests.run_tests()
        total_tests += perf_result.get("total", 0)
        passed_tests += perf_result.get("passed", 0)
        failed_tests += perf_result.get("failed", 0)
        results_data["performance"] = perf_result
        if perf_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(perf_result.get("errors", []))

        status = TestStatus.PASSED if all_passed else TestStatus.FAILED
        message = f"Hardware layer: {passed_tests}/{total_tests} tests passed"

        return LayerResult(
            layer_name=self._name,
            status=status,
            message=message,
            tests_run=total_tests,
            tests_passed=passed_tests,
            tests_failed=failed_tests,
            errors=errors,
            data=results_data,
        )

    def teardown(self, context: LayerContext) -> None:
        """Clean up hardware layer."""
        self._logger.info("Hardware layer teardown")
        self._stress_tests.stop_all()

    def get_power_tests(self) -> PowerTests:
        """Get power tests instance."""
        return self._power_tests

    def get_boot_tests(self) -> BootTests:
        """Get boot tests instance."""
        return self._boot_tests

    def get_stress_tests(self) -> StressTests:
        """Get stress tests instance."""
        return self._stress_tests

    def get_thermal_tests(self) -> ThermalTests:
        """Get thermal tests instance."""
        return self._thermal_tests

    def get_performance_tests(self) -> PerformanceTests:
        """Get performance tests instance."""
        return self._performance_tests
