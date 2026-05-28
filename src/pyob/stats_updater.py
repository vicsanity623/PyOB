import json
import os
import time


class StatsUpdater:
    def __init__(self, pyob_dir: str):
        self.stats_path = os.path.join(pyob_dir, "SESSION_STATS.json")
        self._stats: dict = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "session_pr_count": 0,
            "session_failures": 0,
            "consecutive_failures": 0,
            "last_success_time": None,
            "cascade_depth_max": 0,
        }

    def _save(self) -> None:
        with open(self.stats_path, "w") as f:
            json.dump(self._stats, f, indent=2)

    def record_success(self, cascade_depth: int = 0) -> None:
        self._stats["session_pr_count"] += 1
        self._stats["consecutive_failures"] = 0
        self._stats["last_success_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._stats["cascade_depth_max"] = max(
            self._stats["cascade_depth_max"], cascade_depth
        )
        self._save()

    def record_failure(self) -> None:
        self._stats["session_failures"] += 1
        self._stats["consecutive_failures"] += 1
        self._save()

    def is_in_failure_spiral(self) -> bool:
        return self._stats["consecutive_failures"] >= 3

    def get_summary(self) -> str:
        s = self._stats
        return (
            f"PRs: {s['session_pr_count']} | "
            f"Failures: {s['session_failures']} | "
            f"Consecutive: {s['consecutive_failures']} | "
            f"Max Cascade Depth: {s['cascade_depth_max']}"
        )