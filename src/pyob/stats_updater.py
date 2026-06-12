import json
import os
import time


class StatsUpdater:
    def __init__(self, pyob_dir: str):
        self.stats_path = os.path.join(pyob_dir, "SESSION_STATS.json")
        self._stats: dict = self._load()

    def _load(self) -> dict:
        defaults = {
            "session_pr_count": 0,
            "session_failures": 0,
            "consecutive_failures": 0,
            "last_success_time": None,
            "cascade_depth_max": 0,
        }
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        # Merge defaults with loaded data to safely handle missing keys
                        return {**defaults, **loaded}
            except Exception:
                pass
        return defaults

    def _save(self) -> None:

        dir_name = os.path.dirname(self.stats_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        temp_path = self.stats_path + ".tmp"
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, indent=2)
            os.replace(temp_path, self.stats_path)
        except Exception:
            with open(self.stats_path, "w", encoding="utf-8") as f:
                json.dump(self._stats, f, indent=2)
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass

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
