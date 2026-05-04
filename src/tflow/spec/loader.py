"""Spec loader for specification documents."""

from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional


class SpecCategory(Enum):
    """Specification category enum."""

    ARCHITECTURE = "architecture"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    API = "api"
    TEST = "test"
    DEPLOYMENT = "deployment"
    OPERATIONS = "operations"


class SpecScope(Enum):
    """Specification scope enum."""

    GLOBAL = "global"
    PROJECT = "project"
    MODULE = "module"
    COMPONENT = "component"


@dataclass
class SpecLoadResult:
    """Result of loading a specification."""

    success: bool
    path: Optional[str] = None
    content: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SpecLoader:
    """Loader for specification documents.

    Loads and manages specification documents from the file system.
    """

    def __init__(self, base_dir: Optional[str] = None):
        """Initialize spec loader.

        Args:
            base_dir: Base directory for specs. Defaults to docs/specs/
        """
        if base_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            base_dir = project_root / "docs" / "specs"
        else:
            base_dir = Path(base_dir)

        self.base_dir = base_dir

    def resolve_spec_dir(
        self,
        category: Optional[SpecCategory] = None,
        scope: Optional[SpecScope] = None,
    ) -> Path:
        """Resolve spec directory path.

        Args:
            category: Category subdirectory
            scope: Scope subdirectory

        Returns:
            Resolved directory path
        """
        path = self.base_dir

        if category:
            path = path / category.value

        if scope:
            path = path / scope.value

        return path

    def _find_spec_files(self, directory: Path, pattern: str = "*.md") -> List[Path]:
        """Find spec files in directory.

        Args:
            directory: Directory to search
            pattern: File pattern

        Returns:
            List of matching files
        """
        if not directory.exists():
            return []

        return list(directory.rglob(pattern))

    def load_by_category(
        self,
        category: SpecCategory,
    ) -> List[SpecLoadResult]:
        """Load all specs in a category.

        Args:
            category: Category to load

        Returns:
            List of load results
        """
        results = []
        directory = self.resolve_spec_dir(category=category)

        for file_path in self._find_spec_files(directory):
            result = self._load_file(file_path)
            results.append(result)

        return results

    def load_by_scope(
        self,
        scope: SpecScope,
    ) -> List[SpecLoadResult]:
        """Load all specs with a scope.

        Args:
            scope: Scope to load

        Returns:
            List of load results
        """
        results = []
        directory = self.resolve_spec_dir(scope=scope)

        for file_path in self._find_spec_files(directory):
            result = self._load_file(file_path)
            results.append(result)

        return results

    def load_all(self) -> List[SpecLoadResult]:
        """Load all specs.

        Returns:
            List of load results
        """
        results = []

        for file_path in self._find_spec_files(self.base_dir):
            result = self._load_file(file_path)
            results.append(result)

        return results

    def _load_file(self, path: Path) -> SpecLoadResult:
        """Load a single spec file.

        Args:
            path: File path

        Returns:
            Load result
        """
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()

            return SpecLoadResult(
                success=True,
                path=str(path),
                content=content,
                metadata={
                    "name": path.stem,
                    "category": self._get_category_from_path(path),
                    "scope": self._get_scope_from_path(path),
                },
            )
        except Exception as e:
            return SpecLoadResult(
                success=False,
                path=str(path),
                error=str(e),
            )

    def _get_category_from_path(self, path: Path) -> Optional[str]:
        """Get category from file path."""
        parts = path.relative_to(self.base_dir).parts
        if len(parts) > 1:
            return parts[0]
        return None

    def _get_scope_from_path(self, path: Path) -> Optional[str]:
        """Get scope from file path."""
        parts = path.relative_to(self.base_dir).parts
        if len(parts) > 2:
            return parts[1]
        return None

    def load(
        self,
        category: Optional[SpecCategory] = None,
        scope: Optional[SpecScope] = None,
        name: Optional[str] = None,
    ) -> SpecLoadResult:
        """Load a specific spec.

        Args:
            category: Category
            scope: Scope
            name: Spec name (without extension)

        Returns:
            Load result
        """
        directory = self.resolve_spec_dir(category=category, scope=scope)

        if name:
            # Try both .md and other extensions
            for ext in [".md", ".markdown", ".txt"]:
                file_path = directory / f"{name}{ext}"
                if file_path.exists():
                    return self._load_file(file_path)

        return SpecLoadResult(
            success=False,
            error="Spec not found",
        )
