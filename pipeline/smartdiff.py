"""Smart-diff builder.

    python pipeline/smartdiff.py --before DIR --after DIR [--approx]
    python pipeline/smartdiff.py --selfcheck
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from capability import scan_text, source_files  # noqa: E402
from normalization import EXCLUDED, prepared_pair  # noqa: E402

MAX_LINE_CHARS = 2000
BUDGET_TOKENS = 28_000
HUNK_HEADER = re.compile(r"^@@ ", re.MULTILINE)
BINARY_LINE = re.compile(r"^Binary files (.+) and (.+) differ$")
TIMESTAMPED = re.compile(r"^(---|\+\+\+) (\S+)\t.*$", re.MULTILINE)

ECHOED_EXCLUDES = re.compile(r"^(diff .*?)(?:-x (?:'[^']*'|\S+) )+", re.MULTILINE)


# truncate_long_lines caps any line at 2,000 characters (§4.2 step 6).
def truncate_long_lines(text, limit=MAX_LINE_CHARS):
    # One very long line is an encoded payload: past its opening it adds no
    # information, and the obfuscation signal is already caught from raw files.
    out = []
    for line in text.split("\n"):
        if len(line) > limit:
            out.append(f"{line[:limit]}…[+{len(line) - limit} chars]")
        else:
            out.append(line)
    return "\n".join(out)


# raw_diff compares two version directories with `diff -N -U 0 -r` (§4.2 steps 3-5).
def raw_diff(before, after):
    # Flags and exclusions come from the upstream generator, not from taste: it
    # runs zero context, and the 25,246-token average the §4.5 budget rests on
    # was measured with that. Three lines of context would silently inflate it.
    excludes = [arg for pattern in EXCLUDED for arg in ("-x", pattern)]
    result = subprocess.run(
        ["diff", "-N", "-U", "0", "-r", *excludes, str(before), str(after)],
        capture_output=True,
        text=True,
        errors="replace",
    )
    # diff exits 1 when files differ, which is the normal case here; only 2 and
    # above mean the tool itself failed.
    if result.returncode >= 2:
        raise RuntimeError(f"diff failed: {result.stderr.strip()}")
    # diff echoes its own options on every file header. Upstream excludes by
    # copying the tree instead, so its headers stay short; left in, nine -x
    # patterns cost ~120 characters per file out of the §4.5 budget.
    return ECHOED_EXCLUDES.sub(r"\1", result.stdout)


# relabel_paths rewrites the extraction directories to fixed a/ and b/ prefixes.
def relabel_paths(diff_text, before, after):
    # diff prints the paths it was given, which carry the package name, and
    # tie the output to wherever the tarballs happened to be unpacked.
    for root, label in ((str(after).rstrip("/"), "b"), (str(before).rstrip("/"), "a")):
        diff_text = diff_text.replace(root + "/", label + "/")
    # Drop the mtimes on ---/+++ too, or the same pair yields different text
    # on every extraction. git shows no timestamps either.
    return TIMESTAMPED.sub(r"\1 \2", diff_text)


# split_by_file breaks a unified diff into one chunk per file.
def split_by_file(diff_text, after_root=None):
    # Line by line, not by a fixed header: a binary file gets no header, and
    # diff echoes back whatever options it was given.
    root = (str(after_root).rstrip("/") + "/") if after_root else ""

    def relative(path):
        return path[len(root):] if root and path.startswith(root) else path

    def finish(chunk):
        return {"path": chunk["path"], "text": "".join(chunk["lines"])}

    chunks, current = [], None
    for line in diff_text.split("\n"):
        binary = BINARY_LINE.match(line)
        if binary:
            if current:
                chunks.append(finish(current))
                current = None
            chunks.append({"path": relative(binary.group(2)), "text": line + "\n"})
        elif line.startswith("diff "):
            if current:
                chunks.append(finish(current))
            parts = line.split()
            current = {"path": relative(parts[-1]) if len(parts) >= 2 else "", "lines": [line + "\n"]}
        elif current is not None:
            # Repeated dictionary-string concatenation is quadratic on large bundles.
            current["lines"].append(line + "\n")
    if current:
        chunks.append(finish(current))
    return chunks


def split_hunks(chunk_text):
    starts = [match.start() for match in HUNK_HEADER.finditer(chunk_text)]
    if not starts:
        return chunk_text, []
    header = chunk_text[: starts[0]]
    hunks = [
        chunk_text[start : (starts[i + 1] if i + 1 < len(starts) else len(chunk_text))]
        for i, start in enumerate(starts)
    ]
    return header, hunks


def signals_per_file(after):
    counts = {}
    for path, text in source_files(after):
        counts[path] = len({signal for signal, _, _ in scan_text(text)})
    return counts


# order_files sorts file chunks by the §4.5 truncation priority.
def order_files(chunks, signals):
    def key(chunk):
        path = chunk["path"]
        if path.endswith("package.json"):
            return (0, 0, path)  # (a) the manifest always survives (D15)
        found = signals.get(path, 0)
        if found:
            return (1, -found, path)  # (b) most signals first
        return (2, 0, path)  # (c) everything else, by path

    return sorted(chunks, key=key)


# fit_budget packs file chunks into the token budget, cutting at hunk boundaries.
def fit_budget(chunks, count, budget=BUDGET_TOKENS):
    kept, used, omitted, dropped_tokens = [], 0, 0, 0

    for chunk in chunks:
        size = count(chunk["text"])
        if used + size <= budget:
            kept.append(chunk["text"])
            used += size
            continue

        # Does not fit whole: keep as many hunks as the remaining budget allows,
        # so a partial file is still readable rather than cut mid-line.
        header, hunks = split_hunks(chunk["text"])
        piece, piece_size = header, count(header)
        taken = 0
        for hunk in hunks:
            hunk_size = count(hunk)
            if used + piece_size + hunk_size > budget:
                break
            piece += hunk
            piece_size += hunk_size
            taken += 1

        if taken:
            kept.append(piece)
            used += piece_size
            dropped_tokens += size - piece_size
        else:
            omitted += 1
            dropped_tokens += size

    text = "".join(kept)
    truncated = omitted > 0 or dropped_tokens > 0
    # Include the marker and tokenization across chunk boundaries in the cap.
    # Summing separately encoded hunks does not bound the concatenated text.
    while True:
        text = "".join(kept)
        marker = (f"\n[smart-diff truncated: {omitted} files omitted, {dropped_tokens} tokens]\n"
                  if truncated else "")
        if count(text + marker) <= budget:
            return text + marker, truncated
        if not kept:
            return "", True
        previous = kept.pop()
        header, hunks = split_hunks(previous)
        replacement = header + "".join(hunks[:-1]) if len(hunks) > 1 else ""
        if replacement:
            kept.append(replacement)
        else:
            omitted += 1
        dropped_tokens += count(previous) - count(replacement)
        truncated = True


# build produces one pair's smart-diff and whether it had to be truncated.
def build_prepared(before, after, count, budget=BUDGET_TOKENS, signals=None):
    diff_text = relabel_paths(raw_diff(before, after), before, after)
    diff_text = truncate_long_lines(diff_text)
    chunks = split_by_file(diff_text, after_root="b")
    ordered = order_files(chunks, signals if signals is not None else signals_per_file(after))
    text, truncated = fit_budget(ordered, count, budget)
    return {"diff": text, "truncated": truncated, "files": len(chunks)}


def build(before, after, count, budget=BUDGET_TOKENS):
    signals = signals_per_file(Path(after))
    with prepared_pair(before, after) as (left, right, report):
        result = build_prepared(left, right, count, budget, signals)
        result["preprocessing"] = report
        return result


# §4.5 budgets in Qwen2.5-Coder-3B tokens.
def qwen_counter(model="Qwen/Qwen2.5-Coder-3B-Instruct"):
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:  # pragma: no cover - depends on the host
        raise RuntimeError(
            "§4.5 budgets in Qwen2.5-Coder-3B tokens; install transformers, "
            "or pass a counter explicitly for tests"
        ) from exc
    tokenizer = AutoTokenizer.from_pretrained(model)
    return lambda text: len(tokenizer(text)["input_ids"])


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--budget", type=int, default=BUDGET_TOKENS)
    parser.add_argument("--approx", action="store_true",
                        help="count 4 characters per token instead of loading the tokenizer")
    args = parser.parse_args(argv)

    count = (lambda text: len(text) // 4) if args.approx else qwen_counter()
    print(json.dumps(build(args.before, args.after, count, args.budget), ensure_ascii=False))


def selfcheck():
    import tempfile

    words = lambda text: len(text.split())  # noqa: E731 - deterministic stand-in
    tmp = Path(tempfile.mkdtemp())

    # --- §4.2 step 6: a long line is capped and says how much was dropped
    capped = truncate_long_lines("x" * 2500, limit=2000)
    assert capped.startswith("x" * 2000) and capped.endswith("…[+500 chars]"), capped
    assert truncate_long_lines("short") == "short", "a short line is untouched"
    assert truncate_long_lines("a\nb") == "a\nb", "line structure is preserved"

    # --- §4.2 steps 3-5 over real directories
    before, after = tmp / "v1", tmp / "v2"
    for root in (before, after):
        (root / "src").mkdir(parents=True)
    (before / "package.json").write_text('{"name":"p","version":"1"}')
    (after / "package.json").write_text('{"name":"p","version":"2"}')
    (before / "src" / "index.js").write_text("module.exports = 1;\n")
    (after / "src" / "index.js").write_text("module.exports = 2;\n")
    # -N must render a newly added file in full, since that is where payloads land.
    (after / "src" / "setup.js").write_text("require('https');\nprocess.env;\n")
    (after / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\xff")
    (before / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x01")
    for root, marker in ((before, "old prose"), (after, "new prose")):
        (root / "README.md").write_text(marker + "\n")
        (root / "LICENSE").write_text(marker + "\n")
        (root / "yarn.lock").write_text(marker + "\n")

    diff_text = relabel_paths(raw_diff(before, after), before, after)
    assert "setup.js" in diff_text and "require('https')" in diff_text

    # The README must not reach the diff, or E*-noint still sees the intent it
    # is supposed to ablate and RQ3 measures nothing.
    assert "README" not in diff_text and "new prose" not in diff_text, diff_text
    assert "LICENSE" not in diff_text and "yarn.lock" not in diff_text, diff_text

    # Zero context: a changed line brings no neighbours with it.
    assert "module.exports = 2;" in diff_text
    assert "-module.exports = 1;" in diff_text
    assert "Binary files" in diff_text, "a binary file keeps diff's own line (§4.2 step 5)"

    # D26: the extraction path carries the package name in real use, so no part
    # of it may survive into the text the model reads.
    assert str(tmp) not in diff_text, "extraction path leaked into the diff"
    # The unified format needs the space after --- / +++; dropping it with the
    # timestamp would leave a header no diff parser accepts.
    assert "--- a/package.json" in diff_text, diff_text[:200]
    assert "+++ b/package.json" in diff_text, diff_text[:200]

    # The same pair must produce the same text wherever it was unpacked, or the
    # §4.5 invariant and campaign clustering by hash both fail.
    import shutil

    elsewhere = tmp / "moved"
    shutil.copytree(before, elsewhere / "A")
    shutil.copytree(after, elsewhere / "B")
    assert relabel_paths(raw_diff(elsewhere / "A", elsewhere / "B"),
                         elsewhere / "A", elsewhere / "B") == diff_text, "diff is not reproducible"

    chunks = split_by_file(diff_text, after_root="b")
    paths = {chunk["path"] for chunk in chunks}
    assert {"package.json", "src/index.js", "src/setup.js", "logo.png"} <= paths, paths

    # --- §4.5 priority: manifest first, then signal-bearing files, then the rest
    signals = signals_per_file(after)
    assert signals.get("src/setup.js", 0) >= 2, signals  # network + host_info
    ordered = [chunk["path"] for chunk in order_files(chunks, signals)]
    assert ordered[0] == "package.json", ordered
    assert ordered.index("src/setup.js") < ordered.index("logo.png"), ordered

    # --- §4.5 budget: everything fits, nothing is marked truncated
    text, truncated = fit_budget(order_files(chunks, signals), words, budget=10_000)
    assert not truncated and "truncated" not in text

    # A budget of zero keeps nothing and reports every file as omitted.
    text, truncated = fit_budget(order_files(chunks, signals), words, budget=0)
    assert truncated and text == "", text

    # --- a file too large for the remaining budget is cut at a hunk boundary
    many = "diff -N -U 0 -r a/big.js b/big.js\n--- a/big.js\n+++ b/big.js\n" + "".join(
        f"@@ -{i},1 +{i},1 @@\n-old line {i}\n+new line {i}\n" for i in range(20)
    )
    header, hunks = split_hunks(many)
    assert len(hunks) == 20 and header.startswith("diff -N -U 0 -r")
    partial, truncated = fit_budget([{"path": "big.js", "text": many}], words,
                                    budget=words(header) + words(hunks[0]) * 3)
    assert truncated, "a partial file still counts as truncated"
    assert 0 < partial.count("@@ ") < 3, partial.count("@@ ")
    assert words(partial) <= words(header) + words(hunks[0]) * 3
    # The cut lands between hunks, never inside one.
    last = partial.count("@@ ") - 1
    assert f"+new line {last}\n" in partial and f"+new line {last + 1}\n" not in partial

    # --- build ties it together and reports the flag pairs.jsonl carries
    result = build_prepared(before, after, words, budget=10_000)
    assert result["truncated"] is False and result["files"] == len(chunks)
    assert result["diff"].index("package.json") < result["diff"].index("setup.js")

    tight = build_prepared(before, after, words, budget=1)
    assert tight["truncated"] is True

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
