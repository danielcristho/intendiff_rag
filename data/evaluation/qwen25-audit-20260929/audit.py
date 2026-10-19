"""Run offline: .venv/bin/python data/evaluation/qwen25-audit-20260929/audit.py."""
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = HERE.parent / 'source-baselines-20260929'
sys.path.insert(0, str(RUN))
from prompts import build, intent_block
from transformers import AutoTokenizer

protocol = json.loads((RUN / 'protocol.json').read_text())
for name, expected in protocol['source_sha256'].items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
manifest = json.loads((RUN / 'artifact-manifest.json').read_text())
for item in manifest['files']:
    assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'], item['path']
pairs = {r['id']: r for r in map(json.loads, (RUN / 'pairs.jsonl').open())}
rows = list(map(json.loads, (RUN / 'qwen25.results.jsonl').open()))
assert len(rows) == len({r['run_key'] for r in rows}) == 1946
assert {r['model'] for r in rows} == {protocol['models'][0]['id']}
assert not any(r.get('error') for r in rows)
by_config = {c: {r['pair_id']: r for r in rows if r['config'] == c} for c in protocol['configs']}
assert all(set(group) == set(pairs) for group in by_config.values())


def independent_parse(raw):
    start = raw.find('{')
    if start < 0:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(raw[start:])
    except json.JSONDecodeError:
        return None
    if not isinstance(value, dict) or not isinstance(value.get('verdict'), str):
        return None
    if value['verdict'].strip().lower() not in {'benign', 'malicious'}:
        return None
    if not isinstance(value.get('reason'), str) or not isinstance(value.get('evidence'), list):
        return None
    if not all(isinstance(e, str) for e in value['evidence']):
        return None
    return {**value, 'verdict': value['verdict'].strip().lower()}


def state(row):
    return row['verdict'] if row['json_valid'] else 'invalid'


for row in rows:
    parsed = independent_parse(row['raw'])
    assert row['json_valid'] == (parsed is not None and row['finish_reason'] != 'length')
    assert row['verdict'] == (parsed['verdict'] if parsed else None)
    assert row['label'] == pairs[row['pair_id']]['label']
    assert (row['seed'], row['temperature'], row['top_p'], row['cards']) == (0, 0, 1, [])
    assert row['diff_sha256'] == hashlib.sha256(pairs[row['pair_id']]['diff'].encode()).hexdigest()

tokenizer = AutoTokenizer.from_pretrained(protocol['models'][0]['path'], local_files_only=True)
prompt_hashes = []
for key, pair in pairs.items():
    baseline, intent = build('DIFF', pair), build('DIFF+I', pair)
    assert intent[0] == baseline[0]
    assert intent[1]['content'].replace(intent_block(pair), '', 1) == baseline[1]['content']
    assert pair['intent_from'] == pair['before']
    for config, messages in [('DIFF', baseline), ('DIFF+I', intent)]:
        assert messages == build(config, {**pair, 'label': 'audit_label_not_for_prompt'})
        encoded = tokenizer.apply_chat_template(messages, tokenize=True, add_generation_prompt=True)
        tokens = len(encoded['input_ids'])
        assert tokens == by_config[config][key]['prompt_tokens'], (key, config)
        assert tokens + 512 <= 32768
        prompt_hashes.append({'pair_id': key, 'config': config, 'tokens': tokens,
                             'sha256': hashlib.sha256(json.dumps(messages).encode()).hexdigest()})
summary = {'verified_runs': len(rows), 'frozen_artifact_hashes_verified': len(manifest['files']),
           'reconstructed_prompt_token_counts_verified': len(prompt_hashes), 'new_llm_calls': 0,
           'prompt_reconstruction_note': 'Rebuilt from frozen code; original HTTP bodies were not logged.',
           'groups': {}, 'paired_transitions': {}, 'both_valid_diagnostic': {}}
reported = json.loads((RUN / 'summary.json').read_text())['groups']
for config, group in by_config.items():
    selected = list(group.values())
    entry = {subset: dict(Counter(state(r) for r in selected if pairs[r['pair_id']]['subset'] == subset))
             for subset in ['MAL', 'TYP']}
    limited = [r for r in selected if r['finish_reason'] == 'length']
    assert all(r['completion_tokens'] == 512 for r in limited)
    entry['length_limited'] = len(limited)
    entry['length_without_verdict_field'] = sum(not re.search(r'(?<!\\)"verdict"\s*:', r['raw']) for r in limited)
    entry['other_invalid'] = sum(not r['json_valid'] and r['finish_reason'] != 'length' for r in selected)
    entry['json_valid'] = sum(r['json_valid'] for r in selected)
    entry['valid_more_than_three_evidence_items'] = sum(len(r['evidence']) > 3 for r in selected if r['json_valid'])
    entry['valid_multiline_evidence'] = sum(any('\n' in e for e in r['evidence']) for r in selected if r['json_valid'])
    old = next(g for g in reported if g['model'] == rows[0]['model'] and g['config'] == config)
    assert entry['MAL']['malicious'] == old['mal_source_recall_proxy']['positive']
    assert entry['TYP']['malicious'] == old['typ_assumed_benign_fpr']['positive']
    assert entry['json_valid'] == old['json_valid']
    summary['groups'][config] = entry
for subset in ['MAL', 'TYP']:
    keys = [k for k, p in pairs.items() if p['subset'] == subset]
    transitions = Counter(f"{state(by_config['DIFF'][k])}->{state(by_config['DIFF+I'][k])}" for k in keys)
    assert sum(transitions.values()) == len(keys)
    summary['paired_transitions'][subset] = dict(transitions)
    common = [k for k in keys if all(by_config[c][k]['json_valid'] for c in by_config)]
    summary['both_valid_diagnostic'][subset] = {'n': len(common), **{
        c: sum(by_config[c][k]['verdict'] == 'malicious' for k in common) for c in by_config}}
log = (RUN / 'qwen25.server.log').read_text()
assert protocol['models'][0]['path'] in log and 'Resolved architecture: Qwen2ForCausalLM' in log
requests = [line for line in log.splitlines() if 'POST /v1/chat/completions HTTP/' in line]
assert len(requests) == 1946 and all('200 OK' in line for line in requests)
summary['http_200_count'] = len(requests)
(HERE / 'audit.json').write_text(json.dumps(summary, indent=2) + '\n')
(HERE / 'reconstructed-prompts.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in prompt_hashes))
print(json.dumps(summary, indent=2))
