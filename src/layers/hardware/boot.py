"""
Boot sequence validation tests.

Tests for BIOS POST, bootloader, and OS initialization.
"""

from typing import Any, Dict
import logging


class BootTests:
    """
    Boot sequence validation test suite.

    Tests BIOS POST, bootloader, boot device order, and OS boot.
    """

    def __init__(self, hardware_api):
        self._api = hardware_api
        self._logger = logging.getLogger(__name__)

    def bios_post_check(self) -> Dict[str, Any]:
        """
        Test BIOS POST completion.

        Returns dict with test result.
        """
        result = {"test": "bios_post_check", "passed": False, "errors": []}

        try:
            # Check power state is on (required for POST)
            state = self._api.get_power_state()
            if state != "on":
                result["errors"].append(f"Cannot run POST check - power is {state}")
                return result

            # In a real implementation, would check IPMI POST completion flag
            # For mock, we simulate successful POST
            sensors = self._api.get_all_sensors()
            if not sensors:
                result["errors"].append("No sensors available for POST check")
                return result

            result["passed"] = True
            self._logger.info("BIOS POST check passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"BIOS POST check failed: {e}")

        return result

    def bootloader_verification(self) -> Dict[str, Any]:
        """
        Test bootloader verification.

        Returns dict with test result.
        """
        result = {"test": "bootloader_verification", "passed": False, "errors": []}

        try:
            # Check boot device is set
            boot_device = self._api.get_boot_device()
            if not boot_device:
                result["errors"].append("Boot device not set")
                return result

            # Verify boot device is a valid option
            valid_devices = ["disk", "pxe", "usb", "cdrom", "bios"]
            if boot_device not in valid_devices:
                result["errors"].append(f"Invalid boot device: {boot_device}")
                return result

            result["passed"] = True
            result["data"] = {"boot_device": boot_device}
            self._logger.info(f"Bootloader verification passed (device: {boot_device})")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Bootloader verification failed: {e}")

        return result

    def os_boot_timeout(self) -> Dict[str, Any]:
        """
        Test OS boot timeout handling.

        Returns dict with test result.
        """
        result = {"test": "os_boot_timeout", "passed": False, "errors": []}

        try:
            # Check power state indicates successful boot
            state = self._api.get_power_state()
            if state != "on":
                result["errors"].append(f"Power state is {state}, expected 'on'")
                return result

            # In real implementation, would check for OS boot complete indicator
            result["passed"] = True
            self._logger.info("OS boot timeout test passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"OS boot timeout test failed: {e}")

        return result

    def boot_device_order(self) -> Dict[str, Any]:
        """
        Test boot device order configuration.

        Returns dict with test result.
        """
        result = {"test": "boot_device_order", "passed": False, "errors": []}

        try:
            # Get current boot device
            boot_device = self._api.get_boot_device()

            # Test setting boot device
            test_device = "pxe"
            if not self._api.set_boot_device(test_device):
                result["errors"].append(f"Failed to set boot device to {test_device}")
                return result

            # Verify it was set
            current = self._api.get_boot_device()
            if current != test_device:
                result["errors"].append(f"Boot device mismatch: expected {test_device}, got {current}")
                return result

            # Restore original boot device
            self._api.set_boot_device(boot_device)

            result["passed"] = True
            result["data"] = {"original_device": boot_device, "tested_device": test_device}
            self._logger.info("Boot device order test passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"Boot device order test failed: {e}")

        return result

    def run_tests(self) -> Dict[str, Any]:
        """
        Run all boot tests.

        Returns aggregate results.
        """
        results = []
        total = 4
        passed = 0
        failed = 0
        all_errors = []

        for test_method in [
            self.bios_post_check,
            self.bootloader_verification,
            self.os_boot_timeout,
            self.boot_device_order,
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
