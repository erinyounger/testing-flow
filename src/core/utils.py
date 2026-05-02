"""
Shared utilities for the server test framework.

Includes: logger, result aggregator, hardware probes.
"""

import logging
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.core.layer import TestStatus


# Logger utilities

def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    return logger


# Result aggregator

@dataclass
class TestResultEntry:
    """Single test result entry."""
    test_name: str
    status: TestStatus
    duration: float
    message: str = ""
    layer: str = ""
    error: Optional[str] = None


class ResultAggregator:
    """
    Aggregates test results across layers.

    Collects and summarizes test results for reporting.
    """

    def __init__(self):
        self._results: List[TestResultEntry] = []
        self._start_time: Optional[float] = None
        self._end_time: Optional[float] = None

    def start(self) -> None:
        """Mark the start of result collection."""
        self._start_time = time.time()

    def end(self) -> None:
        """Mark the end of result collection."""
        self._end_time = time.time()

    def add_result(self, result: TestResultEntry) -> None:
        """Add a test result entry."""
        self._results.append(result)

    def add_results(self, results: List[TestResultEntry]) -> None:
        """Add multiple test result entries."""
        self._results.extend(results)

    def get_results(self) -> List[TestResultEntry]:
        """Get all result entries."""
        return self._results.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        total = len(self._results)
        passed = sum(1 for r in self._results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self._results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self._results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in self._results if r.status == TestStatus.ERROR)

        duration = 0.0
        if self._start_time and self._end_time:
            duration = self._end_time - self._start_time
        elif self._start_time:
            duration = time.time() - self._start_time

        by_layer: Dict[str, Dict[str, int]] = {}
        for r in self._results:
            if r.layer not in by_layer:
                by_layer[r.layer] = {"passed": 0, "failed": 0, "skipped": 0, "error": 0}
            if r.status == TestStatus.PASSED:
                by_layer[r.layer]["passed"] += 1
            elif r.status == TestStatus.FAILED:
                by_layer[r.layer]["failed"] += 1
            elif r.status == TestStatus.SKIPPED:
                by_layer[r.layer]["skipped"] += 1
            elif r.status == TestStatus.ERROR:
                by_layer[r.layer]["error"] += 1

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "errors": errors,
            "duration_seconds": duration,
            "by_layer": by_layer,
        }

    def get_failed_tests(self) -> List[TestResultEntry]:
        """Get all failed test entries."""
        return [r for r in self._results if r.status == TestStatus.FAILED]

    def get_errors(self) -> List[TestResultEntry]:
        """Get all error test entries."""
        return [r for r in self._results if r.status == TestStatus.ERROR]


# Hardware probes

class HardwareProbeError(Exception):
    """Exception raised by hardware probe failures."""
    pass


class HardwareProbe:
    """
    Hardware enumeration utility.

    Probes system hardware and returns structured information.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or get_logger(__name__)

    def probe_cpu(self) -> Dict[str, Any]:
        """
        Probe CPU information.

        Returns dictionary with CPU details.
        """
        info = {
            "count": 0,
            "model": "Unknown",
            "cores": 0,
            "threads": 0,
            "frequency_mhz": 0,
        }

        try:
            # Try to read from /proc/cpuinfo
            cpuinfo_path = "/proc/cpuinfo"
            with open(cpuinfo_path, 'r') as f:
                content = f.read()

            # Count processors
            processor_count = content.count("processor\t:")
            info["count"] = processor_count if processor_count > 0 else 1

            # Parse model name
            for line in content.split("\n"):
                if line.startswith("model name"):
                    info["model"] = line.split(":")[1].strip()
                    break

        except FileNotFoundError:
            self._logger.warning("/proc/cpuinfo not found, using mock data")
        except Exception as e:
            self._logger.warning(f"Failed to probe CPU: {e}")

        return info

    def probe_memory(self) -> Dict[str, Any]:
        """
        Probe memory information.

        Returns dictionary with memory details.
        """
        info = {
            "total_kb": 0,
            "available_kb": 0,
            "total_gb": 0.0,
            "available_gb": 0.0,
        }

        try:
            meminfo_path = "/proc/meminfo"
            with open(meminfo_path, 'r') as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        info["total_kb"] = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        info["available_kb"] = int(line.split()[1])
                        break

            info["total_gb"] = info["total_kb"] / (1024 * 1024)
            info["available_gb"] = info["available_kb"] / (1024 * 1024)

        except FileNotFoundError:
            self._logger.warning("/proc/meminfo not found, using mock data")
        except Exception as e:
            self._logger.warning(f"Failed to probe memory: {e}")

        return info

    def probe_storage(self) -> List[Dict[str, Any]]:
        """
        Probe storage devices.

        Returns list of storage device information.
        """
        devices = []

        try:
            import subprocess
            result = subprocess.run(
                ["lsblk", "-d", "-n", "-o", "NAME,TYPE,SIZE,MODEL"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append({
                            "name": parts[0],
                            "type": parts[1] if len(parts) > 1 else "unknown",
                            "size": parts[2] if len(parts) > 2 else "unknown",
                        })
        except Exception as e:
            self._logger.warning(f"Failed to probe storage: {e}")

        return devices

    def probe_network(self) -> List[Dict[str, Any]]:
        """
        Probe network interfaces.

        Returns list of network interface information.
        """
        interfaces = []

        try:
            import subprocess
            result = subprocess.run(
                ["ip", "-o", "link", "show"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        name = parts[1].strip()
                        state = "up" if "state UP" in line else "down"
                        interfaces.append({
                            "name": name,
                            "state": state,
                        })
        except Exception as e:
            self._logger.warning(f"Failed to probe network: {e}")

        return interfaces

    def probe_all(self) -> Dict[str, Any]:
        """
        Probe all hardware components.

        Returns comprehensive hardware information.
        """
        return {
            "cpu": self.probe_cpu(),
            "memory": self.probe_memory(),
            "storage": self.probe_storage(),
            "network": self.probe_network(),
        }
