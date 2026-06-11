import os

from .core_utils import IGNORE_DIRS, IGNORE_FILES, SUPPORTED_EXTENSIONS


class ScannerMixin:
    # Type hint so Mypy knows this mixin expects a target_dir attribute
    target_dir: str

    import os

from .core_utils import IGNORE_DIRS, IGNORE_FILES, SUPPORTED_EXTENSIONS


class ScannerMixin:
    # Type hint so Mypy knows this mixin expects a target_dir attribute
    target_dir: str

    def scan_directory(self) -> list[str]:
        file_list = []

        supported_ext_tuple = tuple(SUPPORTED_EXTENSIONS)
        excluded_ext_tuple = (".spec", ".dmg")
        
        for root, dirs, files in os.walk(self.target_dir):

            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for file in files:
                if file in IGNORE_FILES:
                    continue
                if file.endswith(excluded_ext_tuple):
                    continue
                if file.endswith(supported_ext_tuple):

                    full_path = os.path.normpath(os.path.join(root, file))
                    file_list.append(full_path)
        return file_list
