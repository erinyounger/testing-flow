"""
Unit tests for layer abstraction.
"""

import pytest
from src.core.layer import (
    LayerContext,
    LayerProtocol,
    LayerResult,
    TestStatus,
    HardwareInfo,
    ServerContext,
    ComponentInfo,
)


class MockLayer(LayerProtocol):
    """Mock implementation of LayerProtocol for testing."""

    def __init__(self, name: str = "mock_layer"):
        self._name = name
        self._setup_called = False
        self._execute_called = False
        self._teardown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Mock layer: {self._name}"

    def setup(self, context: LayerContext) -> None:
        self._setup_called = True

    def execute(self, context: LayerContext) -> LayerResult:
        self._execute_called = True
        return LayerResult(
            layer_name=self._name,
            status=TestStatus.PASSED,
            message="Mock execution successful",
            tests_run=1,
            tests_passed=1,
        )

    def teardown(self, context: LayerContext) -> None:
        self._teardown_called = True


class TestLayerContext:
    """Tests for LayerContext dataclass."""

    def test_layer_context_creation(self, layer_context):
        """Test LayerContext can be created with fixtures."""
        assert layer_context.layer_name == "test_layer"
        assert layer_context.server.hostname == "test-server-01"
        assert layer_context.hardware.cpu_count == 2
        assert layer_context.components["cpu"][0].name == "CPU0"

    def test_layer_context_parent_none(self, layer_context):
        """Test parent is None by default."""
        assert layer_context.parent is None

    def test_layer_context_parent_chain(self, layer_context):
        """Test parent context chain."""
        child_context = LayerContext(
            layer_name="child_layer",
            server=layer_context.server,
            hardware=layer_context.hardware,
            components=layer_context.components,
            parent=layer_context,
        )
        assert child_context.parent == layer_context
        assert child_context.get_parent_context("test_layer") == layer_context

    def test_layer_context_test_data(self, layer_context):
        """Test test data storage and retrieval."""
        layer_context.set_test_data("key1", "value1")
        assert layer_context.get_test_data("key1") == "value1"

    def test_layer_context_test_data_inheritance(self, layer_context):
        """Test test data is inherited from parent."""
        child_context = LayerContext(
            layer_name="child_layer",
            server=layer_context.server,
            hardware=layer_context.hardware,
            components=layer_context.components,
            parent=layer_context,
        )
        layer_context.set_test_data("shared_key", "shared_value")
        assert child_context.get_test_data("shared_key") == "shared_value"

    def test_layer_context_test_data_default(self, layer_context):
        """Test test data default value when key not found."""
        assert layer_context.get_test_data("nonexistent", "default") == "default"


class TestLayerResult:
    """Tests for LayerResult dataclass."""

    def test_layer_result_success(self):
        """Test LayerResult success property."""
        result = LayerResult(
            layer_name="test_layer",
            status=TestStatus.PASSED,
        )
        assert result.success is True

    def test_layer_result_failure(self):
        """Test LayerResult failure property."""
        result = LayerResult(
            layer_name="test_layer",
            status=TestStatus.FAILED,
        )
        assert result.success is False

    def test_layer_result_with_errors(self):
        """Test LayerResult can hold errors."""
        result = LayerResult(
            layer_name="test_layer",
            status=TestStatus.ERROR,
            errors=["Error 1", "Error 2"],
        )
        assert len(result.errors) == 2


class TestLayerProtocol:
    """Tests for LayerProtocol ABC."""

    def test_mock_layer_implements_protocol(self):
        """Test mock layer properly implements the protocol."""
        layer = MockLayer()
        assert hasattr(layer, 'name')
        assert hasattr(layer, 'description')
        assert hasattr(layer, 'setup')
        assert hasattr(layer, 'execute')
        assert hasattr(layer, 'teardown')

    def test_mock_layer_execution_flow(self, layer_context):
        """Test mock layer executes setup, execute, teardown in order."""
        layer = MockLayer()

        # Initially none called
        assert not layer._setup_called
        assert not layer._execute_called
        assert not layer._teardown_called

        # Execute flow
        layer.setup(layer_context)
        result = layer.execute(layer_context)
        layer.teardown(layer_context)

        # All should be called
        assert layer._setup_called
        assert layer._execute_called
        assert layer._teardown_called
        assert result.status == TestStatus.PASSED

    def test_get_test_methods(self):
        """Test get_test_methods returns test methods."""
        layer = MockLayer()
        # Add some test methods using regular functions
        def test_one(ctx): pass
        def test_two(ctx): pass
        def helper(): pass

        layer.test_one = test_one
        layer.test_two = test_two
        layer.helper = helper

        methods = layer.get_test_methods()
        method_names = [m.__name__ for m in methods]
        assert "test_one" in method_names
        assert "test_two" in method_names
        assert "helper" not in method_names


class TestHardwareInfo:
    """Tests for HardwareInfo dataclass."""

    def test_hardware_info_to_dict(self):
        """Test HardwareInfo serializes to dict."""
        info = HardwareInfo(
            cpu_count=4,
            cpu_model="Xeon Gold",
            memory_total_gb=512.0,
        )
        d = info.to_dict()
        assert d["cpu_count"] == 4
        assert d["cpu_model"] == "Xeon Gold"
        assert d["memory_total_gb"] == 512.0


class TestServerContext:
    """Tests for ServerContext dataclass."""

    def test_server_context_to_dict(self):
        """Test ServerContext serializes to dict."""
        ctx = ServerContext(
            hostname="testhost",
            ipmi_ip="192.168.1.1",
        )
        d = ctx.to_dict()
        assert d["hostname"] == "testhost"
        assert d["ipmi_ip"] == "192.168.1.1"


class TestComponentInfo:
    """Tests for ComponentInfo dataclass."""

    def test_component_info_to_dict(self):
        """Test ComponentInfo serializes to dict."""
        comp = ComponentInfo(
            component_type="cpu",
            name="CPU0",
            location="Socket 0",
            status="healthy",
            properties={"cores": 24},
        )
        d = comp.to_dict()
        assert d["component_type"] == "cpu"
        assert d["properties"]["cores"] == 24
