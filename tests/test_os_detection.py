"""
Unit tests for OS Detection & Registry Framework.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.core.os_detection.models import OSInfo, DetectionResult
from src.core.os_detection.registry import OSRegistry
from src.core.os_detection.detector import OSDetector


class TestOSInfo:
    """Tests for OSInfo dataclass."""

    def test_os_info_creation(self):
        os_info = OSInfo(
            id="ubuntu",
            name="Ubuntu 22.04",
            family="debian",
            version="22.04",
            package_manager="apt",
        )
        assert os_info.id == "ubuntu"
        assert os_info.name == "Ubuntu 22.04"
        assert os_info.family == "debian"
        assert os_info.version == "22.04"
        assert os_info.package_manager == "apt"

    def test_os_info_to_dict(self):
        os_info = OSInfo(
            id="deepin",
            name="Deepin 20",
            family="debian",
            version="20",
            package_manager="apt",
        )
        result = os_info.to_dict()
        assert result["id"] == "deepin"
        assert result["name"] == "Deepin 20"
        assert result["family"] == "debian"

    def test_os_info_from_dict(self):
        data = {
            "id": "anolis",
            "name": "Anolis OS 8",
            "family": "rhel",
            "version": "8",
            "package_manager": "dnf",
        }
        os_info = OSInfo.from_dict(data)
        assert os_info.id == "anolis"
        assert os_info.family == "rhel"


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_detection_result_success(self):
        os_info = OSInfo(
            id="ubuntu",
            name="Ubuntu",
            family="debian",
            version="22.04",
        )
        result = DetectionResult(
            os_info=os_info,
            source="os_release",
            confidence=0.95,
        )
        assert result.success is True
        assert result.source == "os_release"

    def test_detection_result_failure(self):
        os_info = OSInfo(
            id="unknown",
            name="Unknown",
            family="linux",
            version="unknown",
        )
        result = DetectionResult(
            os_info=os_info,
            source="unknown",
            confidence=0.0,
        )
        assert result.success is False


class TestOSRegistry:
    """Tests for OSRegistry."""

    def test_registry_register_and_lookup(self):
        registry = OSRegistry()
        os_info = OSInfo(
            id="ubuntu-kylin",
            name="Ubuntu Kylin",
            family="debian",
            version="22.04",
        )
        registry.register(os_info)
        result = registry.lookup("ubuntu-kylin")
        assert result is not None
        assert result.id == "ubuntu-kylin"
        assert result.name == "Ubuntu Kylin"

    def test_registry_lookup_unknown(self):
        registry = OSRegistry()
        result = registry.lookup("nonexistent")
        assert result is None

    def test_registry_lookup_by_name(self):
        registry = OSRegistry()
        os_info = OSInfo(
            id="deepin",
            name="Deepin 20",
            family="debian",
            version="20",
        )
        registry.register(os_info)
        result = registry.lookup_by_name("Deepin")
        assert result is not None
        assert result.id == "deepin"

    def test_registry_get_all(self):
        registry = OSRegistry()
        registry.register(OSInfo(id="a", name="A", family="x", version="1"))
        registry.register(OSInfo(id="b", name="B", family="y", version="2"))
        all_os = registry.get_all()
        assert len(all_os) == 2
        assert "a" in all_os
        assert "b" in all_os


class TestOSDetector:
    """Tests for OSDetector hybrid detection."""

    @patch.object(Path, "exists", return_value=False)
    def test_detector_default_init(self, mock_exists):
        detector = OSDetector()
        assert detector.registry is not None

    def test_detector_explicit_os_override(self):
        detector = OSDetector()
        detector.set_explicit_os("ubuntu")
        result = detector.detect()
        assert result.source == "config"
        assert result.confidence == 1.0
        assert result.os_info.id == "ubuntu"

    def test_detector_explicit_os_not_found(self):
        detector = OSDetector()
        detector.set_explicit_os("nonexistent-os")
        # Falls back to detection
        result = detector.detect()
        assert result.source != "config" or result.confidence < 1.0

    @patch("builtins.open", new_callable=mock_open, read_data="")
    @patch.object(Path, "exists", return_value=False)
    def test_detector_os_release_not_found(self, mock_exists, mock_file):
        detector = OSDetector()
        result = detector.detect()
        # Should fallback to uname or unknown
        assert result.source in ("uname", "unknown")

    def test_registry_lookup_returns_correct_os(self):
        """Test that registry lookup returns correct OSInfo for known distributions."""
        registry = OSRegistry()
        config_path = Path(__file__).parent.parent / "src" / "core" / "os_detection" / "config.yaml"
        if config_path.exists():
            registry.load_config(config_path)
            # Test ubuntu lookup
            ubuntu = registry.lookup("ubuntu")
            assert ubuntu is not None
            assert ubuntu.family == "debian"
            # Test domestic OS lookup
            deepin = registry.lookup("deepin")
            if deepin:
                assert deepin.family == "debian"

    def test_infer_family(self):
        """Test OS family inference from distro ID."""
        detector = OSDetector()
        assert detector._infer_family("debian") == "debian"
        assert detector._infer_family("ubuntu") == "debian"
        assert detector._infer_family("deepin") == "debian"
        assert detector._infer_family("centos") == "rhel"
        assert detector._infer_family("anolis") == "rhel"
        assert detector._infer_family("arch") == "arch"
        assert detector._infer_family("opensuse") == "suse"

    def test_infer_package_manager(self):
        """Test package manager inference from distro ID."""
        detector = OSDetector()
        assert detector._infer_package_manager("debian") == "apt"
        assert detector._infer_package_manager("arch") == "pacman"
        assert detector._infer_package_manager("centos") == "dnf"
        assert detector._infer_package_manager("opensuse") == "zypper"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
