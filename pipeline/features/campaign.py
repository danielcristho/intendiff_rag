"""Campaign clustering: shared report, identical added file, or similar added code."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

from pipeline.features.files import SOURCE_SUFFIXES, read_text
from pipeline.shared.hashing import sha256_text
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl

MERGE_THRESHOLD = 0.5
REPORTED_THRESHOLDS = (0.5, 0.8)
DOLOS_KGRAM = 70
DOLOS_WINDOW = 17


# added_files maps each text file new in `after` to its content.
def added_files(before, after):
    before, after = Path(before), Path(after)
    existing = {str(path.relative_to(before)) for path in before.rglob("*") if path.is_file()}
    added = {}
    for path in sorted(after.rglob("*")):
        relative = str(path.relative_to(after))
        if path.is_file() and relative not in existing:
            text = read_text(path)
            if text is not None:
                added[relative] = text
    return added


# added_hashes compares raw file digests, not paths.
def added_hashes(before, after):
    return {sha256_text(text) for text in added_files(before, after).values()}


# added_code concatenates the added JavaScript, which is what Dolos compares.
def added_code(before, after):
    return "\n".join(text for name, text in sorted(added_files(before, after).items())
                     if Path(name).suffix in SOURCE_SUFFIXES)


# dolos_similarity scores two code excerpts with the upstream Dolos parameters.
def dolos_similarity(left, right):
    if not left.strip() or not right.strip():
        return 0.0
    # TODO: Dolos is not in the analysis image yet, and npx needs the network the container lacks.
    with tempfile.TemporaryDirectory() as work:
        root = Path(work)
        (root / "a.js").write_text(left, encoding="utf-8")
        (root / "b.js").write_text(right, encoding="utf-8")
        result = subprocess.run(
            ["npx", "--yes", "@dodona/dolos", "run", "-f", "terminal",
             "--kgram-length", str(DOLOS_KGRAM), "--kgrams-in-window", str(DOLOS_WINDOW),
             str(root / "a.js"), str(root / "b.js")],
            capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"dolos failed: {result.stderr.strip()[:300]}")
        return parse_similarity(result.stdout)


# parse_similarity takes the first 0-1 float on the report line naming both files.
def parse_similarity(output):
    for line in output.splitlines():
        if "a.js" in line and "b.js" in line:
            for token in line.replace("|", " ").split():
                try:
                    value = float(token)
                except ValueError:
                    continue
                if 0.0 <= value <= 1.0:
                    return value
    return 0.0


def find(parent, item):
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


# union keeps the smaller id as the root, so the label does not depend on reading order.
def union(parent, left, right):
    left_root, right_root = find(parent, left), find(parent, right)
    if left_root != right_root:
        low, high = sorted((left_root, right_root))
        parent[high] = low


def linked_without_code(left, right):
    if set(left.get("reports") or ()) & set(right.get("reports") or ()):
        return True
    return bool(set(left.get("added_hashes") or ()) & set(right.get("added_hashes") or ()))


# cluster assigns every item a campaign id, as the transitive closure of the three links.
def cluster(items, similarity=None, threshold=MERGE_THRESHOLD):
    parent = {item["id"]: item["id"] for item in items}
    for index, left in enumerate(items):
        for right in items[index + 1:]:
            if find(parent, left["id"]) == find(parent, right["id"]):
                continue
            if linked_without_code(left, right) or (
                    similarity is not None
                    and similarity(left.get("code", ""), right.get("code", "")) >= threshold):
                union(parent, left["id"], right["id"])
    return {item["id"]: find(parent, item["id"]) for item in items}


def count_clusters(items, similarity=None, thresholds=REPORTED_THRESHOLDS):
    return {threshold: len(set(cluster(items, similarity, threshold).values()))
            for threshold in thresholds}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="campaign")
    parser.add_argument("--items", required=True, help="JSONL with id, reports, added_hashes and code")
    parser.add_argument("--threshold", type=float, default=MERGE_THRESHOLD)
    parser.add_argument("--no-dolos", action="store_true", help="use the report and file-hash links only")
    args = parser.parse_args(argv)
    require_offline()
    items = read_jsonl(args.items)
    similarity = None if args.no_dolos else dolos_similarity
    print(json.dumps({"campaigns": cluster(items, similarity, args.threshold),
                      "clusters": count_clusters(items, similarity)}, ensure_ascii=False, indent=2))
