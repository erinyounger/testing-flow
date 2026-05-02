import pytest
import time
from tflow.engine.wave_scheduler import WaveScheduler


class TestWaveScheduler:
    """WaveScheduler TDD tests"""

    def test_schedule_groups_tasks_by_wave(self):
        """RED: Group by wave field"""
        ws = WaveScheduler()
        tasks = [
            {"id": "TASK-001", "wave": 0},
            {"id": "TASK-002", "wave": 0},
            {"id": "TASK-003", "wave": 1},
            {"id": "TASK-004", "wave": 2},
        ]

        waves = ws.schedule(tasks)

        assert len(waves) == 3
        assert len(waves[0]) == 2  # wave 0: TASK-001, TASK-002
        assert len(waves[1]) == 1  # wave 1: TASK-003
        assert len(waves[2]) == 1  # wave 2: TASK-004

    def test_schedule_handles_missing_wave_field(self):
        """GREEN: Default wave 0 when missing"""
        ws = WaveScheduler()
        tasks = [
            {"id": "TASK-001"},  # No wave field
            {"id": "TASK-002", "wave": 1},
        ]

        waves = ws.schedule(tasks)

        assert len(waves[0]) == 1  # TASK-001 default wave 0
        assert len(waves[1]) == 1  # TASK-002 wave 1

    def test_schedule_returns_empty_for_empty_list(self):
        """GREEN: Empty list returns empty"""
        ws = WaveScheduler()
        assert ws.schedule([]) == []

    def test_run_waves_executes_sequentially(self):
        """GREEN: Waves execute serially"""
        ws = WaveScheduler()
        executed = []

        def executor(task):
            executed.append(task["id"])
            return {"success": True, "task_id": task["id"]}

        waves = [[{"id": "TASK-001"}], [{"id": "TASK-002"}]]
        results = ws.run_waves(waves, executor)

        assert executed == ["TASK-001", "TASK-002"]  # Sequential
        assert len(results) == 2

    def test_run_waves_executes_within_wave_in_parallel(self):
        """GREEN: Tasks within wave execute in parallel"""
        import concurrent.futures
        ws = WaveScheduler()
        start_times = {}

        def executor(task):
            start_times[task["id"]] = time.time()
            time.sleep(0.1)
            return {"success": True, "task_id": task["id"]}

        waves = [[{"id": "TASK-001"}, {"id": "TASK-002"}]]  # Same wave
        ws.run_waves(waves, executor)

        # Verify parallel: both start times are close
        diff = abs(start_times["TASK-001"] - start_times["TASK-002"])
        assert diff < 0.05  # Almost simultaneous