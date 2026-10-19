"""Prepare source evidence for human annotation without generating labels.

    python pipeline/audit_materials.py --acquisition DIR --mal-root DIR --out DIR
"""
import argparse
import hashlib
import json
from pathlib import Path

import capability
import campaign
import smartdiff
from samples import load_jsonl
from wyss import write_jsonl


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().encode()
        with path.open("rb") as content:
            file_hash = hashlib.file_digest(content, "sha256").digest()
        digest.update(len(relative).to_bytes(8, "big") + relative + file_hash)
    return digest.hexdigest()


def material(row, before, after, out):
    # The replication ZIP mixes bare package roots and retained package/ wrappers.
    before = resolve_root(before, row["name"], row["before"])
    after = resolve_root(after, row["name"], row["after"])
    before_json, after_json = capability.package_json(before), capability.package_json(after)
    if before_json.get("name") == after_json.get("name") != row["name"]:
        row = dict(row, source_name=row["name"], source_id=row["id"],
                   name=after_json["name"], id=f"{after_json['name']}@{row['after']}")
    expected_before = row["name"], row["before"]
    expected_after = row["name"], row["after"]
    if (before_json.get("name"), str(before_json.get("version", "")).split("+", 1)[0]) != expected_before:
        raise ValueError(f"before identity mismatch: {before}")
    if (after_json.get("name"), str(after_json.get("version", "")).split("+", 1)[0]) != expected_after:
        raise ValueError(f"after identity mismatch: {after}")
    key = hashlib.sha256(row["id"].encode()).hexdigest()
    target = out / "diffs" / (key + ".diff")
    diff = smartdiff.relabel_paths(smartdiff.raw_diff(before, after), before, after)
    target.write_text(diff)
    return dict(row, before_dir=str(before), after_dir=str(after),
                annotation_status="pending", audit_diff=str(target),
                audit_diff_kind="raw_zero_context_before_normalization",
                sha256_before_tree=tree_digest(before), sha256_after_tree=tree_digest(after),
                delta=row["delta"] if "delta" in row else capability.delta(before, after),
                delta_evidence=row["delta_evidence"] if "delta_evidence" in row else capability.delta_evidence(before, after))


def resolve_root(root, name, version):
    candidates = [root, root / "package"]
    matches = [p for p in candidates if str(capability.package_json(p).get("version", "")).split("+", 1)[0] == version]
    if len(matches) != 1:
        raise ValueError(f"expected one package root for {name}@{version} in {root}")
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--acquisition", required=True)
    parser.add_argument("--mal-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root, out = Path(args.acquisition), Path(args.out)
    (out / "diffs").mkdir(parents=True, exist_ok=True)
    advisory = {(r["name"], r["version"]): r for r in
                load_jsonl(root / "advisories.jsonl") + load_jsonl(root / "alias-advisories.jsonl")}
    rows, failures, campaigns = [], [], []
    for row in load_jsonl(root / "mal.source.jsonl"):
        before = Path(args.mal_root) / row["upstream_before"]
        after = Path(args.mal_root) / row["upstream_after"]
        try:
            result = material(row, before, after, out)
            result["subset"] = "MAL"
            result["advisory_before"] = advisory.get((result["name"], result["before"]))
            result["advisory_after"] = advisory.get((result["name"], result["after"]))
            rows.append(result)
            before, after = Path(result["before_dir"]), Path(result["after_dir"])
            reports = [identifier for identifier in (result["advisory_after"] or {}).get("advisory_ids", [])
                       if identifier.startswith("MAL-")]
            campaigns.append({"id": result["id"], "reports": reports,
                              "added_hashes": sorted(campaign.added_hashes(before, after)),
                              "code": campaign.added_code(before, after)})
        except Exception as exc:
            failures.append(dict(row, error=str(exc)))
        print(f"audit {len(rows) + len(failures)}/46", flush=True)
    write_jsonl(root / "mal.audit.jsonl", rows)
    write_jsonl(root / "mal.audit-failures.jsonl", failures)
    write_jsonl(out / "mal.campaign-items.jsonl", campaigns)
    print(json.dumps({"source_pairs": len(rows) + len(failures), "audit_ready": len(rows),
                      "failures": len(failures), "labels_assigned": 0}))
    hn_rows, hn_failures = [], []
    for row in load_jsonl(root / "hn.candidates.jsonl"):
        try:
            hn_rows.append(material(row, Path(row["before_dir"]), Path(row["after_dir"]), out))
        except Exception as exc:
            hn_failures.append(dict(row, error=str(exc)))
    write_jsonl(root / "hn.audit.jsonl", hn_rows)
    write_jsonl(root / "hn.audit-failures.jsonl", hn_failures)
    print(json.dumps({"hn_audit_ready": len(hn_rows), "hn_failures": len(hn_failures)}))


if __name__ == "__main__":
    main()
