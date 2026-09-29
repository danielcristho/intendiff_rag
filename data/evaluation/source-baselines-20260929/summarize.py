"""Verify real responses and summarize agreement with provisional source labels."""
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from analysis import cost_summary, latest_runs, verdict_of
from runner import parse_verdict

HERE = Path(__file__).resolve().parent
protocol = json.loads((HERE / 'protocol.json').read_text())
pairs = {row['id']: row for row in
         (json.loads(line) for line in (HERE / 'pairs.jsonl').open())}
campaign_sizes = Counter(pair['campaign'] for pair in pairs.values() if pair['subset'] == 'MAL')
audit_path = HERE.parents[1] / 'acquisition/context-audit-baselines.jsonl'
token_audit = {(row['model'], row['pair_id']): row['prompt_tokens']
               for row in map(json.loads, audit_path.open())}
for filename, expected in protocol['source_sha256'].items():
    assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected, filename
rows = []
attempts = 0
for model in protocol['models']:
    path = HERE / f'{model["tag"]}.results.jsonl'
    if path.exists():
        records = [json.loads(line) for line in path.open() if line.endswith('\n')]
        attempts += len(records)
        rows.extend(latest_runs(records))
expected_keys = {(m['id'], config, pair_id) for m in protocol['models']
                 for config in protocol['configs'] for pair_id in pairs}
actual = {(r['model'], r['config'], r['pair_id']) for r in rows}
assert actual <= expected_keys and len(actual) == len(rows)
for row in rows:
    pair = pairs[row['pair_id']]
    assert row['label'] == pair['label'] and row['diff_sha256'] == pair['diff_sha256']
    assert row['evaluation_scope'] == 'exploratory_source_labels'
    assert row['human_annotation_verified'] is False
    if row.get('error'):
        continue
    parsed = parse_verdict(row['raw'])
    valid = parsed is not None and row['finish_reason'] != 'length'
    assert valid == row['json_valid']
    if parsed:
        assert parsed['verdict'] == row['verdict'] and parsed['evidence'] == row['evidence']
    assert row['prompt_tokens'] > 0 and row['completion_tokens'] > 0
    if row['config'] == 'DIFF+I':
        assert row['prompt_tokens'] == token_audit[row['model'], row['pair_id']]


def rate(selected, invalid_as='benign'):
    positive = sum(verdict_of(r, invalid_as) == 'malicious' for r in selected)
    return {'positive': positive, 'n': len(selected),
            'rate': positive / len(selected) if selected else None}


def invalid_category(row):
    if row['finish_reason'] == 'length':
        return 'length_limit'
    start = row['raw'].find('{')
    if start < 0:
        return 'missing_json_object'
    try:
        json.JSONDecoder().raw_decode(row['raw'][start:])
    except json.JSONDecodeError:
        return 'json_syntax'
    return 'schema_mismatch'


groups = []
for model in protocol['models']:
    for config in protocol['configs']:
        group = [r for r in rows if r['model'] == model['id'] and r['config'] == config]
        successful = [r for r in group if not r.get('error')]
        mal = [r for r in successful if pairs[r['pair_id']]['subset'] == 'MAL']
        typ = [r for r in successful if pairs[r['pair_id']]['subset'] == 'TYP']
        campaigns = defaultdict(list)
        for row in mal:
            campaigns[pairs[row['pair_id']]['campaign']].append(row)
        entry = {'model': model['id'], 'config': config, 'completed': len(successful),
                 'transport_errors': len(group) - len(successful),
                 'json_valid': sum(r['json_valid'] for r in successful),
                 'length_limited': sum(r['finish_reason'] == 'length' for r in successful),
                 'invalid_categories': dict(Counter(invalid_category(r) for r in successful
                                                     if not r['json_valid'])),
                 'mal_source_recall_proxy': rate(mal), 'typ_assumed_benign_fpr': rate(typ),
                 'invalid_as_malicious': {'mal': rate(mal, 'malicious'), 'typ': rate(typ, 'malicious')},
                 'mal_campaigns': len(campaigns),
                 'mal_campaign_macro_recall_proxy': (sum(rate(rs)['rate'] for rs in campaigns.values())
                                                    / len(campaigns)) if campaigns else None,
                 'cost': cost_summary(successful),
                 'total_prompt_tokens': sum(r['prompt_tokens'] for r in successful),
                 'total_completion_tokens': sum(r['completion_tokens'] for r in successful)}
        entry['mal_subgroups'] = {
            'truncated': rate([r for r in mal if pairs[r['pair_id']]['truncated']]),
            'not_truncated': rate([r for r in mal if not pairs[r['pair_id']]['truncated']]),
            'empty_delta': rate([r for r in mal if not pairs[r['pair_id']]['delta']]),
            'nonempty_delta': rate([r for r in mal if pairs[r['pair_id']]['delta']])}
        quoted = [r for r in successful if r.get('evidence')]
        matching = sum(all(line in pairs[r['pair_id']]['diff'].splitlines()
                           for line in r['evidence']) for r in quoted)
        entry['verbatim_evidence_check'] = {'responses_with_evidence': len(quoted),
                                            'all_quotes_match_diff_lines': matching,
                                            'gold_localization': False}
        groups.append(entry)
summary = {'scope': protocol['scope'], 'human_annotation_verified': False,
           'generated_at_utc': datetime.now(timezone.utc).isoformat(),
           'expected_runs': len(expected_keys), 'unique_runs': len(rows), 'attempt_records': attempts,
           'complete': actual == expected_keys and not any(r.get('error') for r in rows),
           'missing_runs': len(expected_keys - actual), 'groups': groups,
           'mal_campaigns': len(campaign_sizes), 'largest_mal_campaign_count': max(campaign_sizes.values()),
           'limitations': ['MAL uses upstream source labels; TYP is assumed benign.',
                           'Candidate corpus, without final campaign cap or post-release quota.',
                           'No HN, retrieval configurations, gold evidence localization, or hypothesis tests.',
                           'Sequential observed latency includes initial requests and prefix caching.']}
(HERE / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
(HERE / 'results.jsonl').write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
from reporting import write_report

write_report(summary, HERE)
print(json.dumps({'complete': summary['complete'], 'unique_runs': len(rows), 'groups': groups}), flush=True)
