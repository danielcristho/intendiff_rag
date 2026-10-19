"""Resolve update pairs for source-labelled malicious versions from external datasets (D97).

    python pipeline/external_mal.py pairs --out DIR
    python pipeline/external_mal.py before --out DIR     # inside --network none
    python pipeline/external_mal.py --selfcheck
"""
import argparse
import csv
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from collect import parse_semver, previous_version
from expansion_fetch import fetch_metadata
from expansion_screen import inspect_archive
from samples import load_jsonl
from wyss import write_jsonl

GUO_TIMES = Path("data/work/guo-20261014/meta/NPMStudy/Data/timecollect/time/malware_time.csv")
POOL = Path("data/acquisition/campaigns-20261013/combined-d96.json")
METADATA_CACHE = Path("data/upstream/guo-20261014/metadata")


# guo_versions decodes the dataset's "@scope##name" spelling of scoped packages.
def guo_versions(path=GUO_TIMES):
    with path.open() as stream:
        return [{"id": f"{r['package_name'].replace('##', '/')}@{r['version']}",
                 "name": r["package_name"].replace("##", "/"), "version": r["version"],
                 "source": "guo2026", "source_label": "malicious"} for r in csv.DictReader(stream)]


# missing_predecessor_reason separates first releases from packages whose
# earlier versions were unpublished (time entries survive, versions do not).
def missing_predecessor_reason(version, times):
    if version not in times:
        return "no publication time for v_t"
    earlier = [v for v in times if v not in ("created", "modified", "unpublished")
               and parse_semver(v) < parse_semver(version) and times[v] < times[version]]
    if earlier:
        return "earlier versions unpublished from registry"
    return "no earlier version (malicious from first release)"


# resolve_pair applies §3.1 (b): the predecessor must predate v_t and must not
# itself be listed malicious by any source we hold.
def resolve_pair(row, document, malicious_ids):
    if document.get("name") != row["name"]:
        return None, "registry identity mismatch"
    before = previous_version(document, row["version"])
    if before is None:
        return None, missing_predecessor_reason(row["version"], document.get("time", {}))
    if f"{row['name']}@{before}" in malicious_ids:
        return None, "predecessor listed malicious"
    dist = document.get("versions", {}).get(before, {}).get("dist")
    if not dist:
        return None, "predecessor not downloadable from registry"
    return dict(row, before=before, after=row["version"], dist_before=dist,
                published_at=document["time"][row["version"]],
                published_before=document["time"][before]), None


def pairs(out, workers):
    rows = guo_versions()
    roles = json.loads(POOL.read_text())["item_roles"]
    held = {i for i, role in roles.items() if role in ("mal_candidate", "kb_pool")}
    malicious_ids = held | {r["id"] for r in rows}
    fresh = [r for r in rows if r["id"] not in held]
    names = sorted({r["name"] for r in fresh})
    METADATA_CACHE.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=workers) as executor:
        metadata = {m["name"]: m for m in executor.map(
            lambda n: fetch_metadata({"name": n}, METADATA_CACHE), names)}
    write_jsonl(out / "metadata.jsonl", metadata.values())
    candidates, excluded = [], []
    for row in fresh:
        meta = metadata[row["name"]]
        if "error" in meta:
            excluded.append(dict(row, reason="registry metadata: " + meta["error"]))
            continue
        document = json.loads(Path(meta["metadata_file"]).read_text())
        pair, reason = resolve_pair(row, document, malicious_ids)
        if reason:
            excluded.append(dict(row, reason=reason))
        else:
            candidates.append(dict(pair, metadata_file=meta["metadata_file"],
                                   metadata_sha256=meta["metadata_sha256"]))
    write_jsonl(out / "pair-candidates.jsonl", candidates)
    write_jsonl(out / "pair-exclusions.jsonl", excluded)
    summary = {"source_versions": len(rows), "already_in_pool": len(rows) - len(fresh),
               "new_versions": len(fresh), "packages_queried": len(names),
               "pair_candidates": len(candidates),
               "exclusions": dict(Counter(r["reason"].split(":")[0] for r in excluded))}
    (out / "pairs-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


def before(out):
    work = Path("data/work/external-mal-20261014/before")
    rows = [inspect_archive(row, work) for row in load_jsonl(out / "archives.before.jsonl")]
    write_jsonl(out / "extracted.before.jsonl", rows)
    print(json.dumps({"predecessors": len(rows), "errors": sum("error" in r for r in rows)}))


def selfcheck():
    doc = {"name": "p", "versions": {"1.0.0": {"dist": {"tarball": "t"}}, "1.0.1": {}},
           "time": {"1.0.0": "2024-01-01", "1.0.1": "2024-02-01", "2.0.0": "2024-03-01"}}
    row = {"name": "p", "version": "2.0.0"}
    assert resolve_pair(row, doc, set())[1] == "predecessor not downloadable from registry"
    doc["versions"]["1.0.1"] = {"dist": {"tarball": "u"}}
    pair, reason = resolve_pair(row, doc, set())
    assert reason is None and pair["before"] == "1.0.1" and pair["dist_before"] == {"tarball": "u"}
    assert resolve_pair(row, doc, {"p@1.0.1"})[1] == "predecessor listed malicious"
    assert resolve_pair({"name": "p", "version": "1.0.0"}, doc, set())[1].startswith("no earlier version")
    gone = {"name": "p", "versions": {}, "time": {"created": "2024", "1.0.0": "2024-01-01", "1.0.1": "2024-02-01"}}
    assert resolve_pair({"name": "p", "version": "1.0.1"}, gone, set())[1] == "earlier versions unpublished from registry"
    assert resolve_pair({"name": "p", "version": "9.0.0"}, doc, set())[1] == "no publication time for v_t"
    assert resolve_pair(row, dict(doc, name="q"), set())[1] == "registry identity mismatch"
    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
        sys.exit()
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["pairs", "before"])
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pairs(out, args.workers) if args.stage == "pairs" else before(out)
