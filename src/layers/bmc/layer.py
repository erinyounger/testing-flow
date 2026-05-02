"""
BMCLayer class implementing LayerProtocol.

Tests firmware management interfaces with access to parent hardware context.
"""

from typing import Any, Dict
import logging

from src.core.layer import LayerContext, LayerProtocol, LayerResult, TestStatus
from src.layers.bmc.ipmi import IpmiTests
from src.layers.bmc.redfish import RedfishTests
from src.layers.bmc.bios_config import BiosConfigTests
from src.layers.bmc.firmware import FirmwareTests
from src.layers.bmc.sel import SelTests


class BMCLayer(LayerProtocol):
    """
    BMC layer for firmware management interface testing.

    Tests IPMI, Redfish, BIOS configuration, firmware updates, and SEL.
    Has access to parent hardware context for integrated testing.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self._name = "bmc"
        self._description = "BMC layer for firmware management interface testing"
        self._config = config or {}
        self._ipmi_tests = IpmiTests()
        self._redfish_tests = RedfishTests()
        self._bios_config_tests = BiosConfigTests()
        self._firmware_tests = FirmwareTests()
        self._sel_tests = SelTests()
        self._logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def setup(self, context: LayerContext) -> None:
        """Initialize BMC layer."""
        self._logger.info("BMC layer setup")

        # Access parent hardware context for integrated testing
        hardware_context = context.get_parent_context("hardware")
        if hardware_context:
            self._logger.info("BMC layer has access to hardware context")
            context.set_test_data("bmc_can_access_hardware", True)
        else:
            context.set_test_data("bmc_can_access_hardware", False)

        context.set_test_data("bmc_layer_ready", True)

    def execute(self, context: LayerContext) -> LayerResult:
        """Execute all BMC layer tests."""
        self._logger.info("Executing BMC layer tests")

        # Check if we have hardware context access
        bmc_can_access_hw = context.get_test_data("bmc_can_access_hardware", False)

        all_passed = True
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        errors = []
        results_data = {"bmc_can_access_hardware": bmc_can_access_hw}

        # IPMI tests
        ipmi_result = self._ipmi_tests.run_tests()
        total_tests += ipmi_result.get("total", 0)
        passed_tests += ipmi_result.get("passed", 0)
        failed_tests += ipmi_result.get("failed", 0)
        results_data["ipmi"] = ipmi_result
        if ipmi_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(ipmi_result.get("errors", []))

        # Redfish tests
        redfish_result = self._redfish_tests.run_tests()
        total_tests += redfish_result.get("total", 0)
        passed_tests += redfish_result.get("passed", 0)
        failed_tests += redfish_result.get("failed", 0)
        results_data["redfish"] = redfish_result
        if redfish_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(redfish_result.get("errors", []))

        # BIOS config tests
        bios_result = self._bios_config_tests.run_tests()
        total_tests += bios_result.get("total", 0)
        passed_tests += bios_result.get("passed", 0)
        failed_tests += bios_result.get("failed", 0)
        results_data["bios_config"] = bios_result
        if bios_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(bios_result.get("errors", []))

        # Firmware tests
        firmware_result = self._firmware_tests.run_tests()
        total_tests += firmware_result.get("total", 0)
        passed_tests += firmware_result.get("passed", 0)
        failed_tests += firmware_result.get("failed", 0)
        results_data["firmware"] = firmware_result
        if firmware_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(firmware_result.get("errors", []))

        # SEL tests
        sel_result = self._sel_tests.run_tests()
        total_tests += sel_result.get("total", 0)
        passed_tests += sel_result.get("passed", 0)
        failed_tests += sel_result.get("failed", 0)
        results_data["sel"] = sel_result
        if sel_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(sel_result.get("errors", []))

        status = TestStatus.PASSED if all_passed else TestStatus.FAILED
        message = f"BMC layer: {passed_tests}/{total_tests} tests passed"

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
        """Clean up BMC layer."""
        self._logger.info("BMC layer teardown")

    def get_ipmi_tests(self) -> IpmiTests:
        """Get IPMI tests instance."""
        return self._ipmi_tests

    def get_redfish_tests(self) -> RedfishTests:
        """Get Redfish tests instance."""
        return self._redfish_tests

    def get_bios_config_tests(self) -> BiosConfigTests:
        """Get BIOS config tests instance."""
        return self._bios_config_tests

    def get_firmware_tests(self) -> FirmwareTests:
        """Get firmware tests instance."""
        return self._firmware_tests

    def get_sel_tests(self) -> SelTests:
        """Get SEL tests instance."""
        return self._sel_tests
