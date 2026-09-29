"""What a version's package.json declares: install hooks and dependencies."""
import json
import re
from pathlib import Path

from pipeline.features.files import read_text

DEPENDENCY_FIELDS = ("dependencies", "optionalDependencies", "peerDependencies")
INSTALL_HOOKS = ("preinstall", "install", "postinstall")
NON_REGISTRY_PREFIX = ("git+", "git:", "http:", "https:", "file:", "github:")
USER_REPO = re.compile(r"^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(?:#.+)?$")


# package_json returns the parsed manifest, empty when absent or invalid.
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


# declared_dependencies merges every dependency field into one mapping.
def declared_dependencies(root):
    manifest, merged = package_json(root), {}
    for field in DEPENDENCY_FIELDS:
        if isinstance(manifest.get(field), dict):
            merged.update(manifest[field])
    return merged


# is_non_registry reports whether a dependency spec points outside the registry.
def is_non_registry(spec):
    if not isinstance(spec, str):
        return False
    spec = spec.strip()
    return spec.startswith(NON_REGISTRY_PREFIX) or bool(USER_REPO.match(spec))
