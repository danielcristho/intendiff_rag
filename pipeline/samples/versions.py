"""Semantic version order and the previous-version rule for release pairs."""

RECENT_RELEASES = 20


# parse_semver returns a sortable key where a prerelease sorts below its release.
def parse_semver(version):
    core, _, prerelease = str(version).partition("-")
    numbers = []
    for part in core.split(".")[:3]:
        digits = "".join(ch for ch in part if ch.isdigit())
        numbers.append(int(digits) if digits else 0)
    while len(numbers) < 3:
        numbers.append(0)
    return (*numbers, 0 if prerelease else 1, prerelease)


# previous_version is the highest lower version published before the target, or None.
def previous_version(doc, target):
    # Publication time alone would pair across parallel release lines, e.g. 1.14.1 with 0.30.4.
    times = doc.get("time", {})
    target_time = times.get(target)
    target_key = parse_semver(target)
    candidates = [version for version in doc.get("versions", {})
                  if parse_semver(version) < target_key
                  and (target_time is None or times.get(version, "") < target_time)]
    return max(candidates, key=parse_semver) if candidates else None


# recent_pairs returns the newest releases as (before, after) pairs, oldest first.
def recent_pairs(doc, limit=RECENT_RELEASES):
    versions = sorted(doc.get("versions", {}), key=parse_semver)[-limit:]
    return [(before, version) for version in versions
            if (before := previous_version(doc, version))]
