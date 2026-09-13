"""Capability extractor, methodology.md §4.3.

    python pipeline/capability.py --before DIR --after DIR
    python pipeline/capability.py --single DIR
    python pipeline/capability.py --selfcheck

Emits the capability delta that keys retrieval (§5.2). The delta is never shown
to the model (D25); it only selects which knowledge-base cards a configuration
sees.

Runs on RAW files, before the minify/unminify of §4.2 (D29): those transforms
rename identifiers and can erase the obfuscation patterns this looks for.

Detection is text pattern matching, not parsing. That is what §4.3 specifies,
and it keeps the extractor readable enough to audit against the table there.
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


# read_text returns a file's contents, or None when it is not UTF-8 text.
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


# source_texts yields the contents of every file the extractor scans.
def source_texts(root):
    root = Path(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix not in SOURCE_SUFFIXES and path.name != "package.json":
            continue
        text = read_text(path)
        if text is not None:
            yield text


# imported_modules returns the module specifiers a source file requires or imports.
def imported_modules(text):
    names = set()
    for match in MODULE_REF.finditer(text):
        name = next(group for group in match.groups() if group is not None)
        names.add(name[5:] if name.startswith("node:") else name)
    return names


# long_encoded_literal reports whether a string literal looks like packed data.
def long_encoded_literal(text):
    for match in STRING_LITERAL.finditer(text):
        value = next((group for group in match.groups() if group is not None), "")
        if len(value) >= 200 and (BASE64_ONLY.match(value) or HEX_ONLY.match(value)):
            return True
    return False


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


# install_commands returns the lifecycle hooks a manifest defines.
def install_commands(root):
    scripts = package_json(root).get("scripts")
    if not isinstance(scripts, dict):
        return {}
    return {hook: scripts[hook] for hook in INSTALL_HOOKS if hook in scripts}


# declared_dependencies flattens every dependency field into one name-to-spec map.
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


# scan_version returns the capabilities detected in one version of a package.
def scan_version(root):
    found = set()
    if install_commands(root):
        found.add("install_script")

    for text in source_texts(root):
        modules = imported_modules(text)
        if modules & NETWORK_MODULES or NETWORK_CALLS.search(text):
            found.add("network")
        if "child_process" in modules:
            found.add("process_exec")
        if HOST_INFO.search(text):
            found.add("host_info")
        if any(marker in text for marker in FS_SENSITIVE_MARKERS):
            found.add("fs_sensitive")
        if BROWSER_DATA.search(text):
            found.add("browser_data")
        if DYNAMIC_CODE.search(text):
            found.add("dynamic_code")
        if HEX_IDENTIFIER.search(text) or DECODE_CALL.search(text) or long_encoded_literal(text):
            found.add("obfuscation")

    return found


# capabilities lists one version's capabilities in table order.
def capabilities(root):
    # For malicious-intent cards, which have no benign predecessor: their delta
    # is the whole capability set (§4.3).
    found = scan_version(root)
    return [name for name in CAPABILITIES if name in found]


# dependency_change reports a new dependency or one repointed off the registry.
def dependency_change(before, after):
    old, new = declared_dependencies(before), declared_dependencies(after)
    for name, spec in new.items():
        if name not in old:
            return True
        if spec != old[name] and is_non_registry(spec):
            return True
    return False


# large_deletion reports whether at least half the previous text files are gone.
def large_deletion(before, after):
    old = text_files(before)
    if not old:
        return False
    removed = old - text_files(after)
    return len(removed) * 2 >= len(old)


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


# main prints the delta for a version pair, or one version's capabilities.
def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--before")
    parser.add_argument("--after")
    parser.add_argument("--single", help="one version, for a malicious-intent card")
    args = parser.parse_args(argv)

    if args.single:
        print(json.dumps(capabilities(args.single)))
    elif args.before and args.after:
        print(json.dumps(delta(args.before, args.after)))
    else:
        parser.error("pass --single, or both --before and --after")


# build_fixture writes a package tree and returns its root, for the self-check.
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


# selfcheck asserts the detection rules of §4.3 against small fixtures.
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

    print("ok")


if __name__ == "__main__":
    if "--selfcheck" in sys.argv:
        selfcheck()
    else:
        main()
