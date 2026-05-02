"""
Layer abstraction for the server test framework.

Defines the base classes and protocols for implementing test layers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import logging


class TestStatus(Enum):
    """Test execution status."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    NOT_RUN = "not_run"


@dataclass
class HardwareInfo:
    """Hardware information for the server under test."""
    cpu_count: int = 0
    cpu_model: str = ""
    memory_total_gb: float = 0.0
    memory_available_gb: float = 0.0
    storage_devices: List[str] = field(default_factory=list)
    network_interfaces: List[str] = field(default_factory=list)
    bios_version: str = ""
    bmc_version: str = ""
    power_supplies: int = 0
    system_vendor: str = ""
    system_product: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_count": self.cpu_count,
            "cpu_model": self.cpu_model,
            "memory_total_gb": self.memory_total_gb,
            "memory_available_gb": self.memory_available_gb,
            "storage_devices": self.storage_devices,
            "network_interfaces": self.network_interfaces,
            "bios_version": self.bios_version,
            "bmc_version": self.bmc_version,
            "power_supplies": self.power_supplies,
            "system_vendor": self.system_vendor,
            "system_product": self.system_product,
        }


@dataclass
class ComponentInfo:
    """Component information for enumerated server components."""
    component_type: str
    name: str
    location: str
    status: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_type": self.component_type,
            "name": self.name,
            "location": self.location,
            "status": self.status,
            "properties": self.properties,
        }


@dataclass
class ServerContext:
    """Server metadata and state."""
    hostname: str = ""
    ipmi_ip: str = ""
    bmc_ip: str = ""
    ssh_host: str = ""
    ssh_user: str = ""
    ssh_password: str = ""
    server_model: str = ""
    server_serial: str = ""
    os_type: str = ""
    os_version: str = ""
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "hostname": self.hostname,
            "ipmi_ip": self.ipmi_ip,
            "bmc_ip": self.bmc_ip,
            "ssh_host": self.ssh_host,
            "ssh_user": self.ssh_user,
            "server_model": self.server_model,
            "server_serial": self.server_serial,
            "os_type": self.os_type,
            "os_version": self.os_version,
            "tags": self.tags,
        }


@dataclass
class LayerContext:
    """
    Context passed through the layer hierarchy.

    Holds server state, hardware info, and component map.
    Can reference parent context for cross-layer access.
    """
    layer_name: str
    server: ServerContext
    hardware: HardwareInfo
    components: Dict[str, List[ComponentInfo]] = field(default_factory=dict)
    parent: Optional["LayerContext"] = None
    test_data: Dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=logging.getLogger)

    def get_parent_context(self, layer_name: str) -> Optional["LayerContext"]:
        """Get parent context by layer name for cross-layer access."""
        if self.parent is None:
            return None
        if self.parent.layer_name == layer_name:
            return self.parent
        return self.parent.get_parent_context(layer_name)

    def set_test_data(self, key: str, value: Any) -> None:
        """Store test data for cross-layer sharing."""
        self.test_data[key] = value

    def get_test_data(self, key: str, default: Any = None) -> Any:
        """Retrieve test data from this or parent contexts."""
        if key in self.test_data:
            return self.test_data[key]
        if self.parent:
            return self.parent.get_test_data(key, default)
        return default


@dataclass
class LayerResult:
    """Result from a layer test execution."""
    layer_name: str
    status: TestStatus
    message: str = ""
    duration_seconds: float = 0.0
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == TestStatus.PASSED


class LayerProtocol(ABC):
    """
    Protocol interface that each test layer must implement.

    Each layer provides setup, execute, and teardown methods
    for test execution within that layer's scope.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Layer name identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Layer description."""
        pass

    @abstractmethod
    def setup(self, context: LayerContext) -> None:
        """
        Prepare the layer for test execution.

        Args:
            context: Shared layer context
        """
        pass

    @abstractmethod
    def execute(self, context: LayerContext) -> LayerResult:
        """
        Execute tests within this layer.

        Args:
            context: Shared layer context

        Returns:
            LayerResult with test outcomes
        """
        pass

    @abstractmethod
    def teardown(self, context: LayerContext) -> None:
        """
        Clean up after test execution.

        Args:
            context: Shared layer context
        """
        pass

    def get_test_methods(self) -> List[Callable]:
        """Return list of test methods in this layer."""
        return [
            getattr(self, name)
            for name in dir(self)
            if name.startswith("test_") and callable(getattr(self, name))
        ]
