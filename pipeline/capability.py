"""Capability extractor.

    python pipeline/capability.py --before DIR --after DIR [--explain]
    python pipeline/capability.py --single DIR
    python pipeline/capability.py --selfcheck
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Table order from §4.3, preserved because §3.4 fills the knowledge base by
# round-robin over these capabilities in exactly this order.
CAPABILITIES = [
    "network",
    "process_exec",
    "host_info",
    "fs_sensitive",
    "browser_data",
    "dynamic_code",
    "obfuscation",
    "install_script",
]
CHANGE_SIGNALS = ["dependency_change", "large_deletion"]

SOURCE_SUFFIXES = {".js", ".ts", ".ejs", ".mjs", ".cjs"}
DEPENDENCY_FIELDS = ("dependencies", "optionalDependencies", "peerDependencies")
INSTALL_HOOKS = ("preinstall", "install", "postinstall")
MAX_EVIDENCE = 3

NETWORK_MODULES = {"http", "https", "net", "dgram", "tls", "dns"}
NETWORK_CALLS = re.compile(r"\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\s*\(|\bnavigator\.sendBeacon\s*\(")

# process.env read whole. A named read (process.env.FOO, process.env["FOO"]) is
# routine configuration and does not count (D28).
HOST_INFO = re.compile(
    r"""process\.env(?!\s*(?:\.\w|\[\s*['"]))|\bos\.(?:userInfo|hostname|homedir|networkInterfaces)\s*\("""
)
FS_SENSITIVE_MARKERS = (
    ".ssh", "id_rsa", "authorized_keys", ".npmrc", ".aws",
    ".git-credentials", ".bash_history", "/etc/passwd", "Login Data", "Local Storage",
)
BROWSER_DATA = re.compile(
    r"""document\.cookie|document\.forms|\blocalStorage\b|\bsessionStorage\b"""
    r"""|type\s*=\s*["']?password["']?|addEventListener\s*\(\s*["']submit["']"""
)
DYNAMIC_CODE = re.compile(
    r"""\beval\s*\(|\bnew\s+Function\s*\(|\bvm\.runIn(?:ThisContext|NewContext|Context)\s*\(|\bnew\s+vm\.Script\s*\("""
)
HEX_IDENTIFIER = re.compile(r"_0x[0-9a-f]{4,}")
DECODE_CALL = re.compile(r"""Buffer\.from\s*\([^\n;]*?["'](?:base64|hex)["']|\batob\s*\(""")

MODULE_REF = re.compile(
    r"""require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|\bfrom\s+['"]([^'"]+)['"]"""
    r"""|\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|\bimport\s+['"]([^'"]+)['"]"""
)
STRING_LITERAL = re.compile(r"""(?<!\\)(?:"([^"\n]*)"|'([^'\n]*)'|`([^`]*)`)""")
BASE64_ONLY = re.compile(r"^[A-Za-z0-9+/=]+$")
HEX_ONLY = re.compile(r"^[0-9a-fA-F]+$")
NON_REGISTRY_PREFIX = ("git+", "git:", "http:", "https:", "file:", "github:")
USER_REPO = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(?:#.+)?$")


# None means the file is not UTF-8 text, which callers treat as binary.
def read_text(path):
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


# text_files returns every UTF-8 readable file, as paths relative to the root.
def text_files(root):
    # §4.3 leaves "text file" undefined; decoding is the closest deterministic
    # reading of it, and it is what large_deletion counts over.
    root = Path(root)
    found = set()
    for path in sorted(root.rglob("*")):
        if path.is_file() and read_text(path) is not None:
            found.add(str(path.relative_to(root)))
    return found


def source_files(root):
    root = Path(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in SOURCE_SUFFIXES and path.name != "package.json":
            continue
        text = read_text(path)
        if text is not None:
            yield str(path.relative_to(root)), text


def imported_modules(text):
    for match in MODULE_REF.finditer(text):
        name = next(group for group in match.groups() if group is not None)
        yield (name[5:] if name.startswith("node:") else name), match


# encoded_literals yields string literals long enough to look like packed data.
def encoded_literals(text):
    for match in STRING_LITERAL.finditer(text):
        value = next((group for group in match.groups() if group is not None), "")
        if len(value) >= 200 and (BASE64_ONLY.match(value) or HEX_ONLY.match(value)):
            yield match


# scan_text yields every (signal, matched text, offset) found in one file.
def scan_text(text):
    # scan_version and explain_version both build on this, so the §4.3 table's
    # detection rules exist in exactly one place.
    for name, match in imported_modules(text):
        if name in NETWORK_MODULES:
            yield "network", match.group(0), match.start()
        elif name == "child_process":
            yield "process_exec", match.group(0), match.start()

    for signal, pattern in (
        ("network", NETWORK_CALLS),
        ("host_info", HOST_INFO),
        ("browser_data", BROWSER_DATA),
        ("dynamic_code", DYNAMIC_CODE),
        ("obfuscation", HEX_IDENTIFIER),
        ("obfuscation", DECODE_CALL),
    ):
        for match in pattern.finditer(text):
            yield signal, match.group(0), match.start()

    for marker in FS_SENSITIVE_MARKERS:
        offset = text.find(marker)
        if offset >= 0:
            yield "fs_sensitive", marker, offset

    for match in encoded_literals(text):
        yield "obfuscation", match.group(0)[:60] + "…", match.start()


# 1-based, to match what an editor shows.
def line_number(text, offset):
    return text.count("\n", 0, offset) + 1


# package_root resolves the directory an npm tarball unpacks its manifest into.
def package_root(version_dir):
    version_dir = Path(version_dir)
    # 60 of the 92 replication samples keep the tarball's own "package/" wrapper
    # and 31 do not. Read through it, or the manifest is invisible and both the
    # intent profile and every manifest-derived signal come out empty.
    inner = version_dir / "package"
    if not (version_dir / "package.json").exists() and (inner / "package.json").exists():
        return inner
    return version_dir


# has_content reports whether a version directory holds any file at all.
def has_content(version_dir):
    return any(path.is_file() for path in Path(version_dir).rglob("*"))


# package_json returns a version's parsed manifest, empty when absent or invalid.
def package_json(root):
    text = read_text(Path(root) / "package.json")
    if text is None:
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def install_commands(root):
    scripts = package_json(root).get("scripts")
    if not isinstance(scripts, dict):
        return {}
    return {hook: scripts[hook] for hook in INSTALL_HOOKS if hook in scripts}


# Flattens dependencies, optionalDependencies and peerDependencies together.
def declared_dependencies(root):
    manifest = package_json(root)
    merged = {}
    for field in DEPENDENCY_FIELDS:
        entries = manifest.get(field)
        if isinstance(entries, dict):
            merged.update(entries)
    return merged


# is_non_registry reports whether a dependency spec points outside the registry.
def is_non_registry(spec):
    if not isinstance(spec, str):
        return False
    spec = spec.strip()
    return spec.startswith(NON_REGISTRY_PREFIX) or bool(USER_REPO.match(spec))


def scan_version(root):
    found = {signal for _, text in source_files(root) for signal, _, _ in scan_text(text)}
    if install_commands(root):
        found.add("install_script")
    return found


def explain_version(root):
    # At most MAX_EVIDENCE per signal: enough for an annotator to judge the
    # documented purpose behind it (§3.3) without bloating pairs.jsonl.
    evidence = {}
    for path, text in source_files(root):
        for signal, matched, offset in scan_text(text):
            entries = evidence.setdefault(signal, [])
            if len(entries) < MAX_EVIDENCE:
                entries.append({
                    "file": path,
                    "line": line_number(text, offset),
                    "match": matched.strip()[:120],
                })
    for hook, command in install_commands(root).items():
        entries = evidence.setdefault("install_script", [])
        if len(entries) < MAX_EVIDENCE:
            entries.append({"file": "package.json", "hook": hook, "match": str(command)[:120]})
    return evidence


# capabilities lists one version's capabilities in table order.
def capabilities(root):
    # For malicious-intent cards, which have no benign predecessor: their delta
    # is the whole capability set (§4.3).
    found = scan_version(root)
    return [name for name in CAPABILITIES if name in found]


# dependency_changes lists each new dependency or one repointed off the registry.
def dependency_changes(before, after):
    old, new = declared_dependencies(before), declared_dependencies(after)
    found = []
    for name, spec in new.items():
        if name not in old:
            found.append({"dependency": name, "before": None, "after": spec})
        elif spec != old[name] and is_non_registry(spec):
            found.append({"dependency": name, "before": old[name], "after": spec})
    return found


# dependency_change reports whether any dependency was added or repointed.
def dependency_change(before, after):
    return bool(dependency_changes(before, after))


# deletion_counts returns how many of the previous text files are gone, and of how many.
def deletion_counts(before, after):
    old = text_files(before)
    return len(old - text_files(after)), len(old)


# large_deletion reports whether at least half the previous text files are gone.
def large_deletion(before, after):
    removed, total = deletion_counts(before, after)
    return total > 0 and removed * 2 >= total


# delta returns the capability delta between two versions, in table order.
def delta(before, after):
    old, new = scan_version(before), scan_version(after)
    signals = {name for name in CAPABILITIES if name in new and name not in old}

    # install_script also enters the delta when the hook survives but its command
    # changed, which a plain set difference would miss (§4.3).
    if install_commands(before) != install_commands(after) and install_commands(after):
        signals.add("install_script")

    ordered = [name for name in CAPABILITIES if name in signals]
    if dependency_change(before, after):
        ordered.append("dependency_change")
    if large_deletion(before, after):
        ordered.append("large_deletion")
    return ordered


# delta_evidence maps each signal in the delta to why it fired.
def delta_evidence(before, after):
    # Evidence comes from the new version only: a signal in the delta was by
    # definition absent before, so v_t is where the annotator has to look.
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--before")
    parser.add_argument("--after")
    parser.add_argument("--single", help="one version, for a malicious-intent card")
    parser.add_argument("--explain", action="store_true", help="also report where each signal fires")
    args = parser.parse_args(argv)

    if args.single:
        result = explain_version(args.single) if args.explain else capabilities(args.single)
    elif args.before and args.after:
        result = (
            delta_evidence(args.before, args.after)
            if args.explain
            else delta(args.before, args.after)
        )
    else:
        parser.error("pass --single, or both --before and --after")
    print(json.dumps(result, indent=2 if args.explain else None))


def build_fixture(root, files):
    root = Path(root)
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")
    return root


def selfcheck():
    import tempfile

    tmp = Path(tempfile.mkdtemp())
    n = [0]

    def pkg(files):
        n[0] += 1
        return build_fixture(tmp / f"v{n[0]}", files)

    # --- network: modules, node: prefix, and browser-style calls
    assert "network" in scan_version(pkg({"a.js": "const h = require('https');"}))
    assert "network" in scan_version(pkg({"a.js": "import dns from 'node:dns';"}))
    assert "network" in scan_version(pkg({"a.js": "await fetch(url);"}))
    assert "network" in scan_version(pkg({"a.js": "navigator.sendBeacon(u, d);"}))
    assert "network" not in scan_version(pkg({"a.js": "const p = require('path');"}))

    assert "process_exec" in scan_version(pkg({"a.js": "const {exec} = require('child_process');"}))

    # --- host_info: whole-environment reads count, named reads do not (D28)
    assert "host_info" in scan_version(pkg({"a.js": "send(JSON.stringify(process.env));"}))
    assert "host_info" in scan_version(pkg({"a.js": "os.hostname();"}))
    assert "host_info" not in scan_version(pkg({"a.js": "if (process.env.NODE_ENV) {}"}))
    assert "host_info" not in scan_version(pkg({"a.js": 'const k = process.env["API_KEY"];'}))

    assert "fs_sensitive" in scan_version(pkg({"a.js": "read('~/.ssh/id_rsa');"}))
    assert "browser_data" in scan_version(pkg({"a.js": "const c = document.cookie;"}))
    assert "browser_data" in scan_version(pkg({"a.js": 'el.addEventListener("submit", f);'}))
    assert "dynamic_code" in scan_version(pkg({"a.js": "eval(payload);"}))
    assert "dynamic_code" in scan_version(pkg({"a.js": "new Function('return 1')();"}))

    # --- obfuscation: identifiers, decode calls, and packed literals
    assert "obfuscation" in scan_version(pkg({"a.js": "var _0x4f2a = 1;"}))
    assert "obfuscation" in scan_version(pkg({"a.js": "Buffer.from(s, 'base64');"}))
    assert "obfuscation" in scan_version(pkg({"a.js": "atob(s);"}))
    packed = "A" * 200
    assert "obfuscation" in scan_version(pkg({"a.js": f'var s = "{packed}";'}))
    # Just under the 200-character threshold must not trigger.
    assert "obfuscation" not in scan_version(pkg({"a.js": 'var s = "' + "A" * 199 + '";'}))
    # Prose of the same length is neither base64 nor hex.
    assert "obfuscation" not in scan_version(pkg({"a.js": 'var s = "' + "hello world " * 30 + '";'}))

    assert "install_script" in scan_version(
        pkg({"package.json": '{"scripts": {"postinstall": "node s.js"}}'})
    )
    assert "install_script" not in scan_version(
        pkg({"package.json": '{"scripts": {"test": "jest"}}'})
    )

    # --- binary files must not crash the scan
    assert scan_version(pkg({"logo.png": b"\x89PNG\r\n\x1a\n\x00\xff", "a.js": "x=1;"})) == set()

    # --- delta: only newly appearing capabilities, in table order
    before = pkg({"a.js": "const h = require('https');", "package.json": "{}"})
    after = pkg({
        "a.js": "const h = require('https');\nconst {exec} = require('child_process');\neval(x);",
        "package.json": "{}",
    })
    assert delta(before, after) == ["process_exec", "dynamic_code"], delta(before, after)

    # A capability already present before is not part of the delta.
    assert "network" not in delta(before, after)

    # --- install_script enters the delta when the hook's command changes
    b = pkg({"package.json": '{"scripts": {"postinstall": "node build.js"}}'})
    a = pkg({"package.json": '{"scripts": {"postinstall": "node evil.js"}}'})
    assert delta(b, a) == ["install_script"], delta(b, a)
    same = pkg({"package.json": '{"scripts": {"postinstall": "node build.js"}}'})
    assert delta(b, same) == [], delta(b, same)

    # --- dependency_change: a new name, or a spec repointed off the registry
    b = pkg({"package.json": '{"dependencies": {"axios": "^1.0.0"}}'})
    assert delta(b, pkg({"package.json": '{"dependencies": {"axios": "^1.0.0", "x": "^1.0.0"}}'})) \
        == ["dependency_change"]
    assert delta(b, pkg({"package.json": '{"dependencies": {"axios": "git+https://e.com/a.git"}}'})) \
        == ["dependency_change"]
    assert delta(b, pkg({"package.json": '{"dependencies": {"axios": "user/repo"}}'})) \
        == ["dependency_change"]
    # A plain version bump stays on the registry and is not a change signal.
    assert delta(b, pkg({"package.json": '{"dependencies": {"axios": "^2.0.0"}}'})) == []

    # --- large_deletion: at least half the previous text files gone
    four = pkg({"a.js": "1", "b.js": "1", "c.js": "1", "d.js": "1"})
    assert delta(four, pkg({"a.js": "1", "b.js": "1"})) == ["large_deletion"]
    assert delta(four, pkg({"a.js": "1", "b.js": "1", "c.js": "1"})) == []

    # --- capabilities(): whole set for a card with no predecessor
    card = pkg({"a.js": "require('https'); eval(x);", "package.json": '{"scripts": {"install": "s"}}'})
    assert capabilities(card) == ["network", "dynamic_code", "install_script"], capabilities(card)

    # --- explain: file, line and the matched text, for §3.3 verification
    b = pkg({"index.js": "module.exports = s => s.trim();", "package.json": "{}"})
    a = pkg({
        "index.js": "module.exports = s => s.trim();",
        "scripts/setup.js": "const https = require('https');\nconst env = JSON.stringify(process.env);\n",
        "package.json": '{"scripts": {"preinstall": "node ./scripts/setup.js"}}',
    })
    why = delta_evidence(b, a)
    assert set(why) == {"network", "host_info", "install_script"}, set(why)
    assert why["network"][0]["file"] == "scripts/setup.js", why["network"]
    assert why["network"][0]["line"] == 1, why["network"]
    assert "https" in why["network"][0]["match"], why["network"]
    # process.env sits on the second line, so the line number must follow it.
    assert why["host_info"][0]["line"] == 2, why["host_info"]
    assert why["install_script"][0]["hook"] == "preinstall", why["install_script"]

    # Evidence covers only what is in the delta: a capability present in both
    # versions is not something the annotator has to re-judge.
    both = pkg({"a.js": "require('https');"})
    grew = pkg({"a.js": "require('https'); eval(x);"})
    assert set(delta_evidence(both, grew)) == {"dynamic_code"}, delta_evidence(both, grew)

    # --- change-signal evidence names the dependency and the counts
    b = pkg({"package.json": '{"dependencies": {"axios": "^1.0.0"}}'})
    a = pkg({"package.json": '{"dependencies": {"axios": "git+https://e.com/a.git"}}'})
    dep = delta_evidence(b, a)["dependency_change"][0]
    assert dep["dependency"] == "axios" and dep["before"] == "^1.0.0", dep

    four = pkg({"a.js": "1", "b.js": "1", "c.js": "1", "d.js": "1"})
    gone = delta_evidence(four, pkg({"a.js": "1"}))["large_deletion"][0]
    assert gone == {"removed": 3, "of": 4}, gone

    # At most MAX_EVIDENCE entries per signal, so pairs.jsonl stays small.
    noisy = pkg({"a.js": "\n".join("eval(x);" for _ in range(10))})
    assert len(explain_version(noisy)["dynamic_code"]) == MAX_EVIDENCE

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
