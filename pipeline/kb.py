"""Select the malicious knowledge-base cards from the Datadog dataset (§3.4).

    python pipeline/kb.py --datadog data/datadog --out data/kb.skeleton.jsonl
    python pipeline/kb.py --selfcheck
"""
import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import campaign  # noqa: E402
import capability  # noqa: E402
from capability import CAPABILITIES, has_content, package_root  # noqa: E402
from collect import hash_key, read_listing  # noqa: E402

TOTAL_CARDS = 50
PER_CAMPAIGN = 2
SAMPLE_DIR = "samples/npm/malicious_intent"
ZIP_PASSWORD = b"infected"  # published in the Datadog dataset README
MAX_UNPACKED = 50 * 2**20  # guards against zip bombs; no card needs more
TEXT_FIELDS = ("intent", "behavior_chain", "code_excerpt", "rationale")


# pool lists every malicious-intent npm sample in hash order.
def pool(datadog):
    manifest = json.loads((datadog / "samples/npm/manifest.json").read_text())
    tree = subprocess.run(
        ["git", "-C", str(datadog), "ls-tree", "-r", "--name-only", "HEAD", SAMPLE_DIR],
        capture_output=True, text=True, check=True,
    ).stdout.split()
    entries = []
    for path in tree:
        # samples/npm/malicious_intent/<name...>/<version>/<file>.zip; scoped
        # names carry one extra segment.
        parts = path[len(SAMPLE_DIR) + 1:].split("/")
        name, version = "/".join(parts[:-2]), parts[-2]
        # A null manifest entry is Datadog's marker for malicious intent.
        if name in manifest and manifest[name] is None:
            entries.append({"name": name, "version": version, "path": path})
    return sorted(entries, key=lambda entry: hash_key(entry["name"], entry["version"]))


# unpack extracts one sample into the cache and returns its package root.
def unpack(datadog, entry, cache):
    target = cache / f"{entry['name'].replace('/', '__')}@{entry['version']}"
    if not target.exists():
        # git fetches this one blob on demand; the clone is blobless.
        blob = subprocess.run(
            ["git", "-C", str(datadog), "show", f"HEAD:{entry['path']}"],
            capture_output=True, check=True,
        ).stdout
        with tempfile.NamedTemporaryFile(suffix=".zip") as handle:
            handle.write(blob)
            handle.flush()
            with zipfile.ZipFile(handle.name) as archive:
                if sum(info.file_size for info in archive.infolist()) > MAX_UNPACKED:
                    target.mkdir(parents=True)
                    return None
                # ZipFile.extractall strips absolute paths and ".." and never
                # creates symlinks, so the sample cannot write outside target.
                archive.extractall(target, pwd=ZIP_PASSWORD)
    return manifest_root(target)


# manifest_root is the shallowest directory holding a package.json.
def manifest_root(extracted):
    # Datadog wraps samples in tmp/<random>/<name>/ next to its own
    # package_info-*.json, which is metadata, not package content.
    manifests = [
        path for path in extracted.rglob("package.json")
        if "node_modules" not in path.parts
    ]
    if not manifests:
        return None
    root = min(manifests, key=lambda path: (len(path.parts), str(path))).parent
    return package_root(root)


# file_hashes digests every text file, which is §3.6 (b) with no predecessor.
def file_hashes(root, empty):
    return campaign.added_hashes(empty, root)


# mal_hashes collects the added-file digests of every MAL test pair.
def mal_hashes(listing, roots, empty):
    digests = set()
    for entry in read_listing(listing):
        before, after = (package_root(roots / entry[side]) for side in ("before_path", "after_path"))
        if has_content(before) and has_content(after):
            digests |= campaign.added_hashes(before, after)
    return digests


# linked_cards returns the chosen cards a candidate would join by transitive closure.
def linked_cards(hashes, chosen):
    linked, frontier = set(), set(hashes)
    grew = True
    while grew:
        grew = False
        for card in chosen:
            if card["id"] not in linked and card["hashes"] & frontier:
                linked.add(card["id"])
                frontier |= card["hashes"]
                grew = True
    return linked


# select fills the cards round-robin over the capabilities in table order.
def select(entries, scan, test_hashes, total=TOTAL_CARDS, log=print):
    chosen, cursors, exhausted, taken = [], dict.fromkeys(CAPABILITIES, 0), set(), set()
    skipped = {"mal_campaign": set(), "campaign_full": set(), "unreadable": set()}
    while len(chosen) < total and len(exhausted) < len(CAPABILITIES):
        for wanted in CAPABILITIES:
            if len(chosen) >= total or wanted in exhausted:
                continue
            while cursors[wanted] < len(entries):
                entry = entries[cursors[wanted]]
                cursors[wanted] += 1
                key = f"{entry['name']}@{entry['version']}"
                if key in taken:
                    continue
                found = scan(entry)
                if found is None:
                    skipped["unreadable"].add(key)
                    continue
                if wanted not in found["delta"]:
                    continue
                if found["hashes"] & test_hashes:
                    skipped["mal_campaign"].add(key)
                    continue
                if len(linked_cards(found["hashes"], chosen)) >= PER_CAMPAIGN:
                    skipped["campaign_full"].add(key)
                    continue
                taken.add(key)
                chosen.append({"id": f"kb-mal-{key}", "entry": entry, "wanted": wanted, **found})
                break
            else:
                exhausted.add(wanted)
                log(f"capability {wanted} exhausted after {len(chosen)} cards")
    # Counted per sample: every capability pass revisits the same pool.
    return chosen, {reason: len(keys) for reason, keys in skipped.items()}


# skeleton turns a chosen card into a kb.jsonl row whose text the annotator writes.
def skeleton(card, campaign_id):
    row = {
        "id": card["id"],
        "name": card["entry"]["name"],
        "label": "malicious",
        "campaign": campaign_id,
        "source": "datadog",
        "delta": card["delta"],
        "selected_for": card["wanted"],
        # delta_evidence points the annotator at the code (§5.1: cards are
        # written from package content, never from model output).
        "delta_evidence": card["evidence"],
    }
    row.update(dict.fromkeys(TEXT_FIELDS, ""))
    return row


def assign_campaigns(chosen):
    items = [{"id": card["id"], "reports": [], "added_hashes": card["hashes"]} for card in chosen]
    return campaign.cluster(items)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--datadog", default="data/datadog")
    parser.add_argument("--mal-listing", default="data/wyss/data/malicious_updates.txt")
    parser.add_argument("--mal-roots", default="data/wyss/samples")
    parser.add_argument("--out", default="data/kb.skeleton.jsonl")
    args = parser.parse_args(argv)

    datadog = Path(args.datadog)
    cache = datadog / "extracted"
    empty = Path(tempfile.mkdtemp())
    test_hashes = mal_hashes(args.mal_listing, Path(args.mal_roots), empty)
    entries = pool(datadog)
    print(f"pool: {len(entries)} malicious-intent samples; MAL digests: {len(test_hashes)}")

    scanned = {}

    def scan(entry):
        key = (entry["name"], entry["version"])
        if key not in scanned:
            root = unpack(datadog, entry, cache)
            scanned[key] = None if root is None else {
                "delta": capability.capabilities(root),
                "evidence": capability.explain_version(root),
                "hashes": file_hashes(root, empty),
            }
        return scanned[key]

    chosen, skipped = select(entries, scan, test_hashes)
    labels = assign_campaigns(chosen)

    out = Path(args.out)
    with out.open("w") as handle:
        for card in chosen:
            handle.write(json.dumps(skeleton(card, labels[card["id"]])) + "\n")

    per_capability = {name: sum(name in card["delta"] for card in chosen) for name in CAPABILITIES}
    print(f"{out}: {len(chosen)} cards, {len(set(labels.values()))} campaigns, "
          f"{len(scanned)} samples scanned")
    print(f"skipped: {skipped}")
    print(f"cards per capability: {per_capability}")


def selfcheck():
    def entry(name):
        return {"name": name, "version": "1.0.0", "path": ""}

    scans = {
        "a": {"delta": ["network"], "hashes": {"h1"}, "evidence": {}},
        "b": {"delta": ["network"], "hashes": {"h1"}, "evidence": {}},
        "c": {"delta": ["network"], "hashes": {"h1"}, "evidence": {}},
        "d": {"delta": ["process_exec"], "hashes": {"mal"}, "evidence": {}},
        "e": {"delta": ["process_exec", "network"], "hashes": {"h2"}, "evidence": {}},
        "f": None,
    }
    entries = [entry(name) for name in "fabcde"]
    chosen, skipped = select(entries, lambda e: scans[e["name"]], {"mal"}, total=4, log=lambda _: None)
    ids = [card["entry"]["name"] for card in chosen]

    # A campaign never contributes a third card, even when it is next in hash order.
    assert ids.count("a") + ids.count("b") + ids.count("c") == 2, ids
    assert skipped["campaign_full"] >= 1, skipped
    # A card sharing a file with a MAL test pair is a leak, so it is never chosen.
    assert "d" not in ids and skipped["mal_campaign"] >= 1, skipped
    # Rotation reaches the next capability instead of draining the first one.
    assert chosen[1]["wanted"] == "process_exec" and ids[1] == "e", ids
    # Every card appears once, however many capabilities it carries.
    assert len(ids) == len(set(ids)), ids
    assert skipped["unreadable"] >= 1

    labels = assign_campaigns(chosen)
    assert labels[chosen[0]["id"]] == labels[chosen[2]["id"]], labels

    row = skeleton(chosen[0], "c1")
    assert all(row[field] == "" for field in TEXT_FIELDS) and row["name"] == "a"

    with tempfile.TemporaryDirectory() as work:
        wrapped = Path(work) / "tmp/x/pkg/package"
        wrapped.mkdir(parents=True)
        (wrapped / "package.json").write_text("{}")
        (Path(work) / "tmp/x/pkg/package_info-pkg.json").write_text("{}")
        nested = wrapped / "node_modules/dep"
        nested.mkdir(parents=True)
        (nested / "package.json").write_text("{}")
        # The Datadog wrapper and its metadata file are not package content.
        assert manifest_root(Path(work)) == wrapped
    print("kb selfcheck ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
