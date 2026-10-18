"""Usage: python pipeline/mal_eval_report.py --release DIR."""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

from mal_eval_metrics import campaign_recall, combined_metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--release', type=Path, required=True)
    out = parser.parse_args().release
    sys.path.insert(0, str((out / 'code').resolve()))
    from source_results import verify
    from source_experiment import check_pins
    from samples import load_jsonl
    from analysis import cost_summary, recall_delta_bootstrap
    from configs import CONTRASTS
    protocol = json.loads((out / 'protocol.json').read_text())
    model, = protocol['models']
    check_pins(protocol, model)
    new = verify(out, 'test', model)
    old = verify(Path(protocol['parent_release']), 'test', model)
    if not new['complete'] or not old['complete']:
        raise ValueError('Reports require both complete verified matrices')
    pairs = load_jsonl(out / 'test.pairs.jsonl')
    groups = defaultdict(list)
    for row in load_jsonl(out / f'test.{model["tag"]}.results.jsonl'):
        if not row.get('error'):
            groups[row['config']].append(row)
    historical = {(g['config'], g['invalid_as']): g for g in old['groups']}
    metrics, comparisons = [], []
    text = ['# Evaluasi MAL tambahan D105', '',
            '96 pair / 65 kampanye; label sumber, bukan gold manusia. Invalid dianggap benign '
            'pada hasil utama. Interval memakai bootstrap kampanye. FPR dan balanced accuracy '
            'tidak terdefinisi untuk cohort tambahan yang seluruhnya MAL. Hasil gabungan di '
            'summary.json hanya deskriptif dan memakai ulang TYP lama.', '',
            '| Konfigurasi | TP / 96 | TPR baru (95% bootstrap kampanye) | Invalid |',
            '|---|---|---|---|']
    for group in new['groups']:
        config, policy = group['config'], group['invalid_as']
        previous = historical[config, policy]
        metric = dict(config=config, invalid_as=policy, new_confusion=group['confusion'],
                      invalid=group['invalid'], new=campaign_recall(pairs, groups[config], policy),
                      historical=previous, combined=combined_metrics(previous['confusion'], group['confusion']),
                      cost=cost_summary(groups[config]))
        metrics.append(metric)
        if policy == 'benign':
            low, high = metric['new']['campaign_bootstrap_95']
            text.append(f"| {config} | {group['confusion'].get('TP', 0)} / 96 | "
                        f"{metric['new']['tpr']:.2%} [{low:.2%}, {high:.2%}] | {group['invalid']} |")
    for baseline, variant in CONTRASTS:
        delta, interval = recall_delta_bootstrap(groups[variant], groups[baseline], pairs)
        comparisons.append(dict(baseline=baseline, variant=variant, delta_points=float(delta),
                                campaign_bootstrap_95=list(map(float, interval)), resamples=10000, seed=2026))
    summary = dict(model=model['id'], complete=True, pairs=96, campaigns=65,
                   json_validity=new['json_validity'], metrics=metrics, paired_comparisons=comparisons,
                   confirmatory_hypothesis_test=False)
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    (out / 'results.md').write_text('\n'.join(text) + '\n')
    print(str(out / 'results.md'), flush=True)


if __name__ == '__main__':
    main()
