"""Verify reference labels against pinned acquisition records."""
import hashlib
import json
from pathlib import Path


def reference(path, record, basis):
    path = Path(path)
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                record_id=record['id'], basis=basis)


def validate(row, cache=None):
    cache = {} if cache is None else cache
    provenance = row.get('label_provenance') or {}
    try:
        path, expected = provenance['path'], provenance['sha256']
        key = (path, expected)
        if key not in cache:
            raw = Path(path).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                return 'label_source_hash_mismatch'
            records = [json.loads(line) for line in raw.splitlines() if line.strip()]
            indexed = {r['id']: r for r in records}
            if len(indexed) != len(records):
                return 'duplicate_label_source_ids'
            cache[key] = indexed
        source = cache[key][provenance['record_id']]
        if source.get('name') != row.get('name') or source.get('after', source.get('version')) != row.get('after', row.get('version')):
            return 'label_source_identity_mismatch'
        basis = provenance['basis']
        if basis == 'source_malicious':
            valid = source.get('source_label') == 'malicious' or source.get('kind') in ('malicious_intent', 'compromised_lib')
            valid = valid and row.get('label') == 'malicious'
        elif basis == 'source_benign':
            valid = source.get('source_label') == 'benign' and row.get('label') == 'benign'
        elif basis == 'assumed_benign':
            checks = source.get('advisory_checks', [])
            checked = {(r.get('name'), r.get('version')) for r in checks
                       if r.get('has_advisory') is False and not r.get('error') and not r.get('advisory_ids')}
            required = {(source['name'], source.get(s)) for s in ('before', 'after')}
            valid = (source.get('assumed_label') == 'benign' and source.get('subset') == 'TYP'
                     and row.get('label') == 'benign' and required <= checked
                     and all(r.get('has_advisory') is False and not r.get('error') for r in checks))
        else:
            return 'unsupported_label_basis'
        return None if valid else 'label_not_supported_by_source'
    except (KeyError, OSError, ValueError, TypeError):
        return 'missing_or_invalid_label_provenance'
