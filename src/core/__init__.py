"""
Server Test Framework - Core Package

A layered test architecture for server testing with plugin-based extensibility.
"""

__version__ = "0.1.0"

from src.core.layer import LayerContext, LayerProtocol, LayerResult
from src.core.runner import TestRunnerEngine
from src.core.plugin import PluginRegistry
from src.core.config import Config

__all__ = [
    "LayerContext",
    "LayerProtocol",
    "LayerResult",
    "TestRunnerEngine",
    "PluginRegistry",
    "Config",
]
