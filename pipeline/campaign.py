"""Campaign clustering.

    python pipeline/campaign.py --items items.jsonl [--no-dolos]
    python pipeline/campaign.py --selfcheck
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from capability import SOURCE_SUFFIXES, read_text  # noqa: E402

MERGE_THRESHOLD = 0.5
REPORTED_THRESHOLDS = (0.5, 0.8)
DOLOS_KGRAM = 70
DOLOS_WINDOW = 17


# sha256_text returns the hex digest of a file's raw contents.
def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def added_files(before, after):
    before, after = Path(before), Path(after)
    existing = {
        str(path.relative_to(before)) for path in before.rglob("*") if path.is_file()
    }
    added = {}
    for path in sorted(after.rglob("*")):
        if not path.is_file():
            continue
        relative = str(path.relative_to(after))
        if relative in existing:
            continue
        text = read_text(path)
        if text is not None:
            added[relative] = text
    return added


# Compares raw file digests, not paths.
def added_hashes(before, after):
    before, after = Path(before), Path(after)
    existing = {p.relative_to(before).as_posix() for p in before.rglob("*") if p.is_file()}
    hashes = set()
    for path in after.rglob("*"):
        if path.is_file() and path.relative_to(after).as_posix() not in existing:
            # read_text normalizes CRLF and omits binary files, violating raw-byte hashes.
            with path.open("rb") as stream:
                hashes.add(hashlib.file_digest(stream, "sha256").hexdigest())
    return hashes


# added_code concatenates the added JavaScript, which is what Dolos compares.
def added_code(before, after):
    sources = added_files(before, after)
    return "\n".join(
        text for name, text in sorted(sources.items())
        if Path(name).suffix in SOURCE_SUFFIXES
    )


# dolos_similarity scores two code excerpts with Wyss's Dolos parameters.
def dolos_similarity(left, right):
    if not left.strip() or not right.strip():
        return 0.0
    from dolos import score_lookup
    return score_lookup([{"code": left}, {"code": right}])(left, right)


# Union-find with path compression.
def find(parent, item):
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item


def union(parent, left, right):
    left_root, right_root = find(parent, left), find(parent, right)
    if left_root != right_root:
        # Keep the lexicographically smaller id as the root, so the campaign
        # label does not depend on the order items were read in.
        low, high = sorted((left_root, right_root))
        parent[high] = low


# linked_without_code reports whether two items already share a report or a file.
def linked_without_code(left, right):
    if set(left.get("reports") or ()) & set(right.get("reports") or ()):
        return True
    return bool(set(left.get("added_hashes") or ()) & set(right.get("added_hashes") or ()))


# cluster assigns every item a campaign id, as the transitive closure of §3.6.
def cluster(items, similarity=None, threshold=MERGE_THRESHOLD):
    parent = {item["id"]: item["id"] for item in items}
    # Index exact links before similarity; rebuilding large hash sets for every
    # pair is prohibitive on the full KB pool and does not change the closure.
    owners = {}
    for item in items:
        for field in ("reports", "added_hashes"):
            for value in item.get(field) or ():
                owner = owners.setdefault((field, value), item["id"])
                union(parent, owner, item["id"])

    if similarity is not None:
        for index, left in enumerate(items):
            for right in items[index + 1:]:
                if find(parent, left["id"]) == find(parent, right["id"]):
                    continue
                if similarity(left.get("code", ""), right.get("code", "")) >= threshold:
                    union(parent, left["id"], right["id"])

    return {item["id"]: find(parent, item["id"]) for item in items}


def count_clusters(items, similarity=None, thresholds=REPORTED_THRESHOLDS):
    return {
        threshold: len(set(cluster(items, similarity, threshold).values()))
        for threshold in thresholds
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", required=True,
                        help="JSONL with id, reports, added_hashes and code per item")
    parser.add_argument("--threshold", type=float, default=MERGE_THRESHOLD)
    parser.add_argument("--no-dolos", action="store_true",
                        help="use only the report and file-hash criteria")
    args = parser.parse_args(argv)

    items = [json.loads(line) for line in Path(args.items).read_text().splitlines() if line.strip()]
    from dolos import score_lookup
    similarity = None if args.no_dolos else score_lookup(items)
    assigned = cluster(items, similarity, args.threshold)
    print(json.dumps({
        "campaigns": assigned,
        "clusters": count_clusters(items, similarity),
    }, ensure_ascii=False, indent=2))


def selfcheck():
    item = lambda i, reports=(), hashes=(), code="": {  # noqa: E731
        "id": i, "reports": list(reports), "added_hashes": list(hashes), "code": code
    }
    campaigns = lambda assigned: {  # noqa: E731
        frozenset(k for k, v in assigned.items() if v == root) for root in set(assigned.values())
    }

    # --- (a) the same advisory merges two items
    same_report = [item("p1", reports=["MAL-2024-1"]), item("p2", reports=["MAL-2024-1"]),
                   item("p3", reports=["MAL-2024-9"])]
    assert campaigns(cluster(same_report)) == {frozenset({"p1", "p2"}), frozenset({"p3"})}

    # --- (b) one identical added file is enough, even among many
    shared = sha256_text("payload")
    same_file = [item("p1", hashes=[shared, "x"]), item("p2", hashes=["y", shared]),
                 item("p3", hashes=["z"])]
    assert campaigns(cluster(same_file)) == {frozenset({"p1", "p2"}), frozenset({"p3"})}

    # --- (c) similarity at or above the threshold merges; below it does not
    scores = {("A", "B"): 0.62, ("A", "C"): 0.10, ("B", "C"): 0.10}
    look_up = lambda a, b: scores.get((a, b)) or scores.get((b, a)) or 0.0  # noqa: E731
    by_code = [item("p1", code="A"), item("p2", code="B"), item("p3", code="C")]
    assert campaigns(cluster(by_code, look_up)) == {frozenset({"p1", "p2"}), frozenset({"p3"})}
    # Exactly 0.5 merges: §3.6 says "at least 0.5".
    assert campaigns(cluster([item("a", code="A"), item("b", code="B")],
                            lambda *_: 0.5)) == {frozenset({"a", "b"})}
    assert campaigns(cluster([item("a", code="A"), item("b", code="B")],
                            lambda *_: 0.49)) == {frozenset({"a"}), frozenset({"b"})}

    # --- transitive closure: a-b by report, b-c by code, so all three are one
    chain = [item("p1", reports=["R"]), item("p2", reports=["R"], code="B"), item("p3", code="C")]
    linked = lambda a, b: 0.9 if {a, b} == {"B", "C"} else 0.0  # noqa: E731
    assert campaigns(cluster(chain, linked)) == {frozenset({"p1", "p2", "p3"})}

    # --- the campaign label is the smallest id, so it does not depend on order
    forward = cluster([item("zz", reports=["R"]), item("aa", reports=["R"])])
    backward = cluster([item("aa", reports=["R"]), item("zz", reports=["R"])])
    assert forward == backward == {"zz": "aa", "aa": "aa"}, (forward, backward)

    # --- items with nothing in common stay apart
    alone = [item("p1"), item("p2"), item("p3")]
    assert len(set(cluster(alone).values())) == 3

    # --- both thresholds are reported, and a higher one never merges more (§3.6)
    spread = [item("p1", code="A"), item("p2", code="B"), item("p3", code="C")]
    graded = {("A", "B"): 0.6, ("A", "C"): 0.9, ("B", "C"): 0.2}
    grade = lambda a, b: graded.get((a, b)) or graded.get((b, a)) or 0.0  # noqa: E731
    counts = count_clusters(spread, grade)
    assert counts == {0.5: 1, 0.8: 2}, counts
    assert counts[0.8] >= counts[0.5], "a stricter threshold cannot produce fewer clusters"

    # Indexed linking must match the exhaustive edge graph, including transitive
    # bridges and values appearing in both metadata namespaces.
    import random
    rng = random.Random(2026)
    for _ in range(20):
        rows = [item(str(i), reports=[str(rng.randrange(20))],
                     hashes=[str(rng.randrange(20))], code=str(i)) for i in range(25)]
        edges = {(str(i), str(j)): rng.random() for i in range(25) for j in range(i + 1, 25)}
        sim = lambda a, b: edges.get((a, b), edges.get((b, a), 0.0))
        for threshold in (0.5, 0.8):
            expected = {r["id"]: r["id"] for r in rows}
            for i, left in enumerate(rows):
                for right in rows[i + 1:]:
                    if linked_without_code(left, right) or sim(left["code"], right["code"]) >= threshold:
                        union(expected, left["id"], right["id"])
            expected = {key: find(expected, key) for key in expected}
            assert cluster(rows, sim, threshold) == expected
            assert cluster(list(reversed(rows)), sim, threshold) == expected

    # --- added_files and added_code read real directories
    import tempfile as tf

    tmp = Path(tf.mkdtemp())
    before, after = tmp / "v1", tmp / "v2"
    (before / "src").mkdir(parents=True)
    (after / "src").mkdir(parents=True)
    (before / "src" / "index.js").write_text("shared();")
    (after / "src" / "index.js").write_text("shared();")
    (after / "src" / "payload.js").write_text("exfiltrate();")
    (after / "notes.txt").write_text("not javascript")

    added = added_files(before, after)
    assert set(added) == {"src/payload.js", "notes.txt"}, set(added)
    assert "shared()" not in added_code(before, after), "an unchanged file is not an addition"
    assert "exfiltrate()" in added_code(before, after)
    # Dolos compares JavaScript; a text file is not part of the code excerpt.
    assert "not javascript" not in added_code(before, after)
    assert sha256_text("exfiltrate();") in added_hashes(before, after)
    (after / "crlf.txt").write_bytes(b"first\r\nsecond\r\n")
    (after / "binary.bin").write_bytes(b"\x00\xff")
    hashes = added_hashes(before, after)
    assert hashlib.sha256(b"first\r\nsecond\r\n").hexdigest() in hashes
    assert hashlib.sha256(b"\x00\xff").hexdigest() in hashes
    assert hashlib.sha256(b"first\nsecond\n").hexdigest() not in hashes

    # --- an empty excerpt scores zero rather than invoking Dolos
    assert dolos_similarity("", "anything") == 0.0
    assert dolos_similarity("   ", "") == 0.0

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
