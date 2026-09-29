"""Reading a package version's files as text."""
from pathlib import Path

SOURCE_SUFFIXES = {".js", ".ts", ".ejs", ".mjs", ".cjs"}


# read_text returns None for a file that is not UTF-8 text, which callers treat as binary.
def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


# text_files lists every UTF-8 readable file, relative to the root.
def text_files(root):
    root = Path(root)
    return {str(path.relative_to(root)) for path in sorted(root.rglob("*"))
            if path.is_file() and read_text(path) is not None}


# source_files yields (relative path, text) for JavaScript sources and package.json.
def source_files(root):
    root = Path(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or (path.suffix not in SOURCE_SUFFIXES and path.name != "package.json"):
            continue
        text = read_text(path)
        if text is not None:
            yield str(path.relative_to(root)), text


# package_root reads through the "package/" wrapper that some unpacked tarballs keep.
def package_root(version_dir):
    version_dir = Path(version_dir)
    inner = version_dir / "package"
    if not (version_dir / "package.json").exists() and (inner / "package.json").exists():
        return inner
    return version_dir


def has_content(version_dir):
    return any(path.is_file() for path in Path(version_dir).rglob("*"))
