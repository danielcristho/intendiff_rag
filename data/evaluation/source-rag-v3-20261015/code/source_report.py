"""Usage: python pipeline/source_report.py --release DIR."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

from analysis import cost_summary, recall_delta_bootstrap, wilson_ci
from configs import CONTRASTS
from samples import load_jsonl
from source_results import verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    args = parser.parse_args()
    out = args.release
    protocol = json.loads((out / 'protocol.json').read_text())
    pairs = load_jsonl(out / 'test.pairs.jsonl')
    comparisons, metrics = [], []
    text = ['# Hasil RAG berbasis label dataset', '',
            'MAL memakai label sumber; TYP assumed-benign. Ini evaluasi deskriptif, '
            'bukan gold manusia atau pengujian hipotesis FPR_HN. Invalid dihitung benign '
            'pada hasil utama dan malicious pada sensitivitas. Akurasi merupakan akurasi '
            'cohort dengan rasio kelas ini, bukan estimasi populasi npm.', '',
            '| Model | Konfigurasi | TPR MAL (95% Wilson) | Akurasi cohort | Balanced accuracy | Invalid |',
            '|---|---|---|---|---|---|']
    strata_lines = ['', '| Model | Konfigurasi | Strata TYP | FP / n | FPR (95% Wilson) |', '|---|---|---|---|---|']
    for model in protocol['models']:
        checked = verify(out, 'test', model)
        if not checked['complete']:
            raise ValueError('Full test matrix is incomplete; use source_status.py for progress')
        rows = [r for r in load_jsonl(out / f'test.{model["tag"]}.results.jsonl') if not r.get('error')]
        grouped = defaultdict(list)
        for row in rows:
            grouped[row['config']].append(row)
        for group in checked['groups']:
            metric = dict(group, model=model['id'])
            tp, fn = (group['confusion'].get(k, 0) for k in ('TP', 'FN'))
            metric['tpr_wilson_95'] = list(map(float, wilson_ci(tp, tp + fn)))
            metric['cost'] = cost_summary(grouped[group['config']])
            for name, stratum in metric['typ_strata'].items():
                stratum['fpr'] = stratum['alarms'] / stratum['n']
                stratum['wilson_95'] = list(map(float, wilson_ci(stratum['alarms'], stratum['n'])))
                if group['invalid_as'] == 'benign':
                    low, high = stratum['wilson_95']
                    strata_lines.append(f"| {model['tag']} | {group['config']} | {name} | {stratum['alarms']} / {stratum['n']} | {stratum['fpr']:.2%} [{low:.2%}, {high:.2%}] |")
            metrics.append(metric)
            if group['invalid_as'] == 'benign':
                low, high = metric['tpr_wilson_95']
                text.append(f"| {model['tag']} | {group['config']} | {group['tpr_source']:.2%} [{low:.2%}, {high:.2%}] | {group['cohort_accuracy']:.2%} | {group['balanced_accuracy']:.2%} | {group['invalid']} |")
        strata = {'MAL': [p for p in pairs if p['subset'] == 'MAL']}
        for pair in pairs:
            if pair['subset'] == 'TYP':
                strata.setdefault('TYP:' + pair['group'], []).append(pair)
        for baseline, variant in CONTRASTS:
            for name, members in strata.items():
                ids = {p['id'] for p in members}
                delta, interval = recall_delta_bootstrap(
                    [r for r in grouped[variant] if r['pair_id'] in ids],
                    [r for r in grouped[baseline] if r['pair_id'] in ids], members)
                comparisons.append(dict(model=model['id'], baseline=baseline, variant=variant,
                    subset=name, alarm_rate_delta_points=float(delta),
                    campaign_bootstrap_95=list(map(float, interval)), resamples=10000, seed=2026,
                    confirmatory_hypothesis_test=False))
    text.extend(strata_lines)
    text += ['', 'Selisih paired dan CI bootstrap kampanye, sensitivitas invalid, '
             'serta token/latency tersimpan di `summary.json`. Tidak memilih konfigurasi '
             'atau mengubah prompt berdasarkan hasil test.', '']
    (out / 'summary.json').write_text(json.dumps(dict(metrics=metrics, paired_comparisons=comparisons), indent=2) + '\n')
    (out / 'results.md').write_text('\n'.join(text))
    print(str(out / 'results.md'))


if __name__ == '__main__':
    main()
