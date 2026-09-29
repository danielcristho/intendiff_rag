"""Smart-diff: the diff ordered by priority and cut to the token budget at hunk boundaries."""
import argparse
import json
from pathlib import Path

from pipeline.features.files import source_files
from pipeline.features.signals import scan_text
from pipeline.features.unified_diff import (normalize, raw_diff, relabel_paths, split_by_file,
                                            split_hunks, truncate_long_lines)
from pipeline.shared.isolation import require_offline
from pipeline.shared.tokens import approx_counter, qwen_counter

BUDGET_TOKENS = 28_000


def signals_per_file(after):
    return {path: len({signal for signal, _, _ in scan_text(text)})
            for path, text in source_files(after)}


# order_files puts package.json first, then files by signal count, then the rest by path.
def order_files(chunks, signals):
    def key(chunk):
        path = chunk["path"]
        if path.endswith("package.json"):
            return (0, 0, path)
        found = signals.get(path, 0)
        return (1, -found, path) if found else (2, 0, path)

    return sorted(chunks, key=key)


# fit_budget packs chunks into the budget; a chunk that does not fit keeps its leading hunks.
def fit_budget(chunks, count, budget=BUDGET_TOKENS):
    kept, used, omitted, dropped_tokens = [], 0, 0, 0
    for chunk in chunks:
        size = count(chunk["text"])
        if used + size <= budget:
            kept.append(chunk["text"])
            used += size
            continue
        header, hunks = split_hunks(chunk["text"])
        piece, piece_size, taken = header, count(header), 0
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
    if truncated:
        text += f"\n[smart-diff truncated: {omitted} files omitted, {dropped_tokens} tokens]\n"
    return text, truncated


# build returns one pair's smart-diff and whether it had to be truncated.
def build(before, after, count, budget=BUDGET_TOKENS):
    before, after = normalize(Path(before)), normalize(Path(after))
    diff_text = truncate_long_lines(relabel_paths(raw_diff(before, after), before, after))
    chunks = split_by_file(diff_text, after_root="b")
    text, truncated = fit_budget(order_files(chunks, signals_per_file(after)), count, budget)
    return {"diff": text, "truncated": truncated, "files": len(chunks)}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="smartdiff")
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--budget", type=int, default=BUDGET_TOKENS)
    parser.add_argument("--approx", action="store_true", help="count 4 characters per token")
    args = parser.parse_args(argv)
    require_offline()
    count = approx_counter if args.approx else qwen_counter()
    print(json.dumps(build(args.before, args.after, count, args.budget), ensure_ascii=False))
