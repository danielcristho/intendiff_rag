"""Publish preprocessed candidates to an isolated human-review data directory.

    python pipeline/review_package.py --acquisition DIR --out-dir DIR
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from normalization import VERSION
from artifact_manifest import write_manifest
from samples import load_jsonl
from wyss import write_jsonl


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--campaigns", default="combined-campaigns-complete.json")
    args = parser.parse_args()
    root, out = Path(args.acquisition), Path(args.out_dir)
    expected = {r["id"] for r in load_jsonl(root / "preprocess.manifest.jsonl")}
    latest = {r["id"]: r for r in load_jsonl(root / "pairs.preprocessed-v2.jsonl")}
    if set(latest) != expected:
        raise ValueError(f"preprocessing incomplete: {len(latest)}/{len(expected)} records")
    checksums = {(r["name"], r["version"]): r.get("sha256") for name in
                 ("samples.typical.jsonl", "samples.datadog-before.jsonl")
                 for r in load_jsonl(root / name) if not r.get("error")}
    inventory = {r["id"]: r for r in load_jsonl(root / "datadog.inventory.jsonl")}
    clustering = json.loads((root / args.campaigns).read_text())
    if not clustering["complete_for_available_items"] or clustering["failures"]:
        raise ValueError("campaign fingerprinting is incomplete for available items")
    prepared, review, excluded = [], [], []
    for row in latest.values():
        if row.get("error"):
            excluded.append({"id": row["id"], "reasons": ["preprocessing_error"], "error": row["error"]})
            continue
        assert row["preprocessing"]["version"] == VERSION
        assert row["diff_tokens"] <= 28000
        assert hashlib.sha256(row["diff"].encode()).hexdigest() == row["diff_sha256"]
        for side in ("before", "after"):
            row[f"sha256_{side}"] = checksums.get((row["name"], row[side]))
        if row["id"] in inventory:
            row["sha256_after"] = inventory[row["id"]]["sha256"]
        if row["subset"] == "MAL":
            row["campaign"] = clustering["campaigns"][row["id"]]
            row["campaign_scope"] = clustering["scope"]
        prepared.append(row)
        if row["subset"] == "TYP":
            continue
        assert row["annotation_status"] == "pending" and "label" not in row
        reasons = []
        if row["subset"] == "HN":
            if row.get("advisory_ids"):
                reasons.append("advisory_present")
            if not row.get("same_publisher"):
                reasons.append("publisher_not_verified_same")
        elif not row.get("advisory_before") or row["advisory_before"]["has_advisory"]:
            reasons.append("predecessor_not_verified_advisory_clear")
        if reasons:
            excluded.append({"id": row["id"], "reasons": reasons})
            continue
        # Source verdicts and predictions are absent from the annotation payload.
        review.append({k: v for k, v in row.items() if k not in ("source_label", "pred", "label")})
    prepared.sort(key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    review.sort(key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(root / "pairs.prepared.jsonl", prepared)
    temporary = out / "pairs.jsonl.tmp"
    write_jsonl(temporary, review)
    temporary.replace(out / "pairs.jsonl")
    write_jsonl(root / "review-exclusions.jsonl", excluded)
    summary = {"preprocessing_version": VERSION, "expected": len(expected),
               "preprocessed": len(prepared), "preprocessing_errors": len(expected) - len(prepared),
               "subsets": dict(Counter(r["subset"] for r in prepared)),
               "truncated": sum(r["truncated"] for r in prepared),
               "max_diff_tokens": max(r["diff_tokens"] for r in prepared),
               "pairs_with_fallback": sum(r["preprocessing"]["fallback_files"] > 0 for r in prepared),
               "fallback_files": sum(r["preprocessing"]["fallback_files"] for r in prepared),
               "review_candidates": len(review), "review_subsets": dict(Counter(r["subset"] for r in review)),
               "review_path": str(out / "pairs.jsonl"), "final_test_set": False,
               "campaigns_complete_for_available_items": True,
               "campaign_scope": clustering["scope"],
               "note": "Screened candidates for independent review; incident verification, labels and final test/KB selection remain pending. See campaign_scope for pool coverage."}
    (root / "preprocessing-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    write_manifest(root / "artifact-manifest-review.json", [
        root / "preprocess.manifest.jsonl", root / "pairs.preprocessed-v2.jsonl",
        root / "pairs.prepared.jsonl", root / args.campaigns,
        root / "preprocessing-summary.json", root / "review-exclusions.jsonl",
        out / "pairs.jsonl", *Path(__file__).parent.glob("*.py")])
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
