"""
OS Detector with hybrid detection mode.

Primary: YAML config file
Secondary: /etc/os-release + uname dynamic detection
"""

import logging
import subprocess
from pathlib import Path
from typing import Optional

import yaml

from src.core.os_detection.models import DetectionResult, OSInfo
from src.core.os_detection.registry import OSRegistry

logger = logging.getLogger(__name__)


class OSDetector:
    """
    Hybrid OS detector with config primary and dynamic secondary.

    Detection order:
    1. Check YAML config for explicit OS specification
    2. Parse /etc/os-release for known distributions
    3. Fallback to uname for kernel-level detection
    4. Auto-register unknown distributions with detected info
    """

    def __init__(self, registry: Optional[OSRegistry] = None, config_path: Optional[Path] = None):
        """
        Initialize OS detector.

        Args:
            registry: OS registry instance (creates new if None)
            config_path: Path to YAML config (uses default if None)
        """
        self.registry = registry or OSRegistry()
        self._explicit_os: Optional[str] = None

        # Load config if path provided or using default
        if config_path:
            self.registry.load_config(config_path)
        else:
            default_config = Path(__file__).parent / "config.yaml"
            if default_config.exists():
                self.registry.load_config(default_config)

    def set_explicit_os(self, os_id: str) -> None:
        """
        Set explicit OS override (config primary mode).

        Args:
            os_id: OS ID to use instead of detection
        """
        self._explicit_os = os_id
        logger.info(f"Explicit OS set to: {os_id}")

    def detect(self) -> DetectionResult:
        """
        Detect OS using hybrid detection.

        Returns:
            DetectionResult with OS info and detection metadata
        """
        # Priority 1: Explicit OS override (config primary)
        if self._explicit_os:
            os_info = self.registry.lookup(self._explicit_os)
            if os_info:
                return DetectionResult(
                    os_info=os_info,
                    source="config",
                    confidence=1.0,
                    raw_data={"explicit": self._explicit_os},
                )
            logger.warning(f"Explicit OS '{self._explicit_os}' not found in registry")

        # Priority 2: Check /etc/os-release
        os_info = self._detect_from_os_release()
        if os_info:
            return DetectionResult(
                os_info=os_info,
                source="os_release",
                confidence=0.95,
                raw_data=self._read_os_release(),
            )

        # Priority 3: Fallback to uname
        os_info = self._detect_from_uname()
        if os_info:
            return DetectionResult(
                os_info=os_info,
                source="uname",
                confidence=0.7,
                raw_data=self._read_uname(),
            )

        # Fallback: Generic Linux
        return DetectionResult(
            os_info=OSInfo(
                id="unknown",
                name="Unknown Linux",
                family="linux",
                version="unknown",
                package_manager="apt",
            ),
            source="unknown",
            confidence=0.0,
            raw_data={},
        )

    def _detect_from_os_release(self) -> Optional[OSInfo]:
        """Detect OS from /etc/os-release file."""
        os_release = self._read_os_release()
        if not os_release:
            return None

        distro_id = os_release.get("ID", "").strip()
        if not distro_id:
            return None

        # Check registry first
        os_info = self.registry.lookup(distro_id)
        if os_info:
            return os_info

        # Auto-register unknown distribution with detected info
        name = os_release.get("NAME", os_release.get("ID", "")).strip()
        version = os_release.get("VERSION_ID", "").strip()
        version = version or os_release.get("VERSION", "").strip()

        # Determine family from ID
        family = self._infer_family(distro_id)

        # Auto-register
        auto_os = OSInfo(
            id=distro_id,
            name=name,
            family=family,
            version=version,
            package_manager=self._infer_package_manager(distro_id),
        )
        self.registry.register(auto_os)
        logger.info(f"Auto-registered unknown OS: {distro_id}")
        return auto_os

    def _detect_from_uname(self) -> Optional[OSInfo]:
        """Fallback detection using uname."""
        try:
            result = subprocess.run(
                ["uname", "-srv"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                uname_output = result.stdout.strip()
                # Parse kernel info
                if "Linux" in uname_output:
                    return OSInfo(
                        id="linux",
                        name=uname_output,
                        family="linux",
                        version=uname_output.split()[2] if len(uname_output.split()) > 2 else "unknown",
                        package_manager="apt",
                    )
        except Exception as e:
            logger.debug(f"uname detection failed: {e}")
        return None

    def _read_os_release(self) -> dict:
        """Read /etc/os-release file."""
        try:
            os_release_path = Path("/etc/os-release")
            if not os_release_path.exists():
                return {}

            result = {}
            with open(os_release_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if "=" in line and not line.startswith("#"):
                        key, _, value = line.partition("=")
                        value = value.strip('"').strip("'")
                        result[key] = value
            return result
        except Exception as e:
            logger.debug(f"Failed to read /etc/os-release: {e}")
            return {}

    def _read_uname(self) -> dict:
        """Read uname output."""
        try:
            result = subprocess.run(
                ["uname", "-m"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                return {"kernel": result.stdout.strip()}
        except Exception:
            pass
        return {}

    def _infer_family(self, distro_id: str) -> str:
        """Infer OS family from distro ID."""
        debian_like = {"debian", "ubuntu", "linuxmint", "deepin", "ubuntu-kylin"}
        rhel_like = {"rhel", "centos", "fedora", "rocky", "alma", "anolis"}
        arch_like = {"arch", "manjaro", "endeavouros"}
        suse_like = {"sles", "suse", "opensuse"}

        distro_lower = distro_id.lower()
        if distro_lower in debian_like:
            return "debian"
        elif distro_lower in rhel_like:
            return "rhel"
        elif distro_lower in arch_like:
            return "arch"
        elif distro_lower in suse_like:
            return "suse"
        return "linux"

    def _infer_package_manager(self, distro_id: str) -> str:
        """Infer package manager from distro ID."""
        pacman_distros = {"arch", "manjaro", "endeavouros"}
        dnf_distros = {"rhel", "centos", "fedora", "rocky", "alma", "anolis"}
        zypper_distros = {"sles", "suse", "opensuse"}

        distro_lower = distro_id.lower()
        if distro_lower in pacman_distros:
            return "pacman"
        elif distro_lower in dnf_distros:
            return "dnf"
        elif distro_lower in zypper_distros:
            return "zypper"
        return "apt"
