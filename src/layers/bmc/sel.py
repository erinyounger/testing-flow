"""
System Event Log (SEL) tests.
"""

from typing import Any, Dict, List
import logging
from datetime import datetime


class SelManager:
    """
    System Event Log manager.

    Handles event logging, log clearing, and alert configuration.
    """

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._sel_entries: List[Dict[str, Any]] = []

    def add_entry(self, entry: Dict[str, Any]) -> bool:
        """Add an entry to the SEL."""
        self._sel_entries.append(entry)
        return True

    def clear_log(self) -> bool:
        """Clear the SEL."""
        self._sel_entries.clear()
        return True

    def get_entries(self) -> List[Dict[str, Any]]:
        """Get all SEL entries."""
        return self._sel_entries.copy()

    def configure_alert(self, alert_type: str, enabled: bool) -> bool:
        """Configure alert (PET/SNMP/email)."""
        self._logger.info(f"Alert {alert_type} configured: enabled={enabled}")
        return True

    def is_overflow(self) -> bool:
        """Check if SEL is in overflow state."""
        return len(self._sel_entries) > 1000


class MockSelManager(SelManager):
    """
    Mock SEL manager for testing.
    """

    def __init__(self):
        super().__init__()
        # Add some sample entries
        self.add_entry({
            "id": 1,
            "timestamp": "2024-01-15T10:30:00",
            "sensor": "CPU Temp",
            "event": "Upper Non-Critical going high",
            "severity": "Warning",
        })
        self.add_entry({
            "id": 2,
            "timestamp": "2024-01-15T10:35:00",
            "sensor": "System Temp",
            "event": "Normal",
            "severity": "OK",
        })


class SelTests:
    """
    SEL test suite.

    Tests event log enumeration, timestamp validation, log clearing,
    alert configuration, and overflow handling.
    """

    def __init__(self, sel_manager: SelManager = None):
        self._sel = sel_manager or MockSelManager()
        self._logger = logging.getLogger(__name__)

    def event_log_enumeration(self) -> Dict[str, Any]:
        """
        Enumerate SEL entries.

        Returns dict with test result.
        """
        result = {"test": "event_log_enumeration", "passed": False, "errors": []}

        try:
            entries = self._sel.get_entries()

            if entries is None:
                result["errors"].append("SEL enumeration returned None")
                return result

            # Check for required fields in entries
            required_fields = ["id", "timestamp", "sensor", "event"]
            for entry in entries:
                for field in required_fields:
                    if field not in entry:
                        result["errors"].append(f"Entry missing field: {field}")
                        return result

            result["passed"] = True
            result["data"] = {"entry_count": len(entries)}
            self._logger.info(f"SEL enumeration passed: {len(entries)} entries")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"SEL enumeration failed: {e}")

        return result

    def event_timestamp_validation(self) -> Dict[str, Any]:
        """
        Validate SEL event timestamps.

        Returns dict with test result.
        """
        result = {"test": "event_timestamp_validation", "passed": False, "errors": []}

        try:
            entries = self._sel.get_entries()

            for entry in entries:
                timestamp_str = entry.get("timestamp", "")
                try:
                    datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                except ValueError:
                    result["errors"].append(f"Invalid timestamp format: {timestamp_str}")
                    return result

            result["passed"] = True
            result["data"] = {"validated_entries": len(entries)}
            self._logger.info("SEL timestamp validation passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"SEL timestamp validation failed: {e}")

        return result

    def log_clear_operation(self) -> Dict[str, Any]:
        """
        Test SEL log clearing.

        Returns dict with test result.
        """
        result = {"test": "log_clear_operation", "passed": False, "errors": []}

        try:
            initial_count = len(self._sel.get_entries())

            success = self._sel.clear_log()
            if not success:
                result["errors"].append("Clear operation failed")
                return result

            cleared_count = len(self._sel.get_entries())
            if cleared_count != 0:
                result["errors"].append(f"Log not cleared: {cleared_count} entries remain")
                return result

            result["passed"] = True
            result["data"] = {
                "initial_count": initial_count,
                "cleared_count": cleared_count,
            }
            self._logger.info("SEL log clear operation passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"SEL log clear operation failed: {e}")

        return result

    def alert_configuration(self) -> Dict[str, Any]:
        """
        Test alert configuration (PET/SNMP/email).

        Returns dict with test result.
        """
        result = {"test": "alert_configuration", "passed": False, "errors": []}

        try:
            alert_types = ["PET", "SNMP", "email"]
            configured = []

            for alert_type in alert_types:
                success = self._sel.configure_alert(alert_type, True)
                if not success:
                    result["errors"].append(f"Failed to configure {alert_type}")
                    return result
                configured.append(alert_type)

            result["passed"] = True
            result["data"] = {"configured_alerts": configured}
            self._logger.info(f"SEL alert configuration passed: {configured}")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"SEL alert configuration failed: {e}")

        return result

    def sel_overflow_handling(self) -> Dict[str, Any]:
        """
        Test SEL overflow handling.

        Returns dict with test result.
        """
        result = {"test": "sel_overflow_handling", "passed": False, "errors": []}

        try:
            is_overflow = self._sel.is_overflow()

            if is_overflow:
                # In real implementation, would log warning or take action
                result["errors"].append("SEL is in overflow state")
                return result

            result["passed"] = True
            result["data"] = {"overflow": False}
            self._logger.info("SEL overflow handling passed")

        except Exception as e:
            result["errors"].append(str(e))
            self._logger.error(f"SEL overflow handling failed: {e}")

        return result

    def run_tests(self) -> Dict[str, Any]:
        """Run all SEL tests."""
        results = []
        total = 5
        passed = 0
        failed = 0
        all_errors = []

        for test_method in [
            self.event_log_enumeration,
            self.event_timestamp_validation,
            self.log_clear_operation,
            self.alert_configuration,
            self.sel_overflow_handling,
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
