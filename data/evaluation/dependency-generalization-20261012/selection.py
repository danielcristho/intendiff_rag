"""Select archived dependency context without consulting model predictions."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def rank(identity):
    return hashlib.sha256(('D89|' + identity).encode()).hexdigest()


def precedes(dependency_time, target_time):
    return bool(dependency_time and target_time and
                datetime.fromisoformat(dependency_time.replace('Z', '+00:00')) <=
                datetime.fromisoformat(target_time.replace('Z', '+00:00')))


def safe_file(root, name):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError('Missing or escaping source file: ' + name)
    return path


def export_entry(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ('.', 'require', 'default', 'import', 'node'):
            if key in value:
                found = export_entry(value[key])
                if found:
                    return found
    return None


def source_files(root):
    manifest = json.loads(safe_file(root, 'package.json').read_text())
    entry = manifest.get('main') or export_entry(manifest.get('exports')) or 'index.js'
    files = {'package.json', entry.removeprefix('./')}
    for hook in ('preinstall', 'install', 'postinstall'):
        command = manifest.get('scripts', {}).get(hook)
        if command:
            # Complex shell pipelines need a separate static dependency resolver.
            match = re.fullmatch(r'node\s+(?:--[\w=-]+\s+)*([\w./-]+\.(?:js|cjs|mjs))(?:\s+--[\w=-]+)*', command)
            if not match:
                raise ValueError('Unsupported lifecycle command: ' + hook)
            files.add(match[1].removeprefix('./'))
    result = {}
    for name in sorted(files):
        path = safe_file(root, name)
        if path.stat().st_size > 200000:
            raise ValueError('Source file exceeds 200000 bytes')
        result[name] = path.read_bytes().decode('utf-8')
    return result


def select_distinct(candidates):
    selected, dependencies, names = [], set(), set()
    for candidate in sorted(candidates, key=lambda c: (rank(c['snapshot']['name']), rank(c['pair']['id']))):
        dependency, name = candidate['snapshot']['name'], candidate['pair']['name']
        if dependency in dependencies or name in names:
            continue
        selected.append(candidate)
        dependencies.add(dependency)
        names.add(name)
    return selected
