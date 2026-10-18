"""Build deterministic reference cards from labelled source records."""
import hashlib
import json
from pathlib import Path

import capability
from kb import fit
from label_provenance import validate


def source_text(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError('Excerpt path escapes source root')
    return path, path.read_text(encoding='utf-8')


def build(entry, count):
    problem = validate(entry)
    if problem:
        raise ValueError(problem)
    root = Path(entry.get('after_dir', entry.get('dir', '')))
    package = capability.package_json(root)
    if package.get('name') != entry['name'] or package.get('version') != entry.get('after', entry.get('version')):
        raise ValueError('Card source package identity mismatch')
    description = package.get('description', '')
    description = description if isinstance(description, str) else ''
    description = description[:4000]
    while count(description) > 64:
        description = description[:-1]
    evidence = capability.explain_version(root)
    capabilities = [c for c in capability.CAPABILITIES if c in evidence]
    locations = []
    for signal in capabilities:
        for match in evidence[signal]:
            locations.append((match['file'], match.get('line', 1)))
    if not locations:
        raise ValueError('No static capability location for reference excerpt')
    card = {key: entry[key] for key in ('name', 'campaign', 'label', 'label_provenance')}
    card.update(id='source-card-' + hashlib.sha256(entry['id'].encode()).hexdigest()[:16],
                source_id=entry['id'], source=entry.get('source', entry.get('source_url', 'dataset')),
                version=entry.get('after', entry.get('version')), delta=capabilities,
                intent=description or 'not available',
                behavior_chain='Static capability matches: ' + ', '.join(capabilities) + '.',
                rationale='Reference label supplied by the dataset protocol. The excerpt is selected automatically; no expert behavioral justification is available.',
                construction='D99_deterministic_source_excerpt_v1', human_annotation_verified=False)
    for relative, line in dict.fromkeys(locations):
        path, content = source_text(root, relative)
        lines = content.splitlines()
        start = max(0, int(line) - 2)
        candidate = dict(card, code_excerpt='\n'.join(lines[start:start + 15]))
        candidate, fits = fit(candidate, count)
        if not fits or not candidate['code_excerpt'].strip():
            continue
        candidate['excerpt_provenance'] = dict(path=str(path),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            start_line=start + 1, lines=len(candidate['code_excerpt'].splitlines()))
        candidate['description_provenance'] = dict(path=str(root / 'package.json'),
            sha256=hashlib.sha256((root / 'package.json').read_bytes()).hexdigest(),
            field='description', prefix=True)
        return candidate
    raise ValueError('No nonempty verbatim excerpt fits the card budget')


def verify(card, count):
    reason = validate(card)
    if reason:
        return reason
    try:
        source = card['excerpt_provenance']
        raw = Path(source['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source['sha256']:
            return 'excerpt_hash_mismatch'
        lines = raw.decode('utf-8').splitlines()
        start = source['start_line'] - 1
        if start < 0 or not 1 <= source['lines'] <= 15:
            return 'invalid_excerpt_range'
        if '\n'.join(lines[start:start + source['lines']]) != card['code_excerpt']:
            return 'excerpt_not_verbatim'
        description = card['description_provenance']
        raw = Path(description['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != description['sha256']:
            return 'description_hash_mismatch'
        package = json.loads(raw)
        if package.get('name') != card['name'] or package.get('version') != card['version']:
            return 'description_identity_mismatch'
        text = package.get('description') or ''
        if card['intent'] != 'not available' and not text.startswith(card['intent']):
            return 'description_not_verbatim_prefix'
        if count(card['intent']) > 64 or not fit(card, count)[1]:
            return 'card_budget_exceeded'
    except (KeyError, TypeError, ValueError, OSError):
        return 'invalid_card_provenance'
    return None
