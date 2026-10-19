"""Verify acquired corpus joins and selection invariants without model calls.

    python pipeline/verify_corpus.py --root data/acquisition
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from samples import load_jsonl


def verify(root):
    root = Path(root)
    typ = load_jsonl(root / "typ.selected.jsonl")
    hn = load_jsonl(root / "hn.audit.jsonl")
    mal = load_jsonl(root / "mal.audit.jsonl")
    assert len(typ) == 100
    assert Counter(row["group"] for row in typ) == {"popular": 50, "random": 50}
    assert len({r["id"] for r in typ}) == len(typ)
    assert not {r["id"] for r in typ} & {r["id"] for r in hn}
    advisories = {(r["name"], r["version"]): r for r in load_jsonl(root / "advisories.jsonl")}
    extracted = {(r["name"], r["version"]): r for r in load_jsonl(root / "extracted.typical.jsonl")}
    for row in typ:
        for side in ("before", "after"):
            key = row["name"], row[side]
            assert key in advisories and not advisories[key]["has_advisory"]
            assert key in extracted and not extracted[key].get("error")
    for row in hn + mal:
        assert row["annotation_status"] == "pending" and "label" not in row
        assert Path(row["audit_diff"]).is_file()
        assert len(row["sha256_before_tree"]) == len(row["sha256_after_tree"]) == 64
    for row in hn:
        assert row["delta"]
        assert "category" not in row, "screening signals must not become human categories"
    downloaded = load_jsonl(root / "datadog.all-downloaded.jsonl")
    inventory = load_jsonl(root / "datadog.inventory.jsonl")
    assert len({r["id"] for r in downloaded}) == 2438
    latest = {r["id"]: r for r in inventory}
    assert set(latest) == {r["id"] for r in downloaded}
    for row in latest.values():
        assert row.get("error") or (row["annotation_status"] == "pending" and "dir" in row)
    candidates = load_jsonl(root / "datadog.pair-candidates.jsonl")
    screened = load_jsonl(root / "datadog.pairs-screened.jsonl")
    excluded = load_jsonl(root / "datadog.pairs-screen-exclusions.jsonl")
    candidate_ids = {r["id"] for r in candidates}
    assert len(candidate_ids) == len(candidates)
    assert {r["id"] for r in screened}.isdisjoint(r["id"] for r in excluded)
    assert {r["id"] for r in screened + excluded} == candidate_ids
    for row in screened:
        assert row["annotation_status"] == "pending" and "label" not in row
        assert not row["advisory_before"]["has_advisory"]
        for side in ("before_dir", "after_dir"):
            manifest = json.loads((Path(row[side]) / "package.json").read_text())
            assert manifest["name"] == row["name"]
            version = row[side.removesuffix("_dir")]
            assert str(manifest["version"]).split("+", 1)[0] == version.split("+", 1)[0]
    result = {"typ_balance_and_advisories": "passed", "typ_hn_disjoint": "passed",
              "human_labels_not_fabricated": "passed", "audit_artifacts_present": "passed",
              "datadog_inventory_complete": "passed", "typ": len(typ),
              "hn_audit": len(hn), "mal_wyss_audit": len(mal),
              "datadog_archives": len(downloaded),
              "datadog_pairs_partition_and_identity": "passed",
              "datadog_pairs_screened": len(screened),
              "datadog_inventory_errors": sum(bool(r.get("error")) for r in latest.values())}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    verify(parser.parse_args().root)
