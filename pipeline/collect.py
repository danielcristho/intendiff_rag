"""Candidate collection from the npm registry.

    python pipeline/collect.py search --category 2 --size 250
    python pipeline/collect.py pairs --package husky
    python pipeline/collect.py typical --listing POPULAR.txt --take 50 --out data/typ
    python pipeline/collect.py candidates --listing POPULAR.txt --exclude data/typ/taken.txt --want 300 --out data/hn
    python pipeline/collect.py --selfcheck
"""
import argparse
import collections
import hashlib
import io
import json
import sys
import tarfile
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import capability  # noqa: E402

REGISTRY = "https://registry.npmjs.org"
OSV = "https://api.osv.dev/v1/query"
RECENT_RELEASES = 20

# §3.3. Keywords drive the search; signals only filter candidates, because the
# category itself is decided by the documented purpose, never by the signal.
HN_CATEGORIES = {
    1: {"name": "Process execution & tooling", "keywords": ["postinstall", "git hooks"],
        "signals": {"install_script", "process_exec"}},
    2: {"name": "Telemetry", "keywords": ["telemetry", "analytics"],
        "signals": {"network"}},
    3: {"name": "Licensing", "keywords": ["license key"],
        "signals": {"obfuscation", "dynamic_code"}},
    4: {"name": "Network, scraper, download", "keywords": ["scraper", "download binary"],
        "signals": {"network", "process_exec"}},
    5: {"name": "Deprecation & structural change", "keywords": ["deprecated"],
        "signals": {"large_deletion", "dependency_change"}},
}


# §3 orders every selection by this digest, never by popularity.
def hash_key(name, version):
    return hashlib.sha256(f"{name}@{version}".encode()).hexdigest()


# hash_order sorts items by the SHA-256 of their name@version.
def hash_order(items, key=lambda item: (item["name"], item["version"])):
    return sorted(items, key=lambda item: hash_key(*key(item)))


# parse_semver returns a comparable key for a version string.
def parse_semver(version):
    # A prerelease sorts below the same release, which is what semver requires
    # and what a plain numeric tuple would get backwards.
    core, _, prerelease = str(version).partition("-")
    numbers = []
    for part in core.split(".")[:3]:
        digits = "".join(ch for ch in part if ch.isdigit())
        numbers.append(int(digits) if digits else 0)
    while len(numbers) < 3:
        numbers.append(0)
    return (*numbers, 0 if prerelease else 1, prerelease)


# previous_version returns v_(t-1) for a target version, or None (D27).
def previous_version(doc, target):
    # Highest semver below the target that also predates it — not "previous by
    # time", which pairs across parallel release lines.
    times = doc.get("time", {})
    target_time = times.get(target)
    target_key = parse_semver(target)

    candidates = [
        version
        for version in doc.get("versions", {})
        if parse_semver(version) < target_key
        and (target_time is None or times.get(version, "") < target_time)
    ]
    return max(candidates, key=parse_semver) if candidates else None


# recent_pairs returns the newest releases as (before, after) pairs, oldest first.
def recent_pairs(doc, limit=RECENT_RELEASES):
    versions = sorted(doc.get("versions", {}), key=parse_semver)[-limit:]
    pairs = []
    for version in versions:
        before = previous_version(doc, version)
        if before:
            pairs.append((before, version))
    return pairs


def fetch_json(url, timeout=30):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


def search_packages(keyword, size=250, timeout=30):
    query = urllib.parse.urlencode({"text": keyword, "size": min(size, 250)})
    found = fetch_json(f"{REGISTRY}/-/v1/search?{query}", timeout)
    return [entry["package"]["name"] for entry in found.get("objects", [])]


def package_doc(name, timeout=30):
    return fetch_json(f"{REGISTRY}/{urllib.parse.quote(name, safe='@')}", timeout)


def tarball_url(doc, version):
    return doc.get("versions", {}).get(version, {}).get("dist", {}).get("tarball")


def has_advisory(name, version, timeout=30):
    payload = json.dumps({"package": {"name": name, "ecosystem": "npm"}, "version": version})
    request = urllib.request.Request(
        OSV, data=payload.encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return bool(json.loads(response.read()).get("vulns"))


# listing_entry splits one "<root>/<name>/<name>@<version>" path from a listing.
def listing_entry(path):
    rest = path.split("/", 1)[1]
    cut = rest.rfind("@")
    # The name repeats, so its length is half of what precedes the version, and
    # taking the tail survives a scoped name carrying its own "@" and "/".
    repeated, version = rest[:cut], rest[cut + 1:]
    return repeated[-((len(repeated) - 1) // 2):], version


# read_listing parses a "before,after" listing into one entry per line.
def read_listing(path):
    entries = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        before_path, after_path = line.strip().split(",")
        (name, before), (_, after) = listing_entry(before_path), listing_entry(after_path)
        entries.append({"name": name, "before": before, "after": after,
                        "before_path": before_path, "after_path": after_path})
    return entries


# unpack downloads one version's tarball into target, or reports why it could not.
def unpack(url, target, timeout=60):
    target = Path(target)
    if target.is_dir() and any(target.rglob("*")):
        return "cached"
    target.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = io.BytesIO(response.read())
        with tarfile.open(fileobj=payload, mode="r:gz") as archive:
            # filter="data" refuses absolute paths, symlinks and "..", so a
            # hostile tarball cannot write outside target. These are untrusted
            # packages; they are unpacked and read, never installed or run.
            archive.extractall(target, filter="data")
    except Exception as exc:  # noqa: BLE001 - any failure means "no sample"
        return f"{type(exc).__name__}: {exc}"
    return None


# draw_typical takes pairs in hash order, skipping any version with an advisory.
def draw_typical(entries, take, out, skip_advisory=True, log=print):
    taken, reasons = [], []
    ordered = hash_order(entries, key=lambda entry: (entry["name"], entry["after"]))
    for entry in ordered:
        if len(taken) == take:
            break
        name, before, after = entry["name"], entry["before"], entry["after"]
        try:
            doc = package_doc(name)
        except Exception as exc:  # noqa: BLE001
            reasons.append((f"{name}@{after}", f"packument: {type(exc).__name__}"))
            continue
        urls = [tarball_url(doc, version) for version in (before, after)]
        if not all(urls):
            reasons.append((f"{name}@{after}", "unpublished"))
            continue
        # §3.2 assumes TYP is benign, so a version with an advisory is replaced
        # by the next draw rather than kept and relabelled.
        if skip_advisory and any(has_advisory(name, version) for version in (before, after)):
            reasons.append((f"{name}@{after}", "advisory"))
            continue
        failed = [unpack(url, Path(out) / path)
                  for url, path in zip(urls, (entry["before_path"], entry["after_path"]))]
        problem = next((why for why in failed if why and why != "cached"), None)
        if problem:
            reasons.append((f"{name}@{after}", problem))
            continue
        taken.append(entry)
        log(f"[{len(taken)}/{take}] {name}@{before} -> {after}")
    return taken, reasons


# publisher returns who published one version, or None when the packument omits it.
def publisher(doc, version):
    entry = doc.get("versions", {}).get(version, {})
    return (entry.get("_npmUser") or {}).get("name")


# matching_categories lists the §3.3 categories a capability delta could belong to.
def matching_categories(delta):
    found = set(delta)
    return [number for number, spec in sorted(HN_CATEGORIES.items())
            if spec["signals"] & found]


# screen_candidates keeps the pairs that pass every §3.3 criterion a machine can check.
def screen_candidates(entries, want, out, log=print):
    kept, reasons = [], []
    for entry in hash_order(entries, key=lambda item: (item["name"], item["after"])):
        if len(kept) == want:
            break
        name, before, after = entry["name"], entry["before"], entry["after"]
        label = f"{name}@{after}"
        try:
            doc = package_doc(name)
        except Exception as exc:  # noqa: BLE001
            reasons.append((label, f"packument: {type(exc).__name__}"))
            continue
        urls = [tarball_url(doc, version) for version in (before, after)]
        if not all(urls):
            reasons.append((label, "unpublished"))
            continue
        if any(has_advisory(name, version) for version in (before, after)):
            reasons.append((label, "advisory"))
            continue
        # A change of publisher is the takeover this study is trying to detect, so
        # it cannot also serve as a benign hard negative (§3.3).
        who = [publisher(doc, version) for version in (before, after)]
        if all(who) and who[0] != who[1]:
            reasons.append((label, f"publisher {who[0]} -> {who[1]}"))
            continue
        paths = [Path(out) / entry[side] for side in ("before_path", "after_path")]
        failed = [unpack(url, path) for url, path in zip(urls, paths)]
        problem = next((why for why in failed if why and why != "cached"), None)
        if problem:
            reasons.append((label, problem))
            continue
        roots = [capability.package_root(path) for path in paths]
        if not all(capability.has_content(root) for root in roots):
            reasons.append((label, "empty"))
            continue
        delta = capability.delta(*roots)
        if not delta:
            reasons.append((label, "delta kosong"))
            continue
        kept.append({**entry, "delta": delta, "categories": matching_categories(delta),
                     "publisher": who[1]})
        log(f"[{len(kept)}/{want}] {label}  {','.join(delta)}")
    return kept, reasons


def candidates_for(name, doc, category, limit=RECENT_RELEASES):
    return [
        {
            "id": f"{name}@{after}",
            "name": name,
            "before": before,
            "after": after,
            "subset": "HN",
            "category": category,
            "source": "path-b",
            "tarball_before": tarball_url(doc, before),
            "tarball_after": tarball_url(doc, after),
        }
        for before, after in recent_pairs(doc, limit)
    ]


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    find = sub.add_parser("search", help="path B: registry search for one category")
    find.add_argument("--category", type=int, required=True, choices=sorted(HN_CATEGORIES))
    find.add_argument("--size", type=int, default=250)

    walk = sub.add_parser("pairs", help="list the recent update pairs of one package")
    walk.add_argument("--package", required=True)
    walk.add_argument("--limit", type=int, default=RECENT_RELEASES)

    screen = sub.add_parser("candidates", help="§3.3 path A: screen typical updates for HN")
    screen.add_argument("--listing", required=True, action="append")
    screen.add_argument("--exclude", action="append", default=[],
                        help="a listing whose pairs are already spoken for")
    screen.add_argument("--want", type=int, required=True)
    screen.add_argument("--out", required=True)

    draw = sub.add_parser("typical", help="§3.2: draw TYP pairs and unpack their tarballs")
    draw.add_argument("--listing", required=True, action="append",
                      help="a Wyss typical_updates listing; repeat for each group")
    draw.add_argument("--take", type=int, required=True, help="pairs to keep per listing")
    draw.add_argument("--out", required=True)

    args = parser.parse_args(argv)

    if args.command == "search":
        category = HN_CATEGORIES[args.category]
        names = []
        for keyword in category["keywords"]:
            names.extend(search_packages(keyword, args.size))
        # Deduplicate while keeping the registry's relevance order stable; the
        # hash ordering is applied later, over resolved candidates.
        unique = list(dict.fromkeys(names))
        print(json.dumps({"category": args.category, "keywords": category["keywords"],
                          "signals": sorted(category["signals"]), "packages": unique}, indent=2))
    elif args.command == "pairs":
        doc = package_doc(args.package)
        for before, after in recent_pairs(doc, args.limit):
            print(f"{args.package}  {before} -> {after}")
    elif args.command == "candidates":
        out = Path(args.out)
        spoken_for = {entry["after_path"] for listing in args.exclude
                      for entry in read_listing(listing)}
        pool = [entry for listing in args.listing for entry in read_listing(listing)
                if entry["after_path"] not in spoken_for]
        print(f"{len(pool)} kandidat jalur A setelah membuang {len(spoken_for)} pair TYP")
        kept, rejected = screen_candidates(pool, args.want, out)
        out.mkdir(parents=True, exist_ok=True)
        with (out / "candidates.jsonl").open("w") as handle:
            for entry in kept:
                handle.write(json.dumps(entry) + "\n")
        print(f"\n{out / 'candidates.jsonl'}: {len(kept)} kandidat")
        tally = collections.Counter(why.split(":")[0].split(" ")[0] for _, why in rejected)
        for why, count in tally.most_common():
            print(f"  {count:5}  ditolak: {why}")
        per_category = collections.Counter(c for entry in kept for c in entry["categories"])
        print("  sinyal cocok kategori:", dict(sorted(per_category.items())))
    else:
        out = Path(args.out)
        kept, rejected = [], []
        for listing in args.listing:
            print(f"--- {listing}")
            taken, reasons = draw_typical(read_listing(listing), args.take, out)
            kept.extend(taken)
            rejected.extend(reasons)
        (out / "taken.txt").write_text(
            "".join(f"{entry['before_path']},{entry['after_path']}\n" for entry in kept))
        print(f"\n{out / 'taken.txt'}: {len(kept)} pair")
        for pair_id, why in rejected:
            print(f"  ditolak {pair_id}: {why}")


def selfcheck():
    assert parse_semver("1.2.3") > parse_semver("1.2.2")
    assert parse_semver("1.10.0") > parse_semver("1.9.0"), "numeric, not lexicographic"
    assert parse_semver("1.0.0-beta.1") < parse_semver("1.0.0"), "a prerelease sorts below release"
    assert parse_semver("2") == parse_semver("2.0.0"), "missing parts default to zero"

    # Parallel release lines publish minutes apart; a time rule would pair
    # 1.14.1 with 0.30.4, which are unrelated.
    doc = {
        "versions": {"0.30.3": {}, "0.30.4": {}, "1.14.0": {}, "1.14.1": {}},
        "time": {
            "0.30.3": "2026-01-01T00:00:00Z",
            "1.14.0": "2026-02-01T00:00:00Z",
            "0.30.4": "2026-03-31T10:00:00Z",
            "1.14.1": "2026-03-31T10:05:00Z",
        },
    }
    assert previous_version(doc, "1.14.1") == "1.14.0", previous_version(doc, "1.14.1")
    assert previous_version(doc, "0.30.4") == "0.30.3", previous_version(doc, "0.30.4")
    # The oldest version has no predecessor and must not invent one.
    assert previous_version(doc, "0.30.3") is None

    # A version published before a lower-numbered one is still not its successor.
    out_of_order = {
        "versions": {"1.0.0": {}, "1.1.0": {}},
        "time": {"1.1.0": "2026-01-01T00:00:00Z", "1.0.0": "2026-06-01T00:00:00Z"},
    }
    assert previous_version(out_of_order, "1.1.0") is None, "1.0.0 came later, so it is not v_(t-1)"

    pairs = recent_pairs(doc)
    assert ("1.14.0", "1.14.1") in pairs and ("0.30.3", "0.30.4") in pairs
    assert all(parse_semver(before) < parse_semver(after) for before, after in pairs)
    assert len(recent_pairs(doc, limit=2)) <= 2

    # Hash ordering is deterministic and independent of the input order (§3).
    items = [{"name": "a", "version": "1.0.0"}, {"name": "b", "version": "2.0.0"},
             {"name": "c", "version": "3.0.0"}]
    assert hash_order(items) == hash_order(list(reversed(items)))
    assert hash_key("a", "1.0.0") != hash_key("a", "1.0.1")

    entries = candidates_for("demo", doc, category=2)
    assert {e["subset"] for e in entries} == {"HN"}
    assert {e["category"] for e in entries} == {2}
    assert all(e["id"] == f"demo@{e['after']}" for e in entries)

    # Every category keeps the keywords and signals §3.3 fixed.
    assert set(HN_CATEGORIES) == {1, 2, 3, 4, 5}
    assert HN_CATEGORIES[2]["signals"] == {"network"}
    assert "deprecated" in HN_CATEGORIES[5]["keywords"]

    # §3.3 maps a delta onto the categories whose filter signals it could satisfy.
    assert matching_categories(["network"]) == [2, 4]
    assert matching_categories(["install_script"]) == [1]
    assert matching_categories(["dependency_change"]) == [5]
    assert matching_categories([]) == [], "an empty delta belongs to no category"
    assert matching_categories(["network", "process_exec"]) == [1, 2, 4]

    doc = {"versions": {"1.0.0": {"_npmUser": {"name": "alice"}}, "1.0.1": {}}}
    assert publisher(doc, "1.0.0") == "alice"
    assert publisher(doc, "1.0.1") is None, "a missing _npmUser is unknown, not a change"

    assert listing_entry("m_samples/coa/coa@2.0.3") == ("coa", "2.0.3")
    assert listing_entry("r_samples/@a/b/@a/b@1.2.1") == ("@a/b", "1.2.1")
    assert listing_entry("b/commander/commander@12.0.0-1") == ("commander", "12.0.0-1")

    import tempfile
    scratch = Path(tempfile.mkdtemp())
    (scratch / "list.txt").write_text("b/x/x@1.0.0,b/x/x@1.0.1\n\nb/y/y@2.0.0,b/y/y@2.1.0\n")
    parsed = read_listing(scratch / "list.txt")
    assert [e["name"] for e in parsed] == ["x", "y"], parsed
    assert parsed[0]["after_path"] == "b/x/x@1.0.1"

    # A tarball that tries to escape its directory must write nothing outside it.
    hostile = scratch / "hostile.tgz"
    member = tarfile.TarInfo("../escaped.txt")
    member.size = 2
    with tarfile.open(hostile, "w:gz") as archive:
        archive.addfile(member, io.BytesIO(b"no"))
    target = scratch / "unpacked"
    unpack(hostile.as_uri(), target)
    assert not (scratch / "escaped.txt").exists(), "tarball escaped its target directory"

    # draw_typical stops at the quota and follows the hash order, not input order.
    real = {name: globals()[name] for name in ("package_doc", "unpack")}
    globals()["package_doc"] = lambda *_, **__: {
        "versions": {v: {"dist": {"tarball": "stub"}} for v in ("1.0.0", "1.0.1")}}
    globals()["unpack"] = lambda *_, **__: None
    candidates = [{"name": n, "before": "1.0.0", "after": "1.0.1",
                   "before_path": f"b/{n}/{n}@1.0.0", "after_path": f"b/{n}/{n}@1.0.1"}
                  for n in ("p1", "p2", "p3", "p4")]
    taken, _ = draw_typical(candidates, 2, scratch, skip_advisory=False, log=lambda _: None)
    expected = [e["name"] for e in hash_order(candidates,
                                              key=lambda e: (e["name"], e["after"]))][:2]
    assert [e["name"] for e in taken] == expected, [e["name"] for e in taken]
    globals().update(real)

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
