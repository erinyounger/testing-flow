# TASK-001: Implement core test framework with layered architecture

## Changes
- `src/core/__init__.py`: Core package initialization with exports
- `src/core/layer.py`: Layer abstraction base classes (LayerContext, LayerProtocol, LayerResult, HardwareInfo, ComponentInfo, ServerContext)
- `src/core/runner.py`: TestRunnerEngine class for multi-layer test orchestration
- `src/core/plugin.py`: PluginRegistry using importlib.metadata entry_points for dynamic discovery
- `src/core/fixtures.py`: Shared pytest fixtures (server_context, hardware_info, component_map, layer_context)
- `src/core/config.py`: Configuration management with YAML support and env var overrides
- `src/core/utils.py`: Shared utilities (get_logger, ResultAggregator, HardwareProbe)
- `tests/unit/test_layer.py`: Unit tests for layer abstraction (15 tests)
- `tests/unit/test_plugin.py`: Unit tests for plugin discovery (11 tests)
- `tests/integration/test_core_integration.py`: Integration tests for core framework (9 tests)
- `conftest.py`: Pytest configuration exposing all fixtures
- `setup.py`: Package setup with entry points for plugin registration
- `server-test.yaml`: Configuration file for server test framework

## Verification
- [x] Framework can discover and load tests from multiple layers via pytest plugin system: Verified with pytest --collect-only showing 35 tests
- [x] Layer context can be propagated from Hardware -> Component -> BMC/BIOS hierarchy: Verified via TestContextPropagation tests
- [x] Plugin registration via entry points successfully discovers custom test modules: PluginRegistry with importlib.metadata support
- [x] Base test fixtures (server_context, hardware_info, component_map) are available to all layers: Verified via conftest.py

## Tests
- [x] `pytest tests/unit/test_layer.py -v`: 15 passed
- [x] `pytest tests/unit/test_plugin.py -v`: 11 passed
- [x] `pytest tests/integration/test_core_integration.py -v`: 9 passed
- [x] `pytest --collect-only`: Shows all 35 tests discovered

## Deviations
- None

## Notes
- The `TestStatus` and `TestRunnerEngine` classes generate pytest collection warnings due to their names starting with "Test" - this is cosmetic and does not affect functionality
- TASK-002, TASK-003, and TASK-004 can now be executed as they all depend on TASK-001
