"""Capability delta between two package versions, and the evidence behind it."""
import argparse
import json

from pipeline.features.files import source_files, text_files
from pipeline.features.manifest import declared_dependencies, install_commands, is_non_registry
from pipeline.features.signals import CAPABILITIES, line_number, scan_text
from pipeline.shared.isolation import require_offline

MAX_EVIDENCE = 3


def scan_version(root):
    found = {signal for _, text in source_files(root) for signal, _, _ in scan_text(text)}
    if install_commands(root):
        found.add("install_script")
    return found


# explain_version maps each signal to at most MAX_EVIDENCE (file, line, match) entries.
def explain_version(root):
    evidence = {}
    for path, text in source_files(root):
        for signal, matched, offset in scan_text(text):
            entries = evidence.setdefault(signal, [])
            if len(entries) < MAX_EVIDENCE:
                entries.append({"file": path, "line": line_number(text, offset),
                                "match": matched.strip()[:120]})
    for hook, command in install_commands(root).items():
        entries = evidence.setdefault("install_script", [])
        if len(entries) < MAX_EVIDENCE:
            entries.append({"file": "package.json", "hook": hook, "match": str(command)[:120]})
    return evidence


# capabilities lists one version's capabilities in table order, for a package with no predecessor.
def capabilities(root):
    found = scan_version(root)
    return [name for name in CAPABILITIES if name in found]


# dependency_changes lists each new dependency and each one repointed off the registry.
def dependency_changes(before, after):
    old, new = declared_dependencies(before), declared_dependencies(after)
    found = []
    for name, spec in new.items():
        if name not in old:
            found.append({"dependency": name, "before": None, "after": spec})
        elif spec != old[name] and is_non_registry(spec):
            found.append({"dependency": name, "before": old[name], "after": spec})
    return found


# deletion_counts returns how many of the previous text files are gone, and of how many.
def deletion_counts(before, after):
    old = text_files(before)
    return len(old - text_files(after)), len(old)


def large_deletion(before, after):
    removed, total = deletion_counts(before, after)
    return total > 0 and removed * 2 >= total


# delta lists the capabilities new in `after`, in table order, then the change signals.
def delta(before, after):
    old, new = scan_version(before), scan_version(after)
    signals = {name for name in CAPABILITIES if name in new and name not in old}
    # A surviving hook whose command changed counts too, which a set difference would miss.
    if install_commands(before) != install_commands(after) and install_commands(after):
        signals.add("install_script")
    ordered = [name for name in CAPABILITIES if name in signals]
    if dependency_changes(before, after):
        ordered.append("dependency_change")
    if large_deletion(before, after):
        ordered.append("large_deletion")
    return ordered


# delta_evidence explains each delta signal from the new version, where it first appears.
def delta_evidence(before, after):
    signals = delta(before, after)
    from_after = explain_version(after)
    evidence = {name: from_after.get(name, []) for name in signals if name in CAPABILITIES}
    if "dependency_change" in signals:
        evidence["dependency_change"] = dependency_changes(before, after)[:MAX_EVIDENCE]
    if "large_deletion" in signals:
        removed, total = deletion_counts(before, after)
        evidence["large_deletion"] = [{"removed": removed, "of": total}]
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(prog="capability")
    parser.add_argument("--before")
    parser.add_argument("--after")
    parser.add_argument("--single", help="one version, for a package with no predecessor")
    parser.add_argument("--explain", action="store_true", help="also report where each signal fires")
    args = parser.parse_args(argv)
    require_offline()
    if args.single:
        result = explain_version(args.single) if args.explain else capabilities(args.single)
    elif args.before and args.after:
        result = (delta_evidence if args.explain else delta)(args.before, args.after)
    else:
        parser.error("pass --single, or both --before and --after")
    print(json.dumps(result, indent=2 if args.explain else None))
