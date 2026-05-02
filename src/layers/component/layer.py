"""
ComponentLayer class implementing LayerProtocol.

Tests individual server parts and modules.
"""

from typing import Any, Dict, List
import logging

from src.core.layer import LayerContext, LayerProtocol, LayerResult, TestStatus
from src.layers.component.cpu import CpuTests
from src.layers.component.memory import MemoryTests
from src.layers.component.storage import StorageTests
from src.layers.component.network import NetworkTests
from src.layers.component.pcie import PCIeTests


class ComponentLayer(LayerProtocol):
    """
    Component layer for testing individual server components.

    Tests CPU, memory, storage, network, and PCIe devices independently.
    """

    def __init__(self, config: Dict[str, Any] = None):
        self._name = "component"
        self._description = "Component layer for parts/modules testing"
        self._config = config or {}
        self._cpu_tests = CpuTests()
        self._memory_tests = MemoryTests()
        self._storage_tests = StorageTests()
        self._network_tests = NetworkTests()
        self._pcie_tests = PCIeTests()
        self._logger = logging.getLogger(__name__)

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def setup(self, context: LayerContext) -> None:
        """Initialize component layer."""
        self._logger.info("Component layer setup")
        context.set_test_data("component_layer_ready", True)

    def execute(self, context: LayerContext) -> LayerResult:
        """Execute all component tests."""
        self._logger.info("Executing component layer tests")

        all_passed = True
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        errors = []
        results_data = {}

        # CPU tests
        cpu_result = self._cpu_tests.run_tests()
        total_tests += cpu_result.get("total", 0)
        passed_tests += cpu_result.get("passed", 0)
        failed_tests += cpu_result.get("failed", 0)
        results_data["cpu"] = cpu_result
        if cpu_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(cpu_result.get("errors", []))

        # Memory tests
        memory_result = self._memory_tests.run_tests()
        total_tests += memory_result.get("total", 0)
        passed_tests += memory_result.get("passed", 0)
        failed_tests += memory_result.get("failed", 0)
        results_data["memory"] = memory_result
        if memory_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(memory_result.get("errors", []))

        # Storage tests
        storage_result = self._storage_tests.run_tests()
        total_tests += storage_result.get("total", 0)
        passed_tests += storage_result.get("passed", 0)
        failed_tests += storage_result.get("failed", 0)
        results_data["storage"] = storage_result
        if storage_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(storage_result.get("errors", []))

        # Network tests
        network_result = self._network_tests.run_tests()
        total_tests += network_result.get("total", 0)
        passed_tests += network_result.get("passed", 0)
        failed_tests += network_result.get("failed", 0)
        results_data["network"] = network_result
        if network_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(network_result.get("errors", []))

        # PCIe tests
        pcie_result = self._pcie_tests.run_tests()
        total_tests += pcie_result.get("total", 0)
        passed_tests += pcie_result.get("passed", 0)
        failed_tests += pcie_result.get("failed", 0)
        results_data["pcie"] = pcie_result
        if pcie_result.get("failed", 0) > 0:
            all_passed = False
            errors.extend(pcie_result.get("errors", []))

        status = TestStatus.PASSED if all_passed else TestStatus.FAILED
        message = f"Component layer: {passed_tests}/{total_tests} tests passed"

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
        """Clean up component layer."""
        self._logger.info("Component layer teardown")

    def get_cpu_tests(self) -> CpuTests:
        """Get CPU tests instance."""
        return self._cpu_tests

    def get_memory_tests(self) -> MemoryTests:
        """Get memory tests instance."""
        return self._memory_tests

    def get_storage_tests(self) -> StorageTests:
        """Get storage tests instance."""
        return self._storage_tests

    def get_network_tests(self) -> NetworkTests:
        """Get network tests instance."""
        return self._network_tests

    def get_pcie_tests(self) -> PCIeTests:
        """Get PCIe tests instance."""
        return self._pcie_tests
