"""
Component enumeration and probing utilities.
"""

from typing import Any, Dict, List, Optional
import logging


class ComponentProbeError(Exception):
    """Exception raised by component probe failures."""
    pass


class ComponentProbe:
    """
    Component enumeration utility.

    Probes system components via sysfs, lspci, and system APIs.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._logger = logger or logging.getLogger(__name__)

    def probe_cpu(self) -> Dict[str, Any]:
        """
        Probe CPU components.

        Returns dictionary with CPU details.
        """
        info = {
            "count": 0,
            "model": "Unknown",
            "cores": 0,
            "threads": 0,
            "frequency_mhz": 0,
            "architecture": "x86_64",
        }

        try:
            # Try to read from /proc/cpuinfo
            cpuinfo_path = "/proc/cpuinfo"
            with open(cpuinfo_path, 'r') as f:
                content = f.read()

            processor_count = content.count("processor\t:")
            info["count"] = processor_count if processor_count > 0 else 1

            for line in content.split("\n"):
                if line.startswith("model name"):
                    info["model"] = line.split(":")[1].strip()
                    break

            # Parse core count from siblings
            cores = 0
            for line in content.split("\n"):
                if line.startswith("cpu cores"):
                    cores = int(line.split(":")[1].strip())
                    break
            info["cores"] = cores

        except FileNotFoundError:
            self._logger.warning("/proc/cpuinfo not found")
        except Exception as e:
            self._logger.warning(f"Failed to probe CPU: {e}")

        return info

    def probe_memory(self) -> Dict[str, Any]:
        """
        Probe memory components.

        Returns dictionary with memory details.
        """
        info = {
            "total_kb": 0,
            "available_kb": 0,
            "total_gb": 0.0,
            "available_gb": 0.0,
            "ecc_enabled": False,
            "slots_used": 0,
            "slots_total": 0,
        }

        try:
            meminfo_path = "/proc/meminfo"
            with open(meminfo_path, 'r') as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        info["total_kb"] = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        info["available_kb"] = int(line.split()[1])

            info["total_gb"] = info["total_kb"] / (1024 * 1024)
            info["available_gb"] = info["available_kb"] / (1024 * 1024)

        except FileNotFoundError:
            self._logger.warning("/proc/meminfo not found")
        except Exception as e:
            self._logger.warning(f"Failed to probe memory: {e}")

        return info

    def probe_storage_devices(self) -> List[Dict[str, Any]]:
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

    def probe_network_interfaces(self) -> List[Dict[str, Any]]:
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

    def probe_pcie_devices(self) -> List[Dict[str, Any]]:
        """
        Probe PCIe devices.

        Returns list of PCIe device information.
        """
        devices = []

        try:
            import subprocess
            result = subprocess.run(
                ["lspci", "-D", "-n"],
                capture_output=True,
                text=True,
                timeout=5
            )
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append({
                            "slot": parts[0],
                            "class_id": parts[1],
                        })
        except Exception as e:
            self._logger.warning(f"Failed to probe PCIe devices: {e}")

        return devices

    def probe_all(self) -> Dict[str, Any]:
        """
        Probe all components.

        Returns comprehensive component information.
        """
        return {
            "cpu": self.probe_cpu(),
            "memory": self.probe_memory(),
            "storage": self.probe_storage_devices(),
            "network": self.probe_network_interfaces(),
            "pcie": self.probe_pcie_devices(),
        }
