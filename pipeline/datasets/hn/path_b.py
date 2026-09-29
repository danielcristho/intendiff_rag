"""Hard-negative path B: registry search per category; fetch and verify on the host, match offline."""
import argparse
import json
from pathlib import Path

from pipeline.datasets.hn.rules import CATEGORIES, hn_candidate, hn_rejection, pair_delta, print_tally
from pipeline.samples.extract import write_plan
from pipeline.samples.fetch import Fetcher
from pipeline.samples.registry import package_doc, publisher, search_packages
from pipeline.samples.versions import recent_pairs
from pipeline.shared.config import layout
from pipeline.shared.hashing import name_order
from pipeline.shared.isolation import require_offline
from pipeline.shared.jsonl import read_jsonl, write_jsonl

DIST_FIELDS = ("tarball", "integrity", "shasum")


def entry_for(name, before, after):
    return {"name": name, "before": before, "after": after,
            "before_path": f"{name}/{name}@{before}", "after_path": f"{name}/{name}@{after}"}


# slim_packument keeps the fields the offline match and the host verify read.
def slim_packument(doc):
    return {"time": doc.get("time", {}),
            "versions": {version: {"dist": {key: value for key, value in (meta.get("dist") or {}).items()
                                            if key in DIST_FIELDS},
                                   "_npmUser": meta.get("_npmUser")}
                         for version, meta in doc.get("versions", {}).items()}}


def packument_path(out, name):
    return Path(out) / "packuments" / f"{name}.json"


def load_packument(out, name):
    path = packument_path(out, name)
    return json.loads(path.read_text()) if path.exists() else None


# fetch_category saves each searched package's packument and its recent release tarballs.
def fetch_category(category, out, fetcher, size=250, log=print):
    names = name_order(name for keyword in CATEGORIES[category]["keywords"]
                       for name in search_packages(keyword, size))
    plan, failed = [], 0
    for index, name in enumerate(names, 1):
        doc = load_packument(out, name)
        if doc is None:
            try:
                doc = slim_packument(package_doc(name))
            except Exception:  # noqa: BLE001
                failed += 1
                continue
            packument_path(out, name).parent.mkdir(parents=True, exist_ok=True)
            packument_path(out, name).write_text(json.dumps(doc))
        for before, after in recent_pairs(doc):
            rows, _ = fetcher.plan(doc, entry_for(name, before, after), out)
            plan.extend(rows or [])
        if index % 25 == 0:
            log(f"  {index}/{len(names)} packages")
    return names, plan, failed


# earliest_match returns the first release pair, oldest first, whose delta carries a category signal.
def earliest_match(doc, name, signals, out):
    for before, after in recent_pairs(doc):
        entry = entry_for(name, before, after)
        found, _ = pair_delta(entry, out)
        if found and signals & set(found):
            return entry, found
    return None, None


def match_category(category, names, out):
    matches, misses = [], 0
    for name in names:
        doc = load_packument(out, name)
        entry, found = earliest_match(doc, name, CATEGORIES[category]["signals"], out) if doc else (None, None)
        if entry:
            matches.append({"entry": entry, "delta": found})
        else:
            misses += 1
    return matches, misses


# verify checks each package's earliest match; trying a later pair would shop for one that passes.
def verify(category, matches, out, want, taken):
    kept, reasons = [], []
    for match in matches:
        if len(kept) == want:
            break
        entry = match["entry"]
        label = f"{entry['name']}@{entry['after']}"
        if label in taken:
            reasons.append((label, "already a pair"))
            continue
        doc = load_packument(out, entry["name"])
        why = hn_rejection(doc, entry["name"], entry["before"], entry["after"])
        if why:
            reasons.append((label, why))
            continue
        taken.add(label)
        kept.append({**hn_candidate(entry, match["delta"]), "publisher": publisher(doc, entry["after"]),
                     "source": "path-b", "search_category": category})
    return kept, reasons


# known_ids gathers the pairs in a subset or candidate file, so path B does not repeat one.
def known_ids(paths):
    return {row.get("id") or f"{row['name']}@{row['after']}" for path in paths for row in read_jsonl(path)}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="hn-path-b")
    parser.add_argument("step", choices=("fetch", "match", "verify"))
    parser.add_argument("--category", type=int, required=True, choices=sorted(CATEGORIES))
    parser.add_argument("--want", type=int, help="candidates to keep, for verify")
    args = parser.parse_args(argv)
    data, cat = layout(), args.category
    out = data.path_b
    if args.step == "fetch":
        names, plan, failed = fetch_category(cat, out, Fetcher(data))
        write_jsonl(out / f"packages.cat{cat}.jsonl", [{"name": name} for name in names])
        write_plan(out / f"extract.plan.cat{cat}.jsonl", plan)
        print(f"category {cat}: {len(names)} packages, {len(plan)} archives, {failed} packuments failed")
    elif args.step == "match":
        require_offline()
        names = [row["name"] for row in read_jsonl(out / f"packages.cat{cat}.jsonl")]
        matches, misses = match_category(cat, names, out)
        write_jsonl(out / f"matches.cat{cat}.jsonl", matches)
        print(f"category {cat}: {len(matches)} packages with a matching pair, {misses} without")
    else:
        if args.want is None:
            parser.error("verify needs --want")
        others = [p for p in out.glob("candidates.cat*.jsonl") if p.name != f"candidates.cat{cat}.jsonl"]
        taken = known_ids([data.pairs, data.pairs_dev, data.hn / "candidates.jsonl", *others])
        kept, rejected = verify(cat, read_jsonl(out / f"matches.cat{cat}.jsonl"), out, args.want, taken)
        write_jsonl(out / f"candidates.cat{cat}.jsonl", kept)
        print(f"{out / f'candidates.cat{cat}.jsonl'}: {len(kept)} candidates in category {cat}")
        print_tally(rejected)
