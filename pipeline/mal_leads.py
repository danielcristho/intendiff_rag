"""Resolve Draz source identifiers into independently verifiable npm pairs.

    python pipeline/mal_leads.py --out DIR --cache DIR
"""
import argparse
import csv
import hashlib
import io
import json
import zipfile
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from collect import previous_version
from expansion_fetch import fetch_metadata
from external_mal import guo_versions
from samples import load_jsonl
from wyss import write_jsonl


def source_rows(archive):
    with zipfile.ZipFile(archive) as source:
        member = next(n for n in source.namelist() if n.endswith("/data/raw/merged_dataset_usable.csv"))
        payload = source.read(member)
    return list(csv.DictReader(io.StringIO(payload.decode()))), member, hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--cache", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)
    archive = Path("data/upstream/draz-20261016/artifact.zip")
    source, member, source_digest = source_rows(archive)
    history = Path("data/acquisition/mal-expansion-20261016/campaigns-with-exposure/combined.json")
    old = json.loads(history.read_text())["campaigns"]
    blocked = {identity.rsplit("@", 1)[0] for identity in old}
    for path in [Path("data/acquisition/expansion-full-20261013/exposure-registry.jsonl"),
                 *[Path("data/evaluation/source-rag-v3-20261015") / name
                   for name in ("test.pairs.jsonl", "dev.pairs.jsonl", "kb.jsonl")]]:
        for row in load_jsonl(path):
            blocked.add(row.get("name"))
            blocked.update(row.get("related_names", []))
    unique, excluded = {}, []
    for row in source:
        if row["ecosystem"] != "npm" or row["label"] != "malicious":
            continue
        identity = row["package"] + "@" + row["version_after"]
        if row["package"] in blocked:
            excluded.append(dict(id=identity, reason="name_previously_held_or_exposed"))
            continue
        unique.setdefault(identity, dict(id=identity, name=row["package"], after=row["version_after"],
                                         lead_record=row, source_member=member, source_member_sha256=source_digest))
    leads = sorted(unique.values(), key=lambda r: hashlib.sha256(r["id"].encode()).hexdigest())
    write_jsonl(args.out / "leads.jsonl", leads)
    names = sorted({r["name"] for r in leads})
    print(json.dumps(dict(leads=len(leads), names=len(names))), flush=True)
    metadata = {}
    with ThreadPoolExecutor(max_workers=6) as workers, (args.out / "metadata.jsonl").open("w") as output:
        for index, row in enumerate(workers.map(lambda name: fetch_metadata(dict(name=name), args.cache), names), 1):
            metadata[row["name"]] = row
            output.write(json.dumps(row) + "\n"); output.flush()
            if index % 50 == 0 or index == len(names):
                print(json.dumps(dict(metadata=index, total=len(names))), flush=True)
    manifest = json.loads(Path("data/upstream/datadog-20261016/manifest-pinned.json").read_text())
    malicious = {r["id"] for r in guo_versions()}
    roles = json.loads(Path("data/acquisition/campaigns-20261013/combined-d96.json").read_text())["item_roles"]
    malicious.update(identity for identity, role in roles.items() if role in ("mal_candidate", "kb_pool"))
    candidates = []
    for lead in leads:
        try:
            meta = metadata[lead["name"]]
            if meta.get("error"):
                raise ValueError("registry_metadata_unavailable")
            document = json.loads(Path(meta["metadata_file"]).read_text())
            if document.get("name") != lead["name"]:
                raise ValueError("registry_identity_mismatch")
            if not document.get("versions", {}).get(lead["after"], {}).get("dist"):
                raise ValueError("target_archive_metadata_unavailable")
            before = previous_version(document, lead["after"])
            if before is None:
                raise ValueError("no_predecessor_with_verified_publication_order")
            listed = manifest.get(lead["name"], [])
            if listed is None or before in listed or f"{lead['name']}@{before}" in malicious:
                raise ValueError("predecessor_listed_malicious")
            candidates.append(dict(lead, before=before, published_at=document["time"][lead["after"]],
                                   published_before=document["time"][before], metadata_file=meta["metadata_file"],
                                   metadata_sha256=meta["metadata_sha256"],
                                   predecessor_differs_from_lead=before != lead["lead_record"]["version_before"]))
        except (KeyError, ValueError, OSError) as exc:
            excluded.append(dict(id=lead["id"], reason=str(exc)))
    write_jsonl(args.out / "pair-candidates.jsonl", candidates)
    write_jsonl(args.out / "pair-exclusions.jsonl", excluded)
    for side in ("before", "after"):
        write_jsonl(args.out / f"wanted.{side}.jsonl", [dict(name=r["name"], version=r[side]) for r in candidates])
    summary = dict(source_npm_records=sum(r["ecosystem"] == "npm" for r in source), leads=len(leads),
                   packages_queried=len(names), candidate_pairs=len(candidates),
                   exclusions=dict(Counter(r["reason"] for r in excluded)),
                   labels_accepted=0, pending="independent OSV MAL confirmation, predecessor checks, archives, campaigns")
    (args.out / "resolution-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
