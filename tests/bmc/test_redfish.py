"""
Unit tests for Redfish tests.
"""

import pytest
from src.layers.bmc.redfish import RedfishTests, MockRedfishClient


class TestRedfishTests:
    """Tests for RedfishTests class."""

    @pytest.fixture
    def redfish_tests(self):
        """Create RedfishTests instance with mock client."""
        return RedfishTests(MockRedfishClient())

    def test_systems_endpoint_get_success(self, redfish_tests):
        """Test GET /Systems endpoint passes."""
        result = redfish_tests.systems_endpoint_get()
        assert result["passed"] is True
        assert "system_id" in result["data"]

    def test_chassis_endpoint_get_success(self, redfish_tests):
        """Test GET /Chassis endpoint passes."""
        result = redfish_tests.chassis_endpoint_get()
        assert result["passed"] is True
        assert "chassis_id" in result["data"]

    def test_managers_endpoint_get_success(self, redfish_tests):
        """Test GET /Managers endpoint passes."""
        result = redfish_tests.managers_endpoint_get()
        assert result["passed"] is True
        assert "manager_id" in result["data"]

    def test_patch_operation_success(self, redfish_tests):
        """Test PATCH /Systems passes."""
        result = redfish_tests.patch_operation()
        assert result["passed"] is True
        assert "patched_fields" in result["data"]

    def test_schema_validation_success(self, redfish_tests):
        """Test schema validation passes."""
        result = redfish_tests.schema_validation()
        assert result["passed"] is True
        assert "schema_valid" in result["data"]

    def test_run_tests_all_pass(self, redfish_tests):
        """Test run_tests returns aggregate results."""
        results = redfish_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0


class TestMockRedfishClient:
    """Tests for MockRedfishClient."""

    def test_connection(self):
        """Test mock client connection."""
        client = MockRedfishClient()
        assert client.connect() is True

    def test_disconnect(self):
        """Test mock client disconnect."""
        client = MockRedfishClient()
        client.disconnect()

    def test_get_systems(self):
        """Test get systems."""
        client = MockRedfishClient()
        systems = client.get_systems()
        assert isinstance(systems, dict)
        assert "Id" in systems
        assert "Model" in systems

    def test_get_chassis(self):
        """Test get chassis."""
        client = MockRedfishClient()
        chassis = client.get_chassis()
        assert isinstance(chassis, dict)
        assert "Id" in chassis

    def test_get_managers(self):
        """Test get managers."""
        client = MockRedfishClient()
        managers = client.get_managers()
        assert isinstance(managers, dict)
        assert "Id" in managers
        assert "FirmwareVersion" in managers

    def test_patch_system(self):
        """Test patch system."""
        client = MockRedfishClient()
        result = client.patch_system({"Model": "NewModel"})
        assert result is True
