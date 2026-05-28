import os

from pyob.core_utils import CoreUtilsMixin


class DummyAgent(CoreUtilsMixin):
    def __init__(self, target_dir):
        self.target_dir = target_dir


def test_find_entry_file_priority(tmp_path):
    agent = DummyAgent(str(tmp_path))
    entrance_file = tmp_path / "entrance.py"
    entrance_file.write_text('if __name__ == "__main__": pass')
    other_file = tmp_path / "other.py"
    other_file.write_text("x = 10")

    detected = agent._find_entry_file()

    assert detected is not None
    assert os.path.basename(detected) == "entrance.py"
