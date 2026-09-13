"""Candidate collection for the hard-negative set, methodology.md §3.

    python pipeline/collect.py search --category 2 --size 250
    python pipeline/collect.py pairs --package husky
    python pipeline/collect.py --selfcheck

Covers path B of §3.3: search the npm registry by fixed keywords, then walk each
package's recent releases to find the earliest pair carrying that category's
signal. Path A needs the 1,900 unused Wyss typical updates and waits on the OSF
download.

Network and analysis are deliberately separate commands. §4.1 requires tarball
extraction and the capability extractor to run in a container with
`--network none`, so nothing here downloads a tarball: this produces the
candidate list, and the container step consumes it.

Selection order is the ascending SHA-256 of `name@version` throughout (§3). That
ordering does not correlate with popularity or with how easy a case is, so the
choice of candidates cannot be steered.
"""
import argparse
import hashlib
import json
import sys
import urllib.parse
import urllib.request

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


# hash_key returns the ordering key for a package version (§3).
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
    # "Highest semver below the target that was also published earlier", not
    # "previous by publication time": parallel release lines can publish within
    # moments of each other, as axios@1.14.1 and axios@0.30.4 did.
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


# fetch_json issues a GET and parses the response.
def fetch_json(url, timeout=30):
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())


# search_packages returns package names the registry matches for a keyword.
def search_packages(keyword, size=250, timeout=30):
    query = urllib.parse.urlencode({"text": keyword, "size": min(size, 250)})
    found = fetch_json(f"{REGISTRY}/-/v1/search?{query}", timeout)
    return [entry["package"]["name"] for entry in found.get("objects", [])]


# package_doc returns a package's full registry document.
def package_doc(name, timeout=30):
    return fetch_json(f"{REGISTRY}/{urllib.parse.quote(name, safe='@')}", timeout)


# tarball_url returns where one version's tarball lives.
def tarball_url(doc, version):
    return doc.get("versions", {}).get(version, {}).get("dist", {}).get("tarball")


# has_advisory reports whether OSV knows a vulnerability for that exact version.
def has_advisory(name, version, timeout=30):
    payload = json.dumps({"package": {"name": name, "ecosystem": "npm"}, "version": version})
    request = urllib.request.Request(
        OSV, data=payload.encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return bool(json.loads(response.read()).get("vulns"))


# candidates_for returns one package's update pairs as unresolved candidates.
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


# main writes candidate lists for the container step to download and scan.
def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    find = sub.add_parser("search", help="path B: registry search for one category")
    find.add_argument("--category", type=int, required=True, choices=sorted(HN_CATEGORIES))
    find.add_argument("--size", type=int, default=250)

    walk = sub.add_parser("pairs", help="list the recent update pairs of one package")
    walk.add_argument("--package", required=True)
    walk.add_argument("--limit", type=int, default=RECENT_RELEASES)

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
    else:
        doc = package_doc(args.package)
        for before, after in recent_pairs(doc, args.limit):
            print(f"{args.package}  {before} -> {after}")


# selfcheck asserts the ordering and version rules offline.
def selfcheck():
    assert parse_semver("1.2.3") > parse_semver("1.2.2")
    assert parse_semver("1.10.0") > parse_semver("1.9.0"), "numeric, not lexicographic"
    assert parse_semver("1.0.0-beta.1") < parse_semver("1.0.0"), "a prerelease sorts below release"
    assert parse_semver("2") == parse_semver("2.0.0"), "missing parts default to zero"

    # D27: axios published 1.14.1 and 0.30.4 minutes apart on parallel release
    # lines. "Previous by time" would pair 1.14.1 with 0.30.4, comparing two
    # unrelated lines; the semver rule must not.
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

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
