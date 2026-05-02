"""
Unit tests for plugin discovery.
"""

import pytest
from src.core.plugin import PluginRegistry, register_plugin, get_registry


class MockPlugin:
    """Mock plugin for testing."""

    def __init__(self, name: str = "mock_plugin"):
        self.name = name
        self.setup_called = False
        self.teardown_called = False


class TestPluginRegistry:
    """Tests for PluginRegistry class."""

    def test_registry_creation(self):
        """Test registry can be created."""
        registry = PluginRegistry()
        assert registry is not None
        assert registry.list_plugins() == []

    def test_register_plugin(self):
        """Test registering a plugin."""
        registry = PluginRegistry()
        plugin = MockPlugin()
        registry.register("test_plugin", plugin)

        assert "test_plugin" in registry.list_plugins()
        assert registry.get("test_plugin") == plugin

    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        registry = PluginRegistry()
        plugin = MockPlugin()
        registry.register("test_plugin", plugin)
        registry.unregister("test_plugin")

        assert "test_plugin" not in registry.list_plugins()
        assert registry.get("test_plugin") is None

    def test_get_all_plugins(self):
        """Test getting all registered plugins."""
        registry = PluginRegistry()
        plugin1 = MockPlugin("plugin1")
        plugin2 = MockPlugin("plugin2")
        registry.register("plugin1", plugin1)
        registry.register("plugin2", plugin2)

        all_plugins = registry.get_all()
        assert len(all_plugins) == 2
        assert "plugin1" in all_plugins
        assert "plugin2" in all_plugins

    def test_get_nonexistent_plugin(self):
        """Test getting a plugin that doesn't exist returns None."""
        registry = PluginRegistry()
        result = registry.get("nonexistent")
        assert result is None

    def test_load_plugin_class(self):
        """Test loading a class from a registered plugin."""
        registry = PluginRegistry()

        class TestPlugin:
            TestClass = type

        registry.register("test", TestPlugin())

        loaded = registry.load_plugin_class("test", "TestClass")
        assert loaded is type

    def test_load_plugin_class_not_found(self):
        """Test loading nonexistent class returns None."""
        registry = PluginRegistry()
        registry.register("test", MockPlugin())

        result = registry.load_plugin_class("test", "NonexistentClass")
        assert result is None

    def test_load_plugin_class_plugin_not_found(self):
        """Test loading class from nonexistent plugin returns None."""
        registry = PluginRegistry()
        result = registry.load_plugin_class("nonexistent", "SomeClass")
        assert result is None


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_get_registry_returns_singleton(self):
        """Test get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_register_plugin_global(self):
        """Test register_plugin registers with global registry."""
        registry = get_registry()
        # Clear any existing plugins
        for name in registry.list_plugins():
            registry.unregister(name)

        plugin = MockPlugin()
        register_plugin("global_test", plugin)

        assert "global_test" in registry.list_plugins()

    def test_discover_from_entry_points_noop_without_plugins(self):
        """Test discover_from_entry_points handles missing entry points gracefully."""
        registry = PluginRegistry()
        discovered = registry.discover_from_entry_points()
        # Should not raise, just return empty list
        assert isinstance(discovered, list)


class TestPluginNamespaceDiscovery:
    """Tests for namespace-based plugin discovery."""

    def test_discover_from_namespace_nonexistent(self):
        """Test discovering from nonexistent namespace."""
        registry = PluginRegistry()
        discovered = registry.discover_from_namespace("nonexistent.namespace")
        assert discovered == []
