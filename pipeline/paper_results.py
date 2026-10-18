"""Usage: python pipeline/paper_results.py. Export verified D101/D102/D105 results."""
import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

from analysis import cost_summary
from paper_tables import render

ROOT = Path('data/evaluation/source-rag-mal-20261018')
OUT = Path('data/writing/paper-20261018')
CONFIGS = ('DIFF', 'DIFF+I', 'DIFF+I+M', 'DIFF+I+MM', 'DIFF+I+MB', 'DIFF+MB')
NAMES = dict(qwen3='Qwen3-4B', qwen25='Qwen2.5-3B', qwen25_7b='Qwen2.5-7B',
             phi4_mini='Phi-4-mini', llama31_8b='Llama-3.1-8B', granite33_8b='Granite-3.3-8B')
PINS = {}


def read(path, lines=False):
    path = Path(path)
    content = path.read_bytes()
    PINS[str(path)] = hashlib.sha256(content).hexdigest()
    return [json.loads(line) for line in content.splitlines() if line.strip()] if lines else json.loads(content)


def checked_rows(directory, tag, model_id):
    pairs = {p['id']: p for p in read(directory / 'test.pairs.jsonl', True)}
    verification = read(directory / f'test.{tag}.verification.json')
    raw = read(directory / f'test.{tag}.results.jsonl', True)
    rows = [r for r in raw if not r.get('error')]
    expected = {(p, c) for p in pairs for c in CONFIGS}
    if len(rows) != len(expected) or {(r['pair_id'], r['config']) for r in rows} != expected:
        raise ValueError(f'Incomplete or duplicate results: {directory}')
    if not verification['complete'] or verification['completed'] != len(rows):
        raise ValueError('Saved verification is not complete')
    for row in rows:
        pair = pairs[row['pair_id']]
        if row['model'] != model_id or row['label'] != pair['label'] or row['diff_sha256'] != pair['diff_sha256']:
            raise ValueError('Prediction identity does not match frozen input')
    valid = sum(r['json_valid'] for r in rows) / len(rows)
    if not math.isclose(valid, verification['json_validity']):
        raise ValueError('JSON validity differs from verification')
    return pairs, rows, verification


def confusion(rows, config, invalid_as):
    result = Counter()
    for row in rows:
        if row['config'] != config:
            continue
        positive = (row['verdict'] if row['json_valid'] else invalid_as) == 'malicious'
        malicious = row['label'] == 'malicious'
        result[('TP' if positive else 'FN') if malicious else ('FP' if positive else 'TN')] += 1
    return {k: result[k] for k in ('TP', 'FN', 'TN', 'FP')}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = read(ROOT / 'manifest.json')
    if not read(ROOT / 'completion.json')['complete'] or len(manifest['models']) != 6:
        raise ValueError('All six eligible models must be complete')
    records, effects, checks, summaries = [], [], [], {}
    for tag in manifest['models']:
        release = ROOT / tag
        protocol = read(release / 'protocol.json')
        parent = Path(protocol['parent_release'])
        model, = protocol['models']
        old_pairs, old_rows, old_verify = checked_rows(parent, tag, model['id'])
        new_pairs, new_rows, new_verify = checked_rows(release, tag, model['id'])
        if len(old_pairs) != 1901 or len(new_pairs) != 96 or set(old_pairs) & set(new_pairs):
            raise ValueError('Unexpected cohort size or overlap')
        summary = read(release / 'summary.json')
        old_summary = read(parent / 'summary.json')
        old_cost = {(m['config'], m['invalid_as']): m['cost'] for m in old_summary['metrics']
                    if m['model'] == model['id']}
        summaries[tag] = summary
        for metric in summary['metrics']:
            config, policy = metric['config'], metric['invalid_as']
            old = confusion(old_rows, config, policy)
            new = confusion(new_rows, config, policy)
            for actual, saved in ((old, metric['historical']['confusion']), (new, metric['new_confusion'])):
                if any(actual[k] != saved.get(k, 0) for k in actual):
                    raise ValueError('Summary confusion counts differ from saved responses')
            if (old['TP'] + old['FN'], old['TN'] + old['FP'], new['TP'] + new['FN']) != (33, 1868, 96):
                raise ValueError('Unexpected class denominators')
            combined = {k: old[k] + new[k] for k in old}
            accuracy = (combined['TP'] + combined['TN']) / 1997
            balanced = (combined['TP'] / 129 + combined['TN'] / 1868) / 2
            if not math.isclose(accuracy, metric['combined']['cohort_accuracy']) or not math.isclose(
                    balanced, metric['combined']['balanced_accuracy']):
                raise ValueError('Combined metrics differ from raw counts')
            if cost_summary([r for r in old_rows if r['config'] == config]) != old_cost[config, policy]:
                raise ValueError('Token or latency summaries differ from raw responses')
            row = dict(tag=tag, model=NAMES[tag], config=config, invalid_as=policy,
                       old_tp=old['TP'], new_tp=new['TP'], typ_fp=old['FP'],
                       old_tpr=old['TP']/33, new_tpr=new['TP']/96, fpr=old['FP']/1868,
                       new_tpr_low=metric['new']['campaign_bootstrap_95'][0],
                       new_tpr_high=metric['new']['campaign_bootstrap_95'][1],
                       macro_campaign_tpr=metric['new']['macro_campaign_tpr'],
                       combined_accuracy=metric['combined']['cohort_accuracy'],
                       combined_balanced_accuracy=metric['combined']['balanced_accuracy'],
                       old_json_validity=old_verify['json_validity'], new_json_validity=new_verify['json_validity'],
                       new_invalid=metric['invalid'], **old_cost[config, policy])
            if not math.isclose(row['new_tpr'], metric['new']['tpr']):
                raise ValueError('TPR differs from raw counts')
            records.append(row)
        for contrast in summary['paired_comparisons']:
            baseline, variant = contrast['baseline'], contrast['variant']
            a, b = (next(r for r in records if r['tag'] == tag and r['config'] == c
                         and r['invalid_as'] == 'benign') for c in (baseline, variant))
            if not math.isclose((b['new_tpr']-a['new_tpr'])*100, contrast['delta_points'], abs_tol=1e-10):
                raise ValueError('Paired point estimate differs from counts')
            effects.append(dict(tag=tag, model=NAMES[tag], fpr_delta_points=(b['fpr']-a['fpr'])*100, **contrast))
        checks.append(dict(tag=tag, historical_responses=len(old_rows), supplemental_responses=len(new_rows),
                           transport_attempt_errors=old_verify['transport_attempt_errors']+new_verify['transport_attempt_errors']))
    for name, rows in (('metrics.csv', records), ('contrasts.csv', effects)):
        with (OUT / name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    render(records, effects, NAMES)
    result = dict(verified=True, checks=checks, total_test_responses=sum(r['historical_responses']+
                  r['supplemental_responses'] for r in checks), unique_pairs=1997,
                  new_pairs=96, new_campaigns=65, inference_performed=False,
                  verification_scope='Complete saved verifications plus raw-response coverage, identities, confusion counts and summary consistency; no new model execution',
                  input_pins=[dict(path=k, sha256=v) for k, v in sorted(PINS.items())])
    (OUT / 'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'input_pins'}, indent=2))


if __name__ == '__main__':
    main()
