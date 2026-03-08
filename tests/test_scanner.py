from pyob.core_utils import CoreUtilsMixin


class DummyAgent(CoreUtilsMixin):
    def __init__(self, target_dir):
        self.target_dir = target_dir


def test_directory_scanner_ignores_hidden_folders(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    valid_file = src_dir / "logic.py"
    valid_file.write_text("print('hello')")

    ignored_file = git_dir / "config"
    ignored_file.write_text("ignore me")

    from pyob.autoreviewer import AutoReviewer

    reviewer = AutoReviewer(str(tmp_path))
    files = reviewer.scan_directory()

    assert any("logic.py" in f for f in files)
    assert not any(".git" in f for f in files)
