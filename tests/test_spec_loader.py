"""Tests for spec loader."""

import pytest
import tempfile
import shutil
from pathlib import Path

from tflow.spec import SpecLoader, SpecCategory, SpecScope, SpecLoadResult


class TestSpecCategory:
    """Test SpecCategory enum."""

    def test_values(self):
        """Test category values."""
        assert SpecCategory.ARCHITECTURE.value == "architecture"
        assert SpecCategory.DESIGN.value == "design"
        assert SpecCategory.IMPLEMENTATION.value == "implementation"
        assert SpecCategory.API.value == "api"
        assert SpecCategory.TEST.value == "test"
        assert SpecCategory.DEPLOYMENT.value == "deployment"
        assert SpecCategory.OPERATIONS.value == "operations"


class TestSpecScope:
    """Test SpecScope enum."""

    def test_values(self):
        """Test scope values."""
        assert SpecScope.GLOBAL.value == "global"
        assert SpecScope.PROJECT.value == "project"
        assert SpecScope.MODULE.value == "module"
        assert SpecScope.COMPONENT.value == "component"


class TestSpecLoadResult:
    """Test SpecLoadResult class."""

    def test_success_result(self):
        """Test creating successful result."""
        result = SpecLoadResult(
            success=True,
            path="/path/to/spec.md",
            content="# Test Spec",
        )

        assert result.success
        assert result.path == "/path/to/spec.md"
        assert result.content == "# Test Spec"
        assert result.error is None

    def test_failure_result(self):
        """Test creating failure result."""
        result = SpecLoadResult(
            success=False,
            path="/path/to/spec.md",
            error="File not found",
        )

        assert not result.success
        assert result.error == "File not found"


class TestSpecLoader:
    """Test SpecLoader class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.loader = SpecLoader(base_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resolve_spec_dir(self):
        """Test resolving spec directory."""
        # Create directory structure
        arch_dir = Path(self.temp_dir) / "architecture"
        arch_dir.mkdir(parents=True)

        path = self.loader.resolve_spec_dir(category=SpecCategory.ARCHITECTURE)
        assert path == arch_dir

        path = self.loader.resolve_spec_dir(
            category=SpecCategory.ARCHITECTURE,
            scope=SpecScope.GLOBAL,
        )
        assert path == arch_dir / "global"

    def test_load_file(self):
        """Test loading a single file."""
        # Create test file
        spec_file = Path(self.temp_dir) / "test-spec.md"
        spec_file.write_text("# Test Specification\n\nThis is a test.")

        result = self.loader._load_file(spec_file)
        assert result.success
        assert "Test Specification" in result.content

    def test_load_all(self):
        """Test loading all specs."""
        # Create test files
        spec1 = Path(self.temp_dir) / "spec1.md"
        spec1.write_text("# Spec 1")

        subdir = Path(self.temp_dir) / "design"
        subdir.mkdir()
        spec2 = subdir / "spec2.md"
        spec2.write_text("# Spec 2")

        results = self.loader.load_all()
        assert len(results) == 2

    def test_load_by_category(self):
        """Test loading by category."""
        # Create category directory and file
        arch_dir = Path(self.temp_dir) / "architecture"
        arch_dir.mkdir()
        spec_file = arch_dir / "arch-spec.md"
        spec_file.write_text("# Architecture Spec")

        results = self.loader.load_by_category(SpecCategory.ARCHITECTURE)
        assert len(results) == 1
        assert results[0].success

    def test_load_by_scope(self):
        """Test loading by scope."""
        # Create scope directory and file
        global_dir = Path(self.temp_dir) / "global"
        global_dir.mkdir()
        spec_file = global_dir / "global-spec.md"
        spec_file.write_text("# Global Spec")

        results = self.loader.load_by_scope(SpecScope.GLOBAL)
        assert len(results) == 1
        assert results[0].success

    def test_load_specific_spec(self):
        """Test loading a specific spec."""
        # Create design directory and file
        design_dir = Path(self.temp_dir) / "design"
        design_dir.mkdir()
        spec_file = design_dir / "api-spec.md"
        spec_file.write_text("# API Specification")

        result = self.loader.load(
            category=SpecCategory.DESIGN,
            name="api-spec",
        )
        assert result.success
        assert "API Specification" in result.content

    def test_load_nonexistent_spec(self):
        """Test loading nonexistent spec."""
        result = self.loader.load(name="nonexistent-spec")
        assert not result.success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
