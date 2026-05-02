"""
Pytest configuration and fixtures for server test framework.
"""

import pytest

# Import all fixtures from src.core.fixtures
from src.core.fixtures import (
    server_context,
    hardware_info,
    component_map,
    layer_context,
    mock_hardware_api,
    mock_ipmi_client,
    mock_redfish_client,
)

# Make fixtures available at package level
pytest_plugins = []


@pytest.fixture(scope="session")
def server_context():
    """Server context fixture."""
    from src.core.layer import ServerContext
    return ServerContext(
        hostname="test-server-01",
        ipmi_ip="192.168.1.1",
        bmc_ip="192.168.1.2",
        ssh_host="192.168.1.10",
        ssh_user="admin",
        ssh_password="",
        server_model="TestServer-Model",
        server_serial="SN12345678",
        os_type="Linux",
        os_version="Ubuntu 22.04",
        tags={"environment": "test", "rack": "A1"},
    )


@pytest.fixture(scope="session")
def hardware_info():
    """Hardware info fixture."""
    from src.core.layer import HardwareInfo
    return HardwareInfo(
        cpu_count=2,
        cpu_model="Intel Xeon Gold 6248",
        memory_total_gb=256.0,
        memory_available_gb=128.0,
        storage_devices=["/dev/sda", "/dev/sdb", "/dev/nvme0n1"],
        network_interfaces=["eth0", "eth1", "eth2", "eth3"],
        bios_version="2.4.5",
        bmc_version="3.2.1",
        power_supplies=2,
        system_vendor="TestVendor",
        system_product="TestServer",
    )


@pytest.fixture(scope="session")
def component_map():
    """Component map fixture."""
    from src.core.layer import ComponentInfo
    return {
        "cpu": [
            ComponentInfo(
                component_type="cpu",
                name="CPU0",
                location="Socket 0",
                status="healthy",
                properties={"cores": 24, "threads": 48, "frequency_mhz": 2500},
            ),
            ComponentInfo(
                component_type="cpu",
                name="CPU1",
                location="Socket 1",
                status="healthy",
                properties={"cores": 24, "threads": 48, "frequency_mhz": 2500},
            ),
        ],
        "memory": [
            ComponentInfo(
                component_type="memory",
                name="DIMM_A1",
                location="Slot A1",
                status="healthy",
                properties={"capacity_gb": 32, "speed_mhz": 2933, "ecc": True},
            ),
        ],
        "storage": [
            ComponentInfo(
                component_type="storage",
                name="NVME_0",
                location="PCIe Slot 1",
                status="healthy",
                properties={"capacity_tb": 2, "model": "Samsung PM9A3"},
            ),
        ],
        "network": [
            ComponentInfo(
                component_type="network",
                name="NIC_0",
                location="PCIe Slot 2",
                status="healthy",
                properties={"speed_gbps": 25, "ports": 2, "offload": True},
            ),
        ],
        "psu": [
            ComponentInfo(
                component_type="psu",
                name="PSU_0",
                location="PSU Bay 1",
                status="healthy",
                properties={"watts": 1200, "input_voltage": 220},
            ),
        ],
    }


@pytest.fixture
def layer_context(server_context, hardware_info, component_map):
    """Full layer context fixture."""
    from src.core.layer import LayerContext
    return LayerContext(
        layer_name="test_layer",
        server=server_context,
        hardware=hardware_info,
        components=component_map,
        parent=None,
        test_data={},
    )


@pytest.fixture
def mock_hardware_api():
    """Mock hardware API fixture."""
    class MockHardwareAPI:
        def __init__(self):
            self.power_state = "on"
            self.boot_device = "disk"
            self.sensors = {
                "cpu_temp": 45.0,
                "memory_temp": 38.0,
                "fan_speed_0": 5000,
                "fan_speed_1": 5100,
                "voltage_12v": 12.1,
                "voltage_5v": 5.0,
                "voltage_3_3v": 3.3,
            }

        def power_cycle(self):
            self.power_state = "off"
            self.power_state = "on"
            return True

        def get_power_state(self):
            return self.power_state

        def set_boot_device(self, device):
            self.boot_device = device
            return True

        def read_sensor(self, sensor_name):
            return self.sensors.get(sensor_name, 0.0)

        def get_all_sensors(self):
            return self.sensors.copy()

    return MockHardwareAPI()


@pytest.fixture
def mock_ipmi_client():
    """Mock IPMI client fixture."""
    class MockIPMIClient:
        def __init__(self, host="192.168.1.1", user="admin", password=""):
            self.host = host
            self.user = user
            self._connected = True
            self.sdr_cache = {}
            self.sel_entries = []

        def connect(self):
            self._connected = True
            return True

        def disconnect(self):
            self._connected = False

        def is_connected(self):
            return self._connected

        def get_sensor_reading(self, sensor_name):
            sensor_map = {
                "CPU Temp": 45.0,
                "System Temp": 38.0,
                "Fan 1": 5000.0,
                "Fan 2": 5100.0,
                "12V": 12.1,
                "5V": 5.0,
                "3.3V": 3.3,
            }
            return sensor_map.get(sensor_name)

        def get_sdr(self):
            return self.sdr_cache

        def get_sel(self):
            return self.sel_entries

    return MockIPMIClient


@pytest.fixture
def mock_redfish_client():
    """Mock Redfish client fixture."""
    class MockRedfishClient:
        def __init__(self, host="192.168.1.2", user="admin", password=""):
            self.host = host
            self.user = user
            self._connected = True
            self.systems_data = {
                "Id": "1",
                "Model": "TestServer",
                "Manufacturer": "TestVendor",
                "Status": {"Health": "OK"},
                "ProcessorSummary": {"Count": 2, "Model": "Xeon"},
                "MemorySummary": {"TotalSystemMemoryGiB": 256},
            }
            self.chassis_data = {
                "Id": "1",
                "Model": "RackMount",
                "Manufacturer": "TestVendor",
                "Status": {"Health": "OK"},
            }
            self.managers_data = {
                "Id": "BMC1",
                "Model": "iDRAC",
                "FirmwareVersion": "3.2.1",
                "Status": {"Health": "OK"},
            }

        def connect(self):
            self._connected = True
            return True

        def disconnect(self):
            self._connected = False

        def get_systems(self):
            return self.systems_data

        def get_chassis(self):
            return self.chassis_data

        def get_managers(self):
            return self.managers_data

        def patch_system(self, data):
            self.systems_data.update(data)
            return True

    return MockRedfishClient
