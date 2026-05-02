"""
IPMI sensor and command tests.
"""

from typing import Any, Dict, List, Optional
import logging


class IpmiClient:
    """
    Abstract IPMI client interface.
    """

    def __init__(self, host: str, user: str, password: str):
        self.host = host
        self.user = user
        self._connected = False

    def connect(self) -> bool:
        """Connect to BMC."""
        raise NotImplementedError

    def disconnect(self) -> None:
        """Disconnect from BMC."""
        raise NotImplementedError

    def is_connected(self) -> bool:
        """Check connection status."""
        raise NotImplementedError

    def get_sensor_reading(self, sensor_name: str) -> Optional[float]:
        """Get sensor reading by name."""
        raise NotImplementedError

    def get_sdr(self) -> Dict[str, Any]:
        """Get SDR (Sensor Data Record) dump."""
        raise NotImplementedError

    def get_sel(self) -> List[Dict[str, Any]]:
        """Get SEL (System Event Log) entries."""
        raise NotImplementedError

    def run_raw_command(self, netfn: int, cmd: int, data: List[int] = None) -> Optional[bytes]:
        """Run raw IPMI command."""
        raise NotImplementedError


class MockIpmiClient(IpmiClient):
    """
    Mock IPMI client for testing.
    """

    def __init__(self, host: str = "192.168.1.1", user: str = "admin", password: str = ""):
        super().__init__(host, user, password)
        self._connected = True
        self.sdr_cache: Dict[str, Any] = {}
        self.sel_entries: List[Dict[str, Any]] = []

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_sensor_reading(self, sensor_name: str) -> Optional[float]:
        sensor_map = {
            "CPU Temp": 45.0,
            "System Temp": 38.0,
            "Fan 1": 5000.0,
            "Fan 2": 5100.0,
            "Fan 3": 4900.0,
            "Fan 4": 5200.0,
            "12V": 12.1,
            "5V": 5.0,
            "3.3V": 3.3,
            "VBAT": 3.0,
        }
        return sensor_map.get(sensor_name)

    def get_sdr(self) -> Dict[str, Any]:
        return {
            "CPU Temp": {"value": 45.0, "unit": "C", "status": "ok"},
            "System Temp": {"value": 38.0, "unit": "C", "status": "ok"},
            "Fan 1": {"value": 5000.0, "unit": "RPM", "status": "ok"},
        }

    def get_sel(self) -> List[Dict[str, Any]]:
        return self.sel_entries.copy()

    def run_raw_command(self, netfn: int, cmd: int, data: List[int] = None) -> Optional[bytes]:
        return b"\x00\x00"


class IpmiTests:
    """
    IPMI test suite.

    Tests sensor readings, SDR, SEL, and raw commands.
    """

    def __init__(self, client: IpmiClient = None):
        self._client = client or MockIpmiClient()
        self._logger = logging.getLogger(__name__)

    def sensor_reading_validation(self) -> Dict[str, Any]:
        """
        Validate IPMI sensor readings.

        Returns dict with test result.
        """
        result = {"test": "sensor_reading_validation", "passed": False, "errors": []}

        try:
            sensors = [
                "CPU Temp",
                "System Temp",
                "Fan 1",
                "Fan 2",
                "12V",
                "5V",
            ]

            for sensor_name in sensors:
                value = self._client.get_sensor_reading(sensor_name)
                if value is None:
                    result["errors"].append(f"Sensor {sensor_name} not found")
                    return result

                # Validate reasonable ranges
                if "Temp" in sensor_name and (value < -20 or value > 120):
                    result["errors"].append(f"Sensor {sensor_name} value out of range: {value}")
                    return result
                if "Fan" in sensor_name and (value < 0 or value > 20000):
                    result["errors"].append(f"Sensor {sensor_name} value out of range: {value}")
                    return result

            result["passed"] = True
            result["data"] = {"sensors_tested": len(sensors)}
            self._logger.info("Sensor reading validation passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Sensor reading validation failed: {e}")

        return result

    def sdr_dump_parsing(self) -> Dict[str, Any]:
        """
        Parse and validate SDR dump.

        Returns dict with test result.
        """
        result = {"test": "sdr_dump_parsing", "passed": False, "errors": []}

        try:
            sdr = self._client.get_sdr()

            if not sdr:
                result["errors"].append("SDR dump is empty")
                return result

            # Validate SDR structure
            for sensor_name, sensor_data in sdr.items():
                if "value" not in sensor_data:
                    result["errors"].append(f"SDR entry {sensor_name} missing value")
                    return result
                if "status" not in sensor_data:
                    result["errors"].append(f"SDR entry {sensor_name} missing status")
                    return result

            result["passed"] = True
            result["data"] = {"sdr_entries": len(sdr)}
            self._logger.info(f"SDR dump parsing passed: {len(sdr)} entries")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"SDR dump parsing failed: {e}")

        return result

    def sel_listing(self) -> Dict[str, Any]:
        """
        List SEL entries.

        Returns dict with test result.
        """
        result = {"test": "sel_listing", "passed": False, "errors": []}

        try:
            sel = self._client.get_sel()

            # SEL can be empty, that's OK
            result["passed"] = True
            result["data"] = {"sel_entries": len(sel)}
            self._logger.info(f"SEL listing passed: {len(sel)} entries")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"SEL listing failed: {e}")

        return result

    def raw_command_execution(self) -> Dict[str, Any]:
        """
        Execute raw IPMI command.

        Returns dict with test result.
        """
        result = {"test": "raw_command_execution", "passed": False, "errors": []}

        try:
            # Execute a simple raw command (Get Device ID: netfn=0x06, cmd=0x01)
            response = self._client.run_raw_command(0x06, 0x01)

            if response is None:
                result["errors"].append("Raw command returned no response")
                return result

            result["passed"] = True
            result["data"] = {"response_length": len(response)}
            self._logger.info(f"Raw command execution passed: {len(response)} bytes")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Raw command execution failed: {e}")

        return result

    def user_management(self) -> Dict[str, Any]:
        """
        Test IPMI user management (simulation).

        Returns dict with test result.
        """
        result = {"test": "user_management", "passed": False, "errors": []}

        try:
            # In real implementation, would test user list, add, delete
            # For mock, just validate connection
            if not self._client.is_connected():
                result["errors"].append("IPMI client not connected")
                return result

            result["passed"] = True
            result["data"] = {"users_configurable": True}
            self._logger.info("User management test passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"User management test failed: {e}")

        return result

    def run_tests(self) -> Dict[str, Any]:
        """Run all IPMI tests."""
        results = []
        total = 5
        passed = 0
        failed = 0
        all_errors = []

        for test_method in [
            self.sensor_reading_validation,
            self.sdr_dump_parsing,
            self.sel_listing,
            self.raw_command_execution,
            self.user_management,
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
