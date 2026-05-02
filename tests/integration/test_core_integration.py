"""
Integration tests for core framework.

Tests cross-layer context propagation and multi-layer execution.
"""

import pytest
from src.core.layer import LayerContext, LayerProtocol, LayerResult, TestStatus, HardwareInfo, ServerContext
from src.core.runner import TestRunnerEngine
from src.core.plugin import PluginRegistry


class HardwareLayer(LayerProtocol):
    """Hardware layer implementation for testing."""

    def __init__(self):
        self._name = "hardware"
        self._setup_called = False
        self._teardown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Hardware layer for whole machine testing"

    def setup(self, context: LayerContext) -> None:
        self._setup_called = True
        # Set hardware-specific test data
        context.set_test_data("hardware_probed", True)
        context.set_test_data("boot_device", "NVMe")

    def execute(self, context: LayerContext) -> LayerResult:
        # Verify we can access hardware info
        cpu_count = context.hardware.cpu_count
        return LayerResult(
            layer_name=self.name,
            status=TestStatus.PASSED,
            message=f"Hardware layer executed, CPU count: {cpu_count}",
            tests_run=1,
            tests_passed=1,
        )

    def teardown(self, context: LayerContext) -> None:
        self._teardown_called = True


class ComponentLayer(LayerProtocol):
    """Component layer implementation for testing."""

    def __init__(self):
        self._name = "component"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "Component layer for parts testing"

    def setup(self, context: LayerContext) -> None:
        # Access parent hardware context
        hardware_ctx = context.get_parent_context("hardware")
        if hardware_ctx:
            context.set_test_data("from_hardware", True)

    def execute(self, context: LayerContext) -> LayerResult:
        # Verify cross-layer data access
        hardware_probed = context.get_test_data("hardware_probed", False)
        from_hardware = context.get_test_data("from_hardware", False)

        return LayerResult(
            layer_name=self.name,
            status=TestStatus.PASSED,
            message=f"Component layer: hardware_probed={hardware_probed}, from_hardware={from_hardware}",
            tests_run=1,
            tests_passed=1,
        )

    def teardown(self, context: LayerContext) -> None:
        pass


class BMCLayer(LayerProtocol):
    """BMC layer implementation for testing."""

    def __init__(self):
        self._name = "bmc"

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return "BMC layer for firmware testing"

    def setup(self, context: LayerContext) -> None:
        # Access hardware context through chain
        hardware_ctx = context.get_parent_context("hardware")
        if hardware_ctx:
            context.set_test_data("bmc_can_access_hardware", True)

    def execute(self, context: LayerContext) -> LayerResult:
        # Verify all layers can access root context
        bmc_can_access_hw = context.get_test_data("bmc_can_access_hardware", False)

        return LayerResult(
            layer_name=self.name,
            status=TestStatus.PASSED,
            message=f"BMC layer: bmc_can_access_hardware={bmc_can_access_hw}",
            tests_run=1,
            tests_passed=1,
        )

    def teardown(self, context: LayerContext) -> None:
        pass


@pytest.fixture
def initial_context(server_context, hardware_info, component_map):
    """Create initial layer context."""
    return LayerContext(
        layer_name="hardware",
        server=server_context,
        hardware=hardware_info,
        components=component_map,
    )


@pytest.fixture
def test_runner():
    """Create a test runner engine."""
    return TestRunnerEngine()


class TestLayerExecution:
    """Tests for layer execution."""

    def test_single_layer_execution(self, test_runner, initial_context):
        """Test executing a single layer."""
        layer = HardwareLayer()
        test_runner.register_layer(layer)

        result = test_runner.run_layer("hardware", initial_context)

        assert result.status == TestStatus.PASSED
        assert result.layer_name == "hardware"

    def test_multi_layer_execution(self, test_runner, initial_context):
        """Test executing multiple layers in order."""
        hw_layer = HardwareLayer()
        comp_layer = ComponentLayer()
        bmc_layer = BMCLayer()

        test_runner.register_layer(hw_layer)
        test_runner.register_layer(comp_layer)
        test_runner.register_layer(bmc_layer)

        results = test_runner.run_all_layers(initial_context)

        assert len(results) == 3
        assert results["hardware"].status == TestStatus.PASSED
        assert results["component"].status == TestStatus.PASSED
        assert results["bmc"].status == TestStatus.PASSED

    def test_layer_execution_order(self, test_runner, initial_context):
        """Test layers execute in registration order."""
        hw_layer = HardwareLayer()
        comp_layer = ComponentLayer()

        test_runner.register_layer(hw_layer)
        test_runner.register_layer(comp_layer)

        layers = test_runner.get_registered_layers()
        assert layers == ["hardware", "component"]


class TestContextPropagation:
    """Tests for context propagation across layers."""

    def test_test_data_propagation(self, test_runner, initial_context):
        """Test test data propagates from hardware to component layer."""
        hw_layer = HardwareLayer()
        comp_layer = ComponentLayer()

        test_runner.register_layer(hw_layer)
        test_runner.register_layer(comp_layer)

        results = test_runner.run_all_layers(initial_context)

        # Component layer should have received hardware_probed from hardware layer
        comp_result = results["component"]
        assert "hardware_probed=True" in comp_result.message

    def test_parent_context_access(self, test_runner, initial_context):
        """Test component layer can access hardware parent context."""
        hw_layer = HardwareLayer()
        comp_layer = ComponentLayer()

        test_runner.register_layer(hw_layer)
        test_runner.register_layer(comp_layer)

        results = test_runner.run_all_layers(initial_context)

        # Component should have set from_hardware via parent access
        comp_result = results["component"]
        assert "from_hardware=True" in comp_result.message

    def test_bmc_layer_hardware_access(self, test_runner, initial_context):
        """Test BMC layer can access hardware context through chain."""
        hw_layer = HardwareLayer()
        comp_layer = ComponentLayer()
        bmc_layer = BMCLayer()

        test_runner.register_layer(hw_layer)
        test_runner.register_layer(comp_layer)
        test_runner.register_layer(bmc_layer)

        results = test_runner.run_all_layers(initial_context)

        bmc_result = results["bmc"]
        assert "bmc_can_access_hardware=True" in bmc_result.message


class TestAggregateSummary:
    """Tests for result aggregation."""

    def test_aggregate_summary(self, test_runner, initial_context):
        """Test aggregate summary counts."""
        hw_layer = HardwareLayer()
        comp_layer = ComponentLayer()

        test_runner.register_layer(hw_layer)
        test_runner.register_layer(comp_layer)

        test_runner.run_all_layers(initial_context)

        summary = test_runner.get_aggregate_summary()
        assert summary["total_run"] == 2
        assert summary["total_passed"] == 2
        assert summary["layers_executed"] == 2


class TestPluginIntegration:
    """Tests for plugin integration with runner."""

    def test_runner_with_plugin_registry(self, test_runner, initial_context):
        """Test runner works with plugin registry."""
        registry = PluginRegistry()
        hw_layer = HardwareLayer()

        registry.register("hardware", hw_layer)
        test_runner.register_layer(hw_layer)

        result = test_runner.run_layer("hardware", initial_context)
        assert result.status == TestStatus.PASSED
