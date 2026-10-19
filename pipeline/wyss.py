"""Prepare acquisition manifests from the original Wyss update lists.

    python pipeline/wyss.py --lists DIR --out data/acquisition
    python pipeline/wyss.py --selfcheck
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from typical import partition


def version_identity(path):
    match = re.fullmatch(r"[^/]+/(.+)/\1@([^/]+)", path)
    if not match:
        raise ValueError(f"unexpected upstream version path: {path}")
    return match.groups()


def read_updates(path, group):
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        before_path, after_path = line.strip().split(",")
        before_name, before = version_identity(before_path)
        name, after = version_identity(after_path)
        if name != before_name:
            raise ValueError(f"update changes package identity: {line}")
        rows.append({"id": f"{name}@{after}", "name": name, "before": before,
                     "after": after, "group": group, "line": line.strip(),
                     "upstream_before": before_path, "upstream_after": after_path,
                     "source": "https://osf.io/92w4e/"})
    return rows


def write_jsonl(path, rows):
    Path(path).write_text("".join(json.dumps(row) + "\n" for row in rows))


def prepare(lists, out):
    lists, out = Path(lists), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    popular = read_updates(lists / "typical_updates_popular.txt", "popular")
    random = read_updates(lists / "typical_updates_random.txt", "random")
    typ, pool = partition(popular, random)
    # Source labels are evidence for annotation, not completed local annotations.
    mal = [dict(row, source_label="malicious", annotation_status="pending")
           for row in read_updates(lists / "malicious_updates.txt", "malicious")]
    write_jsonl(out / "typ.draw.jsonl", typ)
    write_jsonl(out / "typ.pool.jsonl", pool)
    write_jsonl(out / "mal.source.jsonl", mal)
    wanted = {}
    for row in typ + pool:
        for side in ("before", "after"):
            key = row["name"], row[side]
            wanted.setdefault(key, {"name": key[0], "version": key[1],
                                    "origin": "registry"})
    write_jsonl(out / "wanted.typical.jsonl", wanted.values())
    summary = {"popular": len(popular), "random": len(random), "typ_draw": len(typ),
               "path_a_pool": len(pool), "unique_registry_versions": len(wanted),
               "mal_source_pairs": len(mal), "seed": 2026,
               "source_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in lists.glob("*.txt")}}
    (out / "wyss-plan.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def selfcheck():
    assert version_identity("a/foo/foo@1.2.3") == ("foo", "1.2.3")
    assert version_identity("a/@scope/foo/@scope/foo@1.2.3-beta.1") == (
        "@scope/foo", "1.2.3-beta.1")
    try:
        version_identity("a/foo/bar@1")
    except ValueError:
        pass
    else:
        raise AssertionError("mismatching path identities must be rejected")
    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        parser = argparse.ArgumentParser()
        parser.add_argument("--lists", required=True)
        parser.add_argument("--out", required=True)
        args = parser.parse_args()
        print(json.dumps(prepare(args.lists, args.out)))
