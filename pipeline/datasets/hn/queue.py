"""Build the hard-negative verification queue from both paths, offline."""
import argparse

from pipeline.datasets.pairs import build_row
from pipeline.features.files import package_root
from pipeline.shared.config import layout
from pipeline.shared.hashing import hash_order
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl
from pipeline.shared.tokens import qwen_counter

CANDIDATE_FIELDS = ("publisher", "categories", "search_category")


# queue_order puts path A before path B, each in hash order, and queues a pair once.
def queue_order(path_a, path_b):
    order, seen = [], set()
    for source, rows in (("path-a", path_a), ("path-b", path_b)):
        for row in hash_order(rows, key=lambda item: (item["name"], item["after"])):
            key = f"{row['name']}@{row['after']}"
            if key not in seen:
                seen.add(key)
                order.append((source, row))
    return order


def main(argv=None):
    argparse.ArgumentParser(prog="hn-queue").parse_args(argv)
    require_offline()
    data = layout()
    roots = {"path-a": data.hn, "path-b": data.path_b}
    path_a = read_jsonl(data.hn / "candidates.jsonl")
    path_b = [row for path in sorted(data.path_b.glob("candidates.cat*.jsonl")) for row in read_jsonl(path)]
    count, rows = qwen_counter(), []
    for position, (source, candidate) in enumerate(queue_order(path_a, path_b), 1):
        before, after = (package_root(roots[source] / candidate[side]) for side in ("before_path", "after_path"))
        row = build_row(candidate["name"], candidate["before"], candidate["after"],
                        before, after, "HN", source, count)
        row.update({field: candidate[field] for field in CANDIDATE_FIELDS if field in candidate})
        rows.append({**row, "queue_position": position})
    write_jsonl(data.hn_queue, rows)
    print(f"{data.hn_queue}: {len(rows)} candidates ({len(path_a)} path A, {len(path_b)} path B before dedup)")
