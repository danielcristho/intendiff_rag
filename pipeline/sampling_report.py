"""Usage: python pipeline/sampling_report.py --release DIR | --selfcheck."""
import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

from analysis import cost_summary, flip_rate, verdict_of
from configs import CONFIGS, CONTRASTS
from mal_eval_metrics import campaign_recall, paired_rate_delta
from runner import load_jsonl
from sampling_batch import grid, verify_cell
from sampling_grid import stem

REFERENCE = (0.0, 0)


def by_config(rows):
    return {c: [r for r in rows if r['config'] == c] for c in CONFIGS}


def cell_rows(release, model, temperature, seed):
    if not verify_cell(release, model, temperature, seed)['complete']:
        raise ValueError(f'{stem(model["tag"], temperature, seed)} is not verified complete')
    rows = load_jsonl(release / f'{stem(model["tag"], temperature, seed)}.results.jsonl')
    return by_config([r for r in rows if not r.get('error')])


def reproduction(historical, rows):
    """How far the reference cell reproduces the historical T=0 run, pair by pair."""
    before = {(r['pair_id'], r['config']): r for r in historical}
    if set(before) != {(r['pair_id'], r['config']) for r in rows}:
        raise ValueError('Reference cell and historical run cover different requests')
    return dict(n=len(rows),
                verdict_agree=sum(verdict_of(r) == verdict_of(before[r['pair_id'], r['config']]) for r in rows),
                raw_identical=sum(r['raw'] == before[r['pair_id'], r['config']]['raw'] for r in rows))


def sign(value):
    return (value > 0) - (value < 0)


def cell_metrics(tag, temperature, seed, config, rows, mal, typ):
    mal_ids = {p['id'] for p in mal}
    mal_rows = [r for r in rows if r['pair_id'] in mal_ids]
    typ_rows = [r for r in rows if r['pair_id'] not in mal_ids]
    tpr, fpr = campaign_recall(mal, mal_rows, 'benign'), campaign_recall(typ, typ_rows, 'benign')
    cost = cost_summary(rows)
    return dict(model=tag, temperature=temperature, seed=seed, config=config,
                tpr=tpr['tpr'], tpr_low=tpr['campaign_bootstrap_95'][0], tpr_high=tpr['campaign_bootstrap_95'][1],
                fpr=fpr['tpr'], fpr_low=fpr['campaign_bootstrap_95'][0], fpr_high=fpr['campaign_bootstrap_95'][1],
                tpr_invalid_malicious=sum(verdict_of(r, 'malicious') == 'malicious' for r in mal_rows) / len(mal),
                fpr_invalid_malicious=sum(verdict_of(r, 'malicious') == 'malicious' for r in typ_rows) / len(typ),
                invalid=sum(not r['json_valid'] for r in rows), json_validity=sum(r['json_valid'] for r in rows) / len(rows),
                mean_completion_tokens=cost['mean_completion_tokens'], median_latency_ms=cost['median_latency_ms'])


def stability(tag, temperature, config, metrics, seed_rows, mal_ids):
    chosen = [m for m in metrics if (m['model'], m['temperature'], m['config']) == (tag, temperature, config)]
    pooled = [r for rows in seed_rows for r in rows]
    row = dict(model=tag, temperature=temperature, config=config, seeds=len(chosen))
    for rate in ('tpr', 'fpr'):
        values = [m[rate] for m in chosen]
        row.update({f'{rate}_mean': statistics.fmean(values), f'{rate}_min': min(values), f'{rate}_max': max(values)})
    row.update(flip_all=flip_rate(pooled), flip_mal=flip_rate([r for r in pooled if r['pair_id'] in mal_ids]),
               flip_typ=flip_rate([r for r in pooled if r['pair_id'] not in mal_ids]))
    return row


def contrast(tag, temperature, seed, rows, mal, typ):
    mal_ids = {p['id'] for p in mal}
    out = []
    for baseline, variant in CONTRASTS:
        split = [([r for r in rows[c] if r['pair_id'] in mal_ids], [r for r in rows[c] if r['pair_id'] not in mal_ids])
                 for c in (baseline, variant)]
        tpr, tpr_ci = paired_rate_delta(mal, split[0][0], split[1][0])
        fpr, fpr_ci = paired_rate_delta(typ, split[0][1], split[1][1])
        out.append(dict(model=tag, temperature=temperature, seed=seed, baseline=baseline, variant=variant,
                        tpr_delta_points=tpr, tpr_low=tpr_ci[0], tpr_high=tpr_ci[1],
                        fpr_delta_points=fpr, fpr_low=fpr_ci[0], fpr_high=fpr_ci[1]))
    return out


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def report(release):
    protocol = json.loads((release / 'protocol.json').read_text())
    pairs = load_jsonl(release / 'test.pairs.jsonl')
    mal = [p for p in pairs if p['label'] == 'malicious']
    typ = [p for p in pairs if p['label'] == 'benign']
    mal_ids = {p['id'] for p in mal}
    metrics, stable, contrasts, reproduced, responses = [], [], [], {}, 0
    for model in protocol['models']:
        tag = model['tag']
        rows = {(t, s): cell_rows(release, model, t, s) for t, s in grid(protocol)}
        responses += sum(len(r) for configs in rows.values() for r in configs.values())
        for (t, s), configs in rows.items():
            metrics += [cell_metrics(tag, t, s, c, configs[c], mal, typ) for c in CONFIGS]
            contrasts += contrast(tag, t, s, configs, mal, typ)
        for t in protocol['temperatures']:
            stable += [stability(tag, t, c, metrics, [rows[t, s][c] for s in protocol['seeds']], mal_ids)
                       for c in CONFIGS]
        historical = by_config([r for path in protocol['historical'][tag] for r in load_jsonl(path) if not r.get('error')])
        reproduced[tag] = {c: reproduction(historical[c], rows[REFERENCE][c]) for c in CONFIGS}
    reference = {(c['model'], c['baseline'], c['variant']): c for c in contrasts
                 if (c['temperature'], c['seed']) == REFERENCE}
    for c in contrasts:
        ref = reference[c['model'], c['baseline'], c['variant']]
        c.update(tpr_same_sign=sign(c['tpr_delta_points']) == sign(ref['tpr_delta_points']),
                 fpr_same_sign=sign(c['fpr_delta_points']) == sign(ref['fpr_delta_points']))
    for name, rows in (('metrics.csv', metrics), ('stability.csv', stable), ('contrasts.csv', contrasts)):
        write_csv(release / name, rows)
    summary = dict(decision='D111', reference_cell=REFERENCE, reproduction=reproduced,
                   cells=len(grid(protocol)), models=[m['tag'] for m in protocol['models']], responses=responses)
    if responses != protocol['total_expected_generations']:
        raise ValueError(f'{responses} responses, expected {protocol["total_expected_generations"]}')
    (release / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


def selfcheck():
    def row(pair, verdict, valid=True, raw='{}'):
        return dict(pair_id=pair, config='DIFF', verdict=verdict, json_valid=valid, raw=raw)
    before = [row('a', 'malicious'), row('b', 'benign')]
    assert reproduction(before, before) == dict(n=2, verdict_agree=2, raw_identical=2)
    # A reply that turns invalid counts as benign, so benign -> invalid is not a disagreement.
    after = [row('a', 'benign', raw='x'), row('b', None, valid=False, raw='y')]
    assert reproduction(before, after) == dict(n=2, verdict_agree=1, raw_identical=0)
    try:
        reproduction(before, before[:1])
    except ValueError:
        pass
    else:
        raise AssertionError('a missing request must not be scored as agreement')
    assert (sign(0.0), sign(-0.5), sign(2)) == (0, -1, 1)
    print('ok')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path)
    parser.add_argument('--selfcheck', action='store_true')
    args = parser.parse_args()
    if args.selfcheck:
        selfcheck()
        return
    report(args.release.resolve())


if __name__ == '__main__':
    sys.exit(main())
