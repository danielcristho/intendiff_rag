"""Join acquired predecessors and advisory checks without assigning gold labels.

    python pipeline/datadog_screen.py --acquisition DIR
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from samples import load_jsonl
from wyss import write_jsonl


def screen(root):
    root = Path(root)
    extracted = {(r["name"], r["version"]): r for r in
                 load_jsonl(root / "extracted.datadog-before.jsonl")}
    advisories = {(r["name"], r["version"]): r for r in
                  load_jsonl(root / "datadog-before-advisories.jsonl")}
    rows = load_jsonl(root / "datadog.pair-candidates.jsonl")
    ready, excluded = [], []
    for row in rows:
        key = row["name"], row["before"]
        before, advisory = extracted.get(key), advisories.get(key)
        reasons = []
        if before is None or before.get("error"):
            reasons.append("predecessor_unavailable_or_invalid")
        elif before.get("rejected"):
            reasons.append("predecessor_has_rejected_archive_entries")
        if advisory is None or advisory.get("error") or "has_advisory" not in advisory:
            reasons.append("predecessor_advisory_check_missing")
        elif advisory["has_advisory"]:
            reasons.append("predecessor_advisory_present")
        if reasons:
            excluded.append(dict(row, reasons=reasons,
                                 predecessor_error=(before or {}).get("error"),
                                 advisory_before=advisory))
            continue
        ready.append(dict(row, subset="MAL", before_dir=before["dir"],
                          sha256_before_tarball=before["sha256"],
                          advisory_before=advisory,
                          screening_status="available_pair_clear_predecessor",
                          pending_checks=["text_payload", "campaign", "independent_annotations"]))
    ready.sort(key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    write_jsonl(root / "datadog.pairs-screened.jsonl", ready)
    write_jsonl(root / "datadog.pairs-screen-exclusions.jsonl", excluded)
    wyss_ids = {r["id"] for r in load_jsonl(root / "mal.audit.jsonl")}
    summary = {"candidates": len(rows), "available_clear_predecessor": len(ready),
               "excluded": len(excluded),
               "overlapping_exclusion_counts": dict(Counter(reason for row in excluded
                                                            for reason in row["reasons"])),
               "overlap_with_wyss_audit": sum(r["id"] in wyss_ids for r in ready),
               "gold_labels_assigned": 0,
               "note": "Availability and advisory screening only; not a final MAL test set."}
    (root / "datadog-screen-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition", required=True)
    screen(parser.parse_args().acquisition)
