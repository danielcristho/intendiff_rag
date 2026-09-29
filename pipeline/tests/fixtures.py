"""Helpers shared by the test modules."""
import tempfile
from pathlib import Path


def build_fixture(root, files):
    root = Path(root)
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    return root


def temp_dir():
    return Path(tempfile.mkdtemp())


# words counts whitespace-separated words, a deterministic stand-in for the tokenizer.
def words(text):
    return len(text.split())


# Versions hands out fresh fixture directories, one per call.
class Versions:
    def __init__(self):
        self.root, self.count = temp_dir(), 0

    def __call__(self, files):
        self.count += 1
        return build_fixture(self.root / f"v{self.count}", files)
