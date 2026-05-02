from typing import List, Dict, Any, Callable
import concurrent.futures


class WaveScheduler:
    """Schedules and executes tasks in waves"""

    def schedule(self, tasks: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Group tasks by wave field"""
        if not tasks:
            return []

        wave_map = {}
        for task in tasks:
            wave = task.get("wave", 0)
            if wave not in wave_map:
                wave_map[wave] = []
            wave_map[wave].append(task)

        if not wave_map:
            return []

        max_wave = max(wave_map.keys())
        waves = []
        for w in range(max_wave + 1):
            waves.append(wave_map.get(w, []))

        return waves

    def run_waves(
        self,
        waves: List[List[Dict[str, Any]]],
        executor: Callable[[Dict[str, Any]], Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Execute waves sequentially, tasks within wave in parallel"""
        results = []

        for wave in waves:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(wave)) as pool:
                futures = [pool.submit(executor, task) for task in wave]
                wave_results = [f.result() for f in concurrent.futures.as_completed(futures)]
                results.extend(wave_results)

        return results