"""Read-only reanalysis of the four historical baseline experiments."""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FOLDERS = ['source-baselines-20260929', 'output-budget-20260929',
           'model-scale-20260930', 'model-families-20261001']
sys.path.insert(0, str(ROOT / 'data/evaluation/model-families-20261001'))
from prompts import build


def read(path):
    return [json.loads(line) for line in path.open()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def parse(raw):
    try:
        value, _ = json.JSONDecoder().raw_decode(raw[raw.index('{'):])
        if not isinstance(value, dict) or not isinstance(value.get('verdict'), str):
            return None
        verdict = value['verdict'].strip().lower()
        if verdict not in ('malicious', 'benign') or not isinstance(value.get('reason'), str):
            return None
        evidence = value.get('evidence')
        if not isinstance(evidence, list) or not all(isinstance(x, str) for x in evidence):
            return None
        return {'verdict': verdict, 'reason': value['reason'], 'evidence': evidence}
    except (ValueError, TypeError):
        return None


def metrics(rows, pairs):
    result = {}
    for subset in ('MAL', 'TYP'):
        selected = [r for r in rows if pairs[r['pair_id']]['subset'] == subset]
        positive = sum(r['json_valid'] and r['verdict'] == 'malicious' for r in selected)
        invalid = sum(not r['json_valid'] for r in selected)
        result[subset] = {'n': len(selected), 'positive': positive, 'invalid': invalid,
                          'rate': positive / len(selected),
                          'invalid_as_malicious_rate': (positive + invalid) / len(selected),
                          'valid_only_rate': positive / (len(selected) - invalid)}
    campaigns = defaultdict(list)
    for r in rows:
        if pairs[r['pair_id']]['subset'] == 'MAL':
            campaigns[pairs[r['pair_id']]['campaign']].append(r)
    result['macro_campaign_recall'] = sum(sum(r['json_valid'] and r['verdict'] == 'malicious'
        for r in rs) / len(rs) for rs in campaigns.values()) / len(campaigns)
    valid = [r for r in rows if r['json_valid']]
    result['valid'] = len(valid)
    result['length'] = sum(r['finish_reason'] == 'length' for r in rows)
    result['placeholder_evidence_valid'] = sum(any('up to 3 lines copied exactly from the smart-diff' in e
                                                for e in r['evidence']) for r in valid)
    result['nonverbatim_full_line_valid'] = sum(any(e not in pairs[r['pair_id']]['diff'].splitlines()
                                                   for e in r['evidence']) for r in valid)
    return result


reports, all_rows = [], []
for folder in FOLDERS:
    here = ROOT / 'data/evaluation' / folder
    protocol = json.loads((here / 'protocol.json').read_text())
    summary = json.loads((here / 'summary.json').read_text())
    pairs = {p['id']: p for p in read(here / 'pairs.jsonl')}
    rows = read(here / 'results.jsonl')
    options = {m['id']: m for m in protocol['models']}
    token_path = here / 'context-audit.jsonl'
    token_audit = {(r['model'], r['config'], r['pair_id']): r['prompt_tokens']
                   for r in read(token_path)} if token_path.exists() else {}
    for model in protocol['models']:
        individual = read(here / f"{model['tag']}.results.jsonl")
        assert len(individual) == len({r['run_key'] for r in individual}) == 1946
        assert {r['run_key']: r for r in individual} == {
            r['run_key']: r for r in rows if r['model'] == model['id']}
    assert len(pairs) == 973 and len(rows) == len({r['run_key'] for r in rows}) == 3892
    assert Counter(p['subset'] for p in pairs.values()) == {'MAL': 873, 'TYP': 100}
    for pair in pairs.values():
        assert hashlib.sha256(pair['diff'].encode()).hexdigest() == pair['diff_sha256']
        assert pair['human_annotation_verified'] is False
        assert pair.get('intent_from', pair['before']) == pair['before']
    hash_checks = []
    for section in ('source_sha256', 'baseline_sha256'):
        for name, expected in protocol.get(section, {}).items():
            verified_path = ROOT / name
            actual = digest(verified_path)
            if actual != expected and name == 'data/evaluation/output-budget-20260929/qwen25.results.jsonl':
                verified_path = OUT / 'qwen25.results.before-restoration.jsonl'
                actual = digest(verified_path)
            hash_checks.append({'section': section, 'path': name, 'match': actual == expected,
                                'verified_path': str(verified_path.relative_to(ROOT))})
            assert actual == expected, name
    groups = []
    for group in summary['groups']:
        selected = [r for r in rows if (r['model'], r['config']) == (group['model'], group['config'])]
        assert len(selected) == 973 and {r['pair_id'] for r in selected} == pairs.keys()
        for row in selected:
            p = pairs[row['pair_id']]
            parsed = parse(row['raw'])
            assert (parsed is not None and row['finish_reason'] != 'length') == row['json_valid']
            if parsed:
                assert all(row[k] == parsed[k] for k in ('verdict', 'reason', 'evidence'))
            assert row['label'] == p['label'] and row['diff_sha256'] == p['diff_sha256']
            assert row['human_annotation_verified'] is False and not row.get('error') and row['cards'] == []
            assert all(row[k] == protocol[k] for k in ('seed', 'temperature', 'top_p'))
            if 'max_tokens' in row:
                assert row['max_tokens'] == protocol['max_tokens']
            else:
                assert folder == FOLDERS[0] and protocol['max_tokens'] == 512
                assert '"max_tokens": 512' in (here / 'runner.py').read_text()
            assert 0 < row['completion_tokens'] <= protocol['max_tokens']
            assert 0 < row['prompt_tokens'] <= protocol['max_model_len'] - protocol['max_tokens']
            if token_audit:
                assert row['prompt_tokens'] == token_audit[row['model'], row['config'], row['pair_id']]
            if 'stop_token_ids' in options[row['model']]:
                assert row['stop_token_ids'] == options[row['model']]['stop_token_ids']
                assert row['response_model'] == row['model']
            messages = build(row['config'], p)
            poisoned = dict(p, label='AUDIT_SENTINEL', source_label='AUDIT_SENTINEL',
                            campaign='AUDIT_SENTINEL', pred='AUDIT_SENTINEL', source='AUDIT_SENTINEL')
            assert messages == build(row['config'], poisoned)
            if 'prompt_messages_sha256' in row:
                assert hashlib.sha256(json.dumps(messages).encode()).hexdigest() == row['prompt_messages_sha256']
        counted = metrics(selected, pairs)
        assert counted['valid'] == group['json_valid'] and counted['length'] == group['length_limited']
        for subset, metric in [('MAL', 'mal_source_recall_proxy'), ('TYP', 'typ_assumed_benign_fpr')]:
            assert all(counted[subset][key] == group[metric][key] for key in ('n', 'positive', 'rate'))
        assert abs(counted['macro_campaign_recall'] - group['mal_campaign_macro_recall_proxy']) < 1e-12
        groups.append({'model': group['model'], 'config': group['config'], **counted})
    logs = {}
    for model in protocol['models']:
        log = (here / f"{model['tag']}.server.log").read_text()
        statuses = Counter(re.findall(r'POST /v1/chat/completions HTTP/1\.1" (\d+)', log))
        assert statuses == {'200': 1946}, (folder, statuses)
        logs[model['tag']] = dict(statuses)
    reports.append({'experiment': folder, 'runs': len(rows), 'groups': groups,
                    'frozen_hash_checks': hash_checks, 'generation_http_statuses': logs})
    if protocol['max_tokens'] == 2048:
        all_rows.extend(rows)
combined = read(ROOT / 'data/evaluation/model-families-20261001/results.all-models.jsonl')
assert {r['run_key']: r for r in combined} == {r['run_key']: r for r in all_rows}
campaigns = Counter(p['campaign'] for p in pairs.values() if p['subset'] == 'MAL')
report = {'passed': True, 'historical_generations': 15568, 'experiments': reports,
          'combined_2048_rows_exact_match': len(combined), 'human_gold_verified': False,
          'campaign_count': len(campaigns), 'largest_campaign': campaigns.most_common(1),
          'truncated_by_subset': dict(Counter(p['subset'] for p in pairs.values() if p['truncated'])),
          'limitations': ['Metadata-injection check excludes source fields only, not memorization or package identity in code.',
                          'D81 has no per-row max_tokens; 512 is pinned in its runner and protocol.',
                          'Nonverbatim full-line evidence includes substrings, not necessarily hallucinations.',
                          'Valid-only rates condition on output validity and are not primary metrics.']}
(OUT / 'baseline-audit.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: v for k, v in report.items() if k != 'experiments'}, indent=2))
