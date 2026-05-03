"""
OS detection data models.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class OSInfo:
    """
    Operating system information.

    Attributes:
        id: Unique identifier (e.g., 'ubuntu-kylin', 'deepin', 'anolis')
        name: Display name (e.g., 'Ubuntu Kylin 22.04')
        family: OS family (e.g., 'debian', 'rhel', 'arch')
        version: Version string (e.g., '22.04', '20')
        package_manager: Primary package manager (e.g., 'apt', 'dnf', 'pacman')
        command_paths: Dict mapping command names to full paths
    """
    id: str
    name: str
    family: str
    version: str
    package_manager: str = "apt"
    command_paths: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "family": self.family,
            "version": self.version,
            "package_manager": self.package_manager,
            "command_paths": self.command_paths,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OSInfo":
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            family=data.get("family", ""),
            version=data.get("version", ""),
            package_manager=data.get("package_manager", "apt"),
            command_paths=data.get("command_paths", {}),
        )


@dataclass
class DetectionResult:
    """
    Result from OS detection process.

    Attributes:
        os_info: Detected OS information
        source: Detection source ('config', 'os_release', 'uname', 'unknown')
        confidence: Detection confidence (0.0 to 1.0)
        raw_data: Raw detection data
    """
    os_info: OSInfo
    source: str
    confidence: float = 1.0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.confidence > 0.0
