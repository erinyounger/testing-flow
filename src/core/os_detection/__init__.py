"""
OS Detection & Registry Framework

Hybrid OS detection: YAML config primary, /etc/os-release + uname secondary.
Supports domestic Chinese OS distributions.
"""

from src.core.os_detection.models import OSInfo, DetectionResult
from src.core.os_detection.registry import OSRegistry
from src.core.os_detection.detector import OSDetector

__all__ = [
    "OSInfo",
    "DetectionResult",
    "OSRegistry",
    "OSDetector",
]
