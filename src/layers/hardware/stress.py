"""
Stress testing module.

Tests for CPU, memory, and IO stress.
"""

from typing import Any, Dict, List, Optional
import logging
import time
import threading


class StressTests:
    """
    Stress testing suite.

    Tests CPU, memory, and IO stress with configurable duration and intensity.
    """

    def __init__(self, hardware_api):
        self._api = hardware_api
        self._logger = logging.getLogger(__name__)
        self._active_stressors: List[threading.Thread] = []
        self._stop_stress = False

    def cpu_stress(self, cores: int = 0, duration_seconds: int = 60) -> Dict[str, Any]:
        """
        Run CPU stress test.

        Args:
            cores: Number of cores to stress (0 = all)
            duration_seconds: Duration of stress test

        Returns dict with test result.
        """
        result = {"test": "cpu_stress", "passed": False, "errors": []}

        try:
            self._logger.info(f"Starting CPU stress test: cores={cores}, duration={duration_seconds}")

            # In a real implementation, would spawn stress processes
            # For mock, we just validate parameters
            if duration_seconds <= 0:
                result["errors"].append("Duration must be positive")
                return result

            sensors = self._api.get_all_sensors()
            cpu_temp = sensors.get("cpu_temp", 0)

            # Simulate stress test
            self._stop_stress = False

            def stress_worker():
                while not self._stop_stress:
                    # Simulate CPU load
                    time.sleep(0.1)

            stress_thread = threading.Thread(target=stress_worker, daemon=True)
            stress_thread.start()
            self._active_stressors.append(stress_thread)

            # Let it run briefly
            time.sleep(min(2, duration_seconds))
            self._stop_stress = True
            stress_thread.join(timeout=5)

            # Check thermal sensors are still readable
            sensors_after = self._api.get_all_sensors()
            if not sensors_after:
                result["errors"].append("Sensors not readable after stress test")
                return result

            result["passed"] = True
            result["data"] = {
                "cores": cores,
                "duration_seconds": duration_seconds,
                "cpu_temp_after": sensors_after.get("cpu_temp", 0),
            }
            self._logger.info("CPU stress test completed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"CPU stress test failed: {e}")

        return result

    def memory_stress(self, percent: int = 50, duration_seconds: int = 60) -> Dict[str, Any]:
        """
        Run memory stress test.

        Args:
            percent: Percentage of memory to stress
            duration_seconds: Duration of stress test

        Returns dict with test result.
        """
        result = {"test": "memory_stress", "passed": False, "errors": []}

        try:
            self._logger.info(f"Starting memory stress test: percent={percent}, duration={duration_seconds}")

            if percent <= 0 or percent > 100:
                result["errors"].append("Percent must be between 1 and 100")
                return result

            if duration_seconds <= 0:
                result["errors"].append("Duration must be positive")
                return result

            # In a real implementation, would allocate and access memory
            # For mock, we just validate parameters

            sensors = self._api.get_all_sensors()
            mem_temp = sensors.get("memory_temp", 0)

            result["passed"] = True
            result["data"] = {
                "percent": percent,
                "duration_seconds": duration_seconds,
                "memory_temp": mem_temp,
            }
            self._logger.info("Memory stress test completed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Memory stress test failed: {e}")

        return result

    def io_stress(self, size_mb: int = 1024, duration_seconds: int = 60) -> Dict[str, Any]:
        """
        Run IO stress test.

        Args:
            size_mb: Size of IO operations in MB
            duration_seconds: Duration of stress test

        Returns dict with test result.
        """
        result = {"test": "io_stress", "passed": False, "errors": []}

        try:
            self._logger.info(f"Starting IO stress test: size={size_mb}MB, duration={duration_seconds}")

            if size_mb <= 0:
                result["errors"].append("Size must be positive")
                return result

            if duration_seconds <= 0:
                result["errors"].append("Duration must be positive")
                return result

            # In a real implementation, would run fio or similar
            # For mock, we just validate parameters

            result["passed"] = True
            result["data"] = {
                "size_mb": size_mb,
                "duration_seconds": duration_seconds,
            }
            self._logger.info("IO stress test completed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"IO stress test failed: {e}")

        return result

    def stop_all(self) -> None:
        """Stop all active stress tests."""
        self._stop_stress = True
        for thread in self._active_stressors:
            if thread.is_alive():
                thread.join(timeout=2)
        self._active_stressors.clear()
        self._logger.info("All stress tests stopped")

    def run_tests(self) -> Dict[str, Any]:
        """
        Run all stress tests with default parameters.

        Returns aggregate results.
        """
        results = []
        total = 3
        passed = 0
        failed = 0
        all_errors = []

        test_configs = [
            (self.cpu_stress, {"cores": 0, "duration_seconds": 5}),
            (self.memory_stress, {"percent": 50, "duration_seconds": 5}),
            (self.io_stress, {"size_mb": 100, "duration_seconds": 5}),
        ]

        for test_method, kwargs in test_configs:
            test_result = test_method(**kwargs)
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
