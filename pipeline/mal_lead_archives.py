"""Acquire independently confirmed MAL pairs, then prepare them offline.

    python pipeline/mal_lead_archives.py fetch --root DIR --cache DIR
    python pipeline/mal_lead_archives.py prepare --root DIR --work DIR
"""
import argparse
import hashlib
import json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import partial
from pathlib import Path

from expansion_fetch import fetch_archive
from expansion_screen import inspect_archive
from samples import load_jsonl
from wyss import write_jsonl


def advisory_gate(pair, before, after):
    for side, check in (("before", before), ("after", after)):
        if not check or check.get("error") or "has_advisory" not in check:
            return "advisory_check_missing"
        if (check.get("name"), check.get("version")) != (pair["name"], pair[side]):
            return "advisory_identity_mismatch"
    if before["has_advisory"]:
        return "predecessor_advisory_present"
    if not any(key.startswith("MAL-") for key in after.get("advisory_ids", [])):
        return "target_has_no_MAL_confirmation"
    return None


def fetch(root, cache):
    checks = {side: {(r["name"], r["version"]): r for r in
                     load_jsonl(root / f"advisories.{side}.jsonl")} for side in ("before", "after")}
    ready, excluded, wanted = [], [], {}
    for pair in load_jsonl(root / "pair-candidates.jsonl"):
        before, after = [checks[side].get((pair["name"], pair[side])) for side in ("before", "after")]
        reason = advisory_gate(pair, before, after)
        if reason:
            excluded.append(dict(id=pair["id"], reason=reason))
            continue
        raw = Path(pair["metadata_file"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != pair["metadata_sha256"]:
            raise ValueError("registry metadata changed")
        document = json.loads(raw)
        for side in ("before", "after"):
            key = pair["name"], pair[side]
            wanted[key] = dict(name=key[0], version=key[1], dist=document["versions"][key[1]]["dist"],
                               registry_metadata=pair["metadata_file"], metadata_sha256=pair["metadata_sha256"])
        ready.append(dict(pair, advisory_before=before, advisory_after=after))
    write_jsonl(root / "advisory-accepted.jsonl", ready)
    write_jsonl(root / "advisory-exclusions.jsonl", excluded)
    write_jsonl(root / "wanted.archives.jsonl", wanted.values())
    cache.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=6) as workers, (root / "archives.jsonl").open("w") as output:
        for index, row in enumerate(workers.map(lambda r: fetch_archive(r, cache), wanted.values()), 1):
            results.append(row)
            output.write(json.dumps(row) + "\n"); output.flush()
            if index % 25 == 0 or index == len(wanted):
                print(json.dumps(dict(downloads=index, total=len(wanted), errors=sum("error" in r for r in results))), flush=True)
    summary = dict(advisory_accepted_pairs=len(ready), names=len({r["name"] for r in ready}),
                   exclusions=dict(Counter(r["reason"] for r in excluded)), archive_requests=len(wanted),
                   downloaded=sum("error" not in r for r in results), archive_errors=sum("error" in r for r in results))
    (root / "download-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


def prepare(root, work):
    rows = load_jsonl(root / "archives.jsonl")
    extracted = []
    with ProcessPoolExecutor(max_workers=2) as workers, (root / "extracted.jsonl").open("w") as output:
        for index, row in enumerate(workers.map(partial(inspect_archive, work=work), rows), 1):
            extracted.append(row)
            output.write(json.dumps(row) + "\n"); output.flush()
            if index % 25 == 0 or index == len(rows):
                print(json.dumps(dict(inspected=index, total=len(rows))), flush=True)
    by_version = {(r["name"], r["version"]): r for r in extracted}
    ready, excluded = [], []
    source = root / "advisories.after.jsonl"
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    for pair in load_jsonl(root / "advisory-accepted.jsonl"):
        before, after = [by_version[(pair["name"], pair[side])] for side in ("before", "after")]
        if before.get("error") or after.get("error"):
            excluded.append(dict(id=pair["id"], before_error=before.get("error"), after_error=after.get("error")))
            continue
        ready.append(dict(pair, before_dir=before["dir"], after_dir=after["dir"],
                          sha256_before=before["sha256"], sha256_after=after["sha256"],
                          sha256_before_tree=before["tree_sha256"], sha256_after_tree=after["tree_sha256"],
                          subset="MAL", label="malicious", source_label="malicious", source="osv-via-draz-lead",
                          annotation_status="source_labelled", evaluation_scope="candidate_new_holdout",
                          label_provenance=dict(path=str(source), sha256=source_digest,
                                                record_id=pair["id"], basis="independently_confirmed_OSV_MAL")))
    write_jsonl(root / "pairs-screened.jsonl", ready)
    write_jsonl(root / "archive-exclusions.jsonl", excluded)
    summary = dict(available_pairs=len(ready), names=len({r["name"] for r in ready}), excluded=len(excluded),
                   campaign_screening_pending=True, sample_execution=False)
    (root / "screen-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("fetch", "prepare"))
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--cache", type=Path)
    parser.add_argument("--work", type=Path)
    args = parser.parse_args()
    if args.stage == "fetch":
        fetch(args.root, args.cache)
    else:
        prepare(args.root, args.work)
