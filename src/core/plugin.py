"""
Plugin registry and discovery mechanism.

Uses entry points for dynamic test module discovery.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    Registry for discovering and managing test plugins.

    Uses importlib.metadata entry_points for dynamic discovery
    of custom test modules.
    """

    ENTRY_POINT_GROUP = "server_test_plugins"

    def __init__(self):
        self._plugins: Dict[str, Any] = {}
        self._discovered_entry_points: Set[str] = set()
        self._logger = logging.getLogger(__name__)

    def register(self, name: str, plugin: Any) -> None:
        """
        Manually register a plugin.

        Args:
            name: Plugin identifier
            plugin: Plugin instance or module
        """
        self._plugins[name] = plugin
        self._logger.info(f"Registered plugin: {name}")

    def unregister(self, name: str) -> None:
        """Remove a plugin from the registry."""
        if name in self._plugins:
            del self._plugins[name]
            self._logger.info(f"Unregistered plugin: {name}")

    def get(self, name: str) -> Optional[Any]:
        """Get a registered plugin by name."""
        return self._plugins.get(name)

    def get_all(self) -> Dict[str, Any]:
        """Get all registered plugins."""
        return self._plugins.copy()

    def list_plugins(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._plugins.keys())

    def discover_from_entry_points(self) -> List[str]:
        """
        Discover plugins via entry points.

        Uses importlib.metadata to find installed packages
        that declare server_test_plugins entry points.

        Returns:
            List of discovered plugin names
        """
        discovered = []
        try:
            from importlib.metadata import entry_points

            eps = entry_points()
            # Python 3.10+ uses select(), older uses dict-like access
            if hasattr(eps, 'select'):
                plugin_eps = list(eps.select(group=self.ENTRY_POINT_GROUP))
            else:
                plugin_eps = list(eps.get(self.ENTRY_POINT_GROUP, []))

            for ep in plugin_eps:
                try:
                    plugin_module = importlib.import_module(ep.module)
                    self.register(ep.name, plugin_module)
                    discovered.append(ep.name)
                    self._discovered_entry_points.add(ep.name)
                    self._logger.info(f"Discovered plugin via entry point: {ep.name}")
                except Exception as e:
                    self._logger.error(f"Failed to load plugin {ep.name}: {e}")

        except ImportError:
            # Python < 3.10 fallback
            try:
                from importlib_metadata import entry_points
                eps = entry_points()
                if hasattr(eps, 'select'):
                    plugin_eps = list(eps.select(group=self.ENTRY_POINT_GROUP))
                else:
                    plugin_eps = list(eps.get(self.ENTRY_POINT_GROUP, []))

                for ep in plugin_eps:
                    try:
                        plugin_module = importlib.import_module(ep.module)
                        self.register(ep.name, plugin_module)
                        discovered.append(ep.name)
                        self._discovered_entry_points.add(ep.name)
                        self._logger.info(f"Discovered plugin via entry point: {ep.name}")
                    except Exception as e:
                        self._logger.error(f"Failed to load plugin {ep.name}: {e}")
            except ImportError:
                self._logger.warning("Neither importlib.metadata nor importlib_metadata available")

        return discovered

    def discover_from_namespace(self, namespace: str) -> List[str]:
        """
        Discover plugins from a namespace package.

        Args:
            namespace: Namespace package path (e.g., 'tests.layers')

        Returns:
            List of discovered module names
        """
        discovered = []
        try:
            ns_module = importlib.import_module(namespace)
            if hasattr(ns_module, '__path__'):
                for _, name, is_pkg in importlib.packages_iter():
                    if not is_pkg:
                        continue
                    try:
                        full_name = f"{namespace}.{name}"
                        module = importlib.import_module(full_name)
                        self.register(name, module)
                        discovered.append(name)
                        self._logger.info(f"Discovered plugin from namespace: {full_name}")
                    except Exception as e:
                        self._logger.warning(f"Could not import {name} from {namespace}: {e}")
        except ImportError as e:
            self._logger.warning(f"Namespace {namespace} not found: {e}")

        return discovered

    def load_plugin_class(self, plugin_name: str, class_name: str) -> Optional[type]:
        """
        Load a specific class from a registered plugin.

        Args:
            plugin_name: Name of the registered plugin
            class_name: Name of the class to load

        Returns:
            The class type or None if not found
        """
        plugin = self.get(plugin_name)
        if plugin is None:
            self._logger.error(f"Plugin not found: {plugin_name}")
            return None

        if not hasattr(plugin, class_name):
            self._logger.error(f"Class {class_name} not found in plugin {plugin_name}")
            return None

        return getattr(plugin, class_name)


# Global registry instance
_global_registry: Optional[PluginRegistry] = None


def get_registry() -> PluginRegistry:
    """Get the global plugin registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = PluginRegistry()
    return _global_registry


def register_plugin(name: str, plugin: Any) -> None:
    """Register a plugin with the global registry."""
    get_registry().register(name, plugin)


def discover_plugins() -> List[str]:
    """Discover plugins via entry points using the global registry."""
    return get_registry().discover_from_entry_points()
