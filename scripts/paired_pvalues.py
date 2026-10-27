"""Exact campaign-level paired tests for the manuscript; no model inference.

Run from the repository root: .venv/bin/python scripts/paired_pvalues.py
The null assumes independent clusters and sign symmetry of their differences.
Integer dynamic programming counts every sign assignment without Monte Carlo.
"""
import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from paper_results import CONFIGS, NAMES, PINS, ROOT, checked_rows, confusion, read

OUT = Path('data/writing/significance-20261026')
CONTRASTS = (
    ('Add M', 'DIFF+I', 'DIFF+I+M'),
    ('MM to MB', 'DIFF+I+MM', 'DIFF+I+MB'),
    ('Add intent', 'DIFF+MB', 'DIFF+I+MB'),
)


def exact_sign_flip(differences):
    """Two-sided P(|sum s_k*d_k| >= |sum d_k|), including ties.

    Coefficients of product(1 + x**abs(d_k)) count subset sums. If the
    subset sum is j and the total absolute difference is W, the signed sum
    is 2*j-W. Python integers keep the counts exact even above 2**1024.
    Zero-difference clusters cancel from the numerator and denominator.
    """
    if any(type(d) is not int for d in differences):
        raise ValueError('Cluster differences must be integers')
    weights = [abs(d) for d in differences if d]
    counts = [1]
    for weight in weights:
        updated = [0] * (len(counts) + weight)
        for j, count in enumerate(counts):
            updated[j] += count
            updated[j + weight] += count
        counts = updated
    total_weight = sum(weights)
    observed = abs(sum(differences))
    extreme = sum(count for j, count in enumerate(counts)
                  if abs(2*j - total_weight) >= observed)
    assignments = 2**len(weights)
    assert sum(counts) == assignments
    return dict(p_value=extreme / assignments, extreme_assignments=str(extreme),
                sign_assignments=str(assignments), nonzero_clusters=len(weights))


def holm_adjust(pvalues):
    if not pvalues or any(not math.isfinite(p) or not 0 <= p <= 1 for p in pvalues):
        raise ValueError('Expected a nonempty family of p-values in [0, 1]')
    order = sorted(range(len(pvalues)), key=pvalues.__getitem__)
    adjusted = [0.0] * len(pvalues)
    running = 0.0
    for rank, index in enumerate(order):
        running = max(running, min(1.0, (len(pvalues) - rank) * pvalues[index]))
        adjusted[index] = running
    return adjusted


def latex_p(value, bold=False):
    content = '<0.001' if value < 0.001 else f'{value:.3f}'
    return ('$\\mathbf{' + content + '}$') if bold else ('$' + content + '$')


def latex_rows(results):
    rows = []
    for tag, model in NAMES.items():
        for index, (name, _, _) in enumerate(CONTRASTS):
            cells = [model if index == 0 else '', name]
            for metric in ('TPR', 'FPR'):
                r, = [r for r in results if (r['tag'], r['contrast'], r['metric']) == (tag, name, metric)]
                cells.extend([f"${r['delta_points']:+.2f}$", latex_p(r['p_value']),
                              latex_p(r['p_holm'], r['significant_holm'])])
            rows.append('    ' + ' & '.join(cells) + r' \\')
    return '\n'.join(rows) + '\n'


def paired_test(pairs, baseline_rows, variant_rows):
    ids = {p['id'] for p in pairs}
    if not pairs or len(ids) != len(pairs) or any(not p.get('campaign') for p in pairs):
        raise ValueError('Expected unique pairs with campaign identities')

    def called(rows):
        if len(rows) != len(ids) or {r['pair_id'] for r in rows} != ids:
            raise ValueError('Expected complete unique paired predictions')
        if any(r.get('error') for r in rows):
            raise ValueError('Transport errors are not predictions')
        if any(r['json_valid'] and r['verdict'] not in ('malicious', 'benign') for r in rows):
            raise ValueError('Unexpected valid verdict')
        return {r['pair_id']: int(r['json_valid'] and r['verdict'] == 'malicious') for r in rows}

    a, b = called(baseline_rows), called(variant_rows)
    differences = Counter()
    for pair in pairs:
        differences[pair['campaign']] += b[pair['id']] - a[pair['id']]
    return dict(n_pairs=len(pairs), n_clusters=len(differences),
                baseline_positive=sum(a.values()), variant_positive=sum(b.values()),
                delta_points=100 * sum(differences.values()) / len(pairs),
                negative_to_positive=sum(a[i] == 0 and b[i] == 1 for i in ids),
                positive_to_negative=sum(a[i] == 1 and b[i] == 0 for i in ids),
                cluster_difference_histogram=dict(sorted(Counter(differences.values()).items())),
                **exact_sign_flip(list(differences.values())))


def main():
    PINS.clear()
    manifest = read(ROOT / 'manifest.json')
    if set(manifest['models']) != set(NAMES) or not read(ROOT / 'completion.json')['complete']:
        raise ValueError('Expected six complete models')
    metrics_path = Path('data/writing/paper-20261018/metrics.csv')
    contrasts_path = metrics_path.with_name('contrasts.csv')
    # Pin the earlier verified tables as well as the original response files.
    import hashlib
    for path in (metrics_path, contrasts_path):
        PINS[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    with metrics_path.open() as stream:
        metrics = {(r['tag'], r['config']): r for r in csv.DictReader(stream) if r['invalid_as'] == 'benign'}
    with contrasts_path.open() as stream:
        contrasts = {(r['tag'], r['baseline'], r['variant']): r for r in csv.DictReader(stream)}
    results, checks, cohort = [], [], None
    for tag in NAMES:
        release = ROOT / tag
        protocol = read(release / 'protocol.json')
        model, = protocol['models']
        old_pairs, old_rows, _ = checked_rows(Path(protocol['parent_release']), tag, model['id'])
        new_pairs, new_rows, _ = checked_rows(release, tag, model['id'])
        if len(old_pairs) != 1901 or len(new_pairs) != 96 or set(old_pairs) & set(new_pairs):
            raise ValueError('Unexpected cohort size or overlap')
        pairs, rows = list(old_pairs.values()) + list(new_pairs.values()), old_rows + new_rows
        identities = {p['id']: (p['label'], p['campaign'], p['diff_sha256']) for p in pairs}
        if cohort is not None and identities != cohort:
            raise ValueError('Models must share pairs, labels and campaign assignments')
        cohort = identities
        for config in CONFIGS:
            counts = confusion(rows, config, 'benign')
            saved = metrics[tag, config]
            if counts != dict(TP=int(saved['old_tp']) + int(saved['new_tp']),
                              FN=129-int(saved['old_tp'])-int(saved['new_tp']),
                              FP=int(saved['typ_fp']), TN=1868-int(saved['typ_fp'])):
                raise ValueError('Stored manuscript metrics disagree with raw responses')
        for name, baseline, variant in CONTRASTS:
            saved = contrasts[tag, baseline, variant]
            for metric, label, n, clusters, delta_key, ci_key in (
                ('TPR', 'malicious', 129, 98, 'pooled_delta_points', 'pooled_campaign_bootstrap_95'),
                ('FPR', 'benign', 1868, 1865, 'fpr_delta_points', 'fpr_campaign_bootstrap_95'),
            ):
                subset = [p for p in pairs if p['label'] == label]
                result = paired_test(subset, *([r for r in rows if r['label'] == label and r['config'] == c]
                                              for c in (baseline, variant)))
                if (result['n_pairs'], result['n_clusters']) != (n, clusters):
                    raise ValueError('Unexpected sample or campaign count')
                if not math.isclose(result['delta_points'], float(saved[delta_key]), abs_tol=1e-10):
                    raise ValueError('Paired difference disagrees with manuscript contrast')
                low, high = json.loads(saved[ci_key])
                results.append(dict(tag=tag, model=NAMES[tag], contrast=name, baseline=baseline,
                                    variant=variant, metric=metric, ci95_low=low, ci95_high=high, **result))
        checks.append(dict(tag=tag, responses=len(rows)))
    assert len(results) == 36
    for result, adjusted in zip(results, holm_adjust([r['p_value'] for r in results])):
        result.update(p_holm=adjusted, significant_holm=adjusted < 0.05)
    OUT.mkdir(parents=True, exist_ok=True)
    with (OUT / 'paired-pvalues.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    report = dict(method='exact cluster sign-flip, integer subset-sum dynamic programming',
                  alternative='two-sided, ties included', invalid_as='benign', family_size=36,
                  correction='Holm', alpha=0.05, inference_performed=False,
                  assumptions='Independent campaigns; cluster differences symmetric about zero under the null. Equal marginal rates alone do not imply this assumption.',
                  checks=checks, total_responses=sum(c['responses'] for c in checks), tests=results,
                  input_pins=[dict(path=k, sha256=v) for k, v in sorted(PINS.items())])
    (OUT / 'paired-pvalues.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'contrast-rows.tex').write_text(latex_rows(results))
    for r in results:
        print(f"{r['model']:15} {r['contrast']:10} {r['metric']} {r['delta_points']:+6.2f} "
              f"p={r['p_value']:.6g} Holm={r['p_holm']:.6g} {'*' if r['significant_holm'] else ''}")


if __name__ == '__main__':
    main()
