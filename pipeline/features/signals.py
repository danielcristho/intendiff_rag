"""Text patterns that mark a sensitive capability in one source file."""
import re

# CAPABILITIES keeps the table order; the knowledge-base selection walks it round-robin.
CAPABILITIES = ["network", "process_exec", "host_info", "fs_sensitive",
                "browser_data", "dynamic_code", "obfuscation", "install_script"]
CHANGE_SIGNALS = ["dependency_change", "large_deletion"]

NETWORK_MODULES = {"http", "https", "net", "dgram", "tls", "dns"}
NETWORK_CALLS = re.compile(r"\bfetch\s*\(|\bXMLHttpRequest\b|\bWebSocket\s*\(|\bnavigator\.sendBeacon\s*\(")
# HOST_INFO matches process.env read whole; a named read such as process.env.FOO is configuration.
HOST_INFO = re.compile(
    r"""process\.env(?!\s*(?:\.\w|\[\s*['"]))|\bos\.(?:userInfo|hostname|homedir|networkInterfaces)\s*\("""
)
FS_SENSITIVE_MARKERS = (".ssh", "id_rsa", "authorized_keys", ".npmrc", ".aws",
                        ".git-credentials", ".bash_history", "/etc/passwd", "Login Data", "Local Storage")
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
PATTERNS = (("network", NETWORK_CALLS), ("host_info", HOST_INFO), ("browser_data", BROWSER_DATA),
            ("dynamic_code", DYNAMIC_CODE), ("obfuscation", HEX_IDENTIFIER), ("obfuscation", DECODE_CALL))


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


# scan_text yields every (signal, matched text, offset) in one file; all detection rules live here.
def scan_text(text):
    for name, match in imported_modules(text):
        if name in NETWORK_MODULES:
            yield "network", match.group(0), match.start()
        elif name == "child_process":
            yield "process_exec", match.group(0), match.start()
    for signal, pattern in PATTERNS:
        for match in pattern.finditer(text):
            yield signal, match.group(0), match.start()
    for marker in FS_SENSITIVE_MARKERS:
        offset = text.find(marker)
        if offset >= 0:
            yield "fs_sensitive", marker, offset
    for match in encoded_literals(text):
        yield "obfuscation", match.group(0)[:60] + "…", match.start()


# line_number is 1-based, to match what an editor shows.
def line_number(text, offset):
    return text.count("\n", 0, offset) + 1
