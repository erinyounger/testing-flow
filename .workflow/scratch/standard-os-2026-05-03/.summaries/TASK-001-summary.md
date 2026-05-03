# TASK-001: OS Detection & Registry Framework

## Changes
- `src/core/os_detection/__init__.py`: Module init with exports
- `src/core/os_detection/models.py`: OSInfo and DetectionResult dataclasses
- `src/core/os_detection/registry.py`: OSRegistry class for known distributions
- `src/core/os_detection/detector.py`: OSDetector with hybrid detection (config + dynamic)
- `src/core/os_detection/config.yaml`: YAML config with domestic OS distributions
- `tests/test_os_detection.py`: Unit tests (16 tests)

## Verification
- [x] OS detection returns correct OS family for known distributions via /etc/os-release
- [x] Config file overrides dynamic detection when OS is explicitly specified
- [x] Unknown distribution triggers auto-discovery and registers with detected info
- [x] Registry lookup by distro ID returns correct OSInfo

## Tests
- [x] pytest tests/test_os_detection.py -v: 16 passed in 0.05s

## Deviations
- None

## Notes
- TASK-002 can now use OSDetector and OSRegistry as dependencies
- Domestic OS adapters in TASK-002 should register with the same registry pattern
