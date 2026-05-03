# TASK-002: Command Adapter Layer & YAML Integration

## Changes
- `src/core/cmd_adapter/__init__.py`: Module init with exports
- `src/core/cmd_adapter/adapter.py`: CommandAdapter ABC, CommandRegistry, CommandResult
- `src/core/cmd_adapter/commands.py`: os_cmd unified interface function
- `src/core/cmd_adapter/adapters/__init__.py`: Adapter exports
- `src/core/cmd_adapter/adapters/linux.py`: GenericLinuxAdapter implementation
- `src/core/cmd_adapter/adapters/domestic.py`: DomesticOSAdapter for Chinese OS
- `src/core/cmd_adapter/commands.yaml`: YAML config for OS command mappings
- `tests/test_cmd_adapter.py`: Unit tests (22 tests)

## Verification
- [x] os_cmd('info') returns structured system info on any registered OS
- [x] Command adapter registry correctly routes to OS-specific implementation
- [x] YAML config can override default command mappings for any OS
- [x] Unregistered OS falls back to generic Linux adapter

## Tests
- [x] pytest tests/test_cmd_adapter.py -v: 22 passed in 0.05s
- [x] pytest tests/test_os_detection.py tests/test_cmd_adapter.py: 38 passed in 0.07s

## Deviations
- None

## Notes
- Both tasks completed successfully
- OS detection and command adapter layers are independent but work together
- Run `from src.core.cmd_adapter import os_cmd; os_cmd('info')` to test
