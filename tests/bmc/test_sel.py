"""
Unit tests for SEL tests.
"""

import pytest
from src.layers.bmc.sel import SelTests, MockSelManager


class TestSelTests:
    """Tests for SelTests class."""

    @pytest.fixture
    def sel_tests(self):
        """Create SelTests instance with mock manager."""
        return SelTests(MockSelManager())

    def test_event_log_enumeration_success(self, sel_tests):
        """Test event log enumeration passes."""
        result = sel_tests.event_log_enumeration()
        assert result["passed"] is True
        assert "entry_count" in result["data"]

    def test_event_timestamp_validation_success(self, sel_tests):
        """Test event timestamp validation passes."""
        result = sel_tests.event_timestamp_validation()
        assert result["passed"] is True
        assert "validated_entries" in result["data"]

    def test_log_clear_operation_success(self, sel_tests):
        """Test log clear operation passes."""
        result = sel_tests.log_clear_operation()
        assert result["passed"] is True
        assert result["data"]["cleared_count"] == 0

    def test_alert_configuration_success(self, sel_tests):
        """Test alert configuration passes."""
        result = sel_tests.alert_configuration()
        assert result["passed"] is True
        assert "configured_alerts" in result["data"]

    def test_sel_overflow_handling_success(self, sel_tests):
        """Test SEL overflow handling passes."""
        result = sel_tests.sel_overflow_handling()
        assert result["passed"] is True
        assert result["data"]["overflow"] is False

    def test_run_tests_all_pass(self, sel_tests):
        """Test run_tests returns aggregate results."""
        results = sel_tests.run_tests()
        assert results["total"] == 5
        assert results["passed"] == 5
        assert results["failed"] == 0


class TestMockSelManager:
    """Tests for MockSelManager."""

    def test_add_entry(self):
        """Test adding entry."""
        manager = MockSelManager()
        initial_count = len(manager.get_entries())
        manager.add_entry({"id": 999, "timestamp": "2024-01-01T00:00:00", "sensor": "Test", "event": "Test", "severity": "OK"})
        assert len(manager.get_entries()) == initial_count + 1

    def test_clear_log(self):
        """Test clearing log."""
        manager = MockSelManager()
        manager.clear_log()
        assert len(manager.get_entries()) == 0

    def test_configure_alert(self):
        """Test configuring alert."""
        manager = MockSelManager()
        result = manager.configure_alert("PET", True)
        assert result is True

    def test_is_overflow_false(self):
        """Test overflow check when not overflow."""
        manager = MockSelManager()
        assert manager.is_overflow() is False
