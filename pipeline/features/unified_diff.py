"""Running diff between two version directories and splitting its output."""
import os
import re
import subprocess

MAX_LINE_CHARS = 2000
HUNK_HEADER = re.compile(r"^@@ ", re.MULTILINE)
BINARY_LINE = re.compile(r"^Binary files (.+) and (.+) differ$")
# TIMESTAMPED matches a quoted path too, which diff prints for names containing spaces.
TIMESTAMPED = re.compile(r'^(---|\+\+\+) ("(?:[^"\\]|\\.)*"|\S+)\t.*$', re.MULTILINE)
# EXCLUDED copies the upstream generator's shutil.ignore_patterns list.
EXCLUDED = ("*.wasm", "*.md", "*.map", ".npmignore", "LICENSE*", "license*",
            "*.tsbuildinfo", "package-lock.json", "yarn.lock")
ECHOED_EXCLUDES = re.compile(r"^(diff .*?)(?:-x (?:'[^']*'|\S+) )+", re.MULTILINE)


# normalize is the minify, un-minify and de-duplicate seam.
def normalize(version_dir):
    # TODO: pass-through; upstream runs uglifyjs -c -m then webcrack on names ending in "js",
    # and de-duplicates with an index.mjs that ships without source.
    return version_dir


# truncate_long_lines caps each line and says how many characters it dropped.
def truncate_long_lines(text, limit=MAX_LINE_CHARS):
    return "\n".join(f"{line[:limit]}…[+{len(line) - limit} chars]" if len(line) > limit else line
                     for line in text.split("\n"))


# raw_diff runs zero-context `diff -N -U 0 -r`, the flags the upstream token average was measured with.
def raw_diff(before, after):
    excludes = [arg for pattern in EXCLUDED for arg in ("-x", pattern)]
    # LC_ALL=C sorts files by byte, so the section order does not depend on the machine's locale.
    result = subprocess.run(["diff", "-N", "-U", "0", "-r", *excludes, str(before), str(after)],
                            env={**os.environ, "LC_ALL": "C"}, capture_output=True, text=True,
                            errors="replace")
    # diff exits 1 when files differ; 2 and above mean the tool failed.
    if result.returncode >= 2:
        raise RuntimeError(f"diff failed: {result.stderr.strip()}")
    # diff echoes each -x option in every file header, which costs budget and says nothing.
    return ECHOED_EXCLUDES.sub(r"\1", result.stdout)


# relabel_paths swaps the extraction directories for a/ and b/ and drops header timestamps.
def relabel_paths(diff_text, before, after):
    for root, label in ((str(after).rstrip("/"), "b"), (str(before).rstrip("/"), "a")):
        diff_text = diff_text.replace(root + "/", label + "/")
    return TIMESTAMPED.sub(r"\1 \2", diff_text)


# split_by_file breaks a unified diff into one chunk per file, binary files included.
def split_by_file(diff_text, after_root=None):
    root = (str(after_root).rstrip("/") + "/") if after_root else ""

    def relative(path):
        return path[len(root):] if root and path.startswith(root) else path

    chunks, current = [], None
    for line in diff_text.split("\n"):
        binary = BINARY_LINE.match(line)
        if binary:
            if current:
                chunks.append(current)
                current = None
            chunks.append({"path": relative(binary.group(2)), "text": line + "\n"})
        elif line.startswith("diff "):
            if current:
                chunks.append(current)
            parts = line.split()
            current = {"path": relative(parts[-1]) if len(parts) >= 2 else "", "text": line + "\n"}
        elif current is not None:
            current["text"] += line + "\n"
    if current:
        chunks.append(current)
    return chunks


# split_hunks returns a file chunk's header and its hunks.
def split_hunks(chunk_text):
    starts = [match.start() for match in HUNK_HEADER.finditer(chunk_text)]
    if not starts:
        return chunk_text, []
    ends = starts[1:] + [len(chunk_text)]
    return chunk_text[: starts[0]], [chunk_text[start:end] for start, end in zip(starts, ends)]
