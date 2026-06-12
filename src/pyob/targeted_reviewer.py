import os

from .autoreviewer import AutoReviewer
from .core_utils import logger


class TargetedReviewer(AutoReviewer):
    """
    Specialized reviewer that targets a single specific file.
    Automatically handles both absolute and relative path inputs for cross-platform stability.
    """

    def __init__(self, target_dir: str, target_file: str) -> None:
        # Normalize the directory path
        normalized_dir: str = os.path.normpath(target_dir)
        super().__init__(normalized_dir)

        # Normalize the target file path to avoid cross-platform slash issues
        normalized_file: str = os.path.normpath(target_file)
        self.forced_target_file: str

        if os.path.isabs(normalized_file):
            self.forced_target_file = os.path.relpath(normalized_file, self.target_dir)
        else:
            self.forced_target_file = normalized_file

    def scan_directory(self) -> list[str]:
        """Returns only the specific targeted file for the pipeline to process."""
        full_target_path = os.path.normpath(
            os.path.join(self.target_dir, self.forced_target_file)
        )
        if os.path.exists(full_target_path):
            return [full_target_path]

        # Log a warning to prevent silent target-miss failures
        logger.warning(f"Targeted file not found on disk: {full_target_path}")
        return []
