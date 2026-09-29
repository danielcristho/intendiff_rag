"""Extract and screen real package versions in a network-disabled container.

    python pipeline/corpus.py extract --samples FILE --into DIR --out FILE
    python pipeline/corpus.py screen --acquisition DIR --work DIR
"""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import capability
import samples
import typical
from wyss import write_jsonl


def load(path):
    return samples.load_jsonl(path)


def unpack(row, into):
    if row.get("error"):
        return {"name": row["name"], "version": row["version"], "error": row["error"]}
    try:
        result = samples.extract_one(row, into)
        root = Path(result["dir"])
        manifest = capability.package_json(root)
        if not manifest:
            # Older npm tarballs use a package-named root instead of package/.
            candidates = [p.parent for p in root.glob("*/package.json")]
            candidates = [p for p in candidates if typical.identity(p) == (row["name"], row["version"])]
            if len(candidates) == 1:
                root = candidates[0]
                manifest = capability.package_json(root)
        actual_version = str((manifest or {}).get("version", ""))
        if not manifest or manifest.get("name") != row["name"] or actual_version.split("+", 1)[0] != row["version"].split("+", 1)[0]:
            raise ValueError("extracted package.json does not match requested identity")
        return {"name": row["name"], "version": row["version"], "dir": str(root),
                "manifest_version": actual_version,
                "sha256": row["sha256"], "rejected": result["rejected"]}
    except Exception as exc:
        return {"name": row["name"], "version": row["version"], "error": str(exc)}


def extract(manifest, into, out):
    rows = load(manifest)
    with ThreadPoolExecutor(max_workers=4) as workers, Path(out).open("w") as output:
        for index, row in enumerate(workers.map(lambda r: unpack(r, into), rows), 1):
            output.write(json.dumps(row) + "\n")
            output.flush()
            if row.get("error"):
                print(json.dumps(row), flush=True)
            if index % 100 == 0 or index == len(rows):
                print(f"extracted {index}/{len(rows)}", flush=True)


def screen(acquisition):
    root = Path(acquisition)
    extracted = {(r["name"], r["version"]): r for r in load(root / "extracted.typical.jsonl")}
    advisory = {(r["name"], r["version"]): r for r in load(root / "advisories.jsonl")}
    downloaded = {(r["name"], r["version"]): r for r in load(root / "samples.typical.jsonl")}
    draw, pool = load(root / "typ.draw.jsonl"), load(root / "typ.pool.jsonl")
    selected, excluded, remaining = [], [], []
    for group in ("popular", "random"):
        for row in [r for r in draw + pool if r["group"] == group]:
            versions = [(row["name"], row[s]) for s in ("before", "after")]
            errors = [extracted.get(k, {}).get("error", "missing extraction" if k not in extracted else None)
                      for k in versions]
            checks = [advisory.get(k) for k in versions]
            reasons = []
            if any(errors):
                reasons.append("version_unavailable_or_invalid")
            if any(c is None for c in checks):
                reasons.append("advisory_check_missing")
            elif any(c["has_advisory"] for c in checks):
                reasons.append("advisory_present")
            if sum(r["group"] == group for r in selected) < 50:
                if reasons:
                    excluded.append(dict(row, reasons=reasons, version_errors=errors,
                                         advisory_ids=[v for c in checks if c for v in c["advisory_ids"]]))
                    continue
                selected.append(dict(row, subset="TYP", label="benign",
                                     label_basis="Wyss typical assumption; exact versions checked in OSV",
                                     before_dir=extracted[versions[0]]["dir"],
                                     after_dir=extracted[versions[1]]["dir"]))
            else:
                remaining.append(row)
    candidates, pool_excluded = [], []
    for row in remaining:
        keys = [(row["name"], row[s]) for s in ("before", "after")]
        if any(k not in extracted or extracted[k].get("error") for k in keys):
            pool_excluded.append(dict(row, reason="version_unavailable_or_invalid"))
            continue
        before, after = [Path(extracted[k]["dir"]) for k in keys]
        delta = capability.delta(before, after)
        if not delta:
            continue
        checks = [advisory.get(k) for k in keys]
        metadata = [json.loads(Path(downloaded[k]["registry_metadata"]).read_text()) for k in keys]
        publishers = [m.get("_npmUser", {}).get("name") for m in metadata]
        candidates.append(dict(row, subset="HN", annotation_status="pending",
                               before_dir=str(before), after_dir=str(after), delta=delta,
                               delta_evidence=capability.delta_evidence(before, after),
                               signal_categories=typical.signal_categories(delta),
                               advisory_checked=all(c is not None for c in checks),
                               advisory_ids=sorted({v for c in checks if c for v in c["advisory_ids"]}),
                               publishers=publishers,
                               same_publisher=bool(publishers[0]) and publishers[0] == publishers[1]))
    candidates.sort(key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    write_jsonl(root / "typ.selected.jsonl", selected)
    write_jsonl(root / "typ.excluded.jsonl", excluded)
    write_jsonl(root / "hn.candidates.jsonl", candidates)
    write_jsonl(root / "hn.pool-excluded.jsonl", pool_excluded)
    summary = {"typ_selected": len(selected), "typ_rejected_before_quota": len(excluded),
               "path_a_pool": len(remaining), "pool_unavailable": len(pool_excluded),
               "hn_with_delta": len(candidates),
               "hn_no_advisory_same_publisher": sum(r["advisory_checked"] and not r["advisory_ids"] and r["same_publisher"] for r in candidates),
               "per_signal_category": {str(n): sum(n in r["signal_categories"] for r in candidates) for n in range(1, 6)},
               "note": "HN candidates require documented-purpose verification and two independent annotations."}
    (root / "corpus-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    unpacker = sub.add_parser("extract")
    unpacker.add_argument("--samples", required=True)
    unpacker.add_argument("--into", required=True)
    unpacker.add_argument("--out", required=True)
    screener = sub.add_parser("screen")
    screener.add_argument("--acquisition", required=True)
    args = parser.parse_args()
    if args.command == "extract":
        extract(args.samples, args.into, args.out)
    else:
        screen(args.acquisition)
