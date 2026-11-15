"""Compute campaign-resampled MAL recall and explicitly descriptive combined metrics."""
import numpy as np


def campaign_recall(pairs, rows, invalid_as, resamples=10000, seed=2026):
    by_id = {r['pair_id']: r for r in rows}
    if len(by_id) != len(rows) or set(by_id) != {p['id'] for p in pairs}:
        raise ValueError('Campaign recall requires complete unique predictions')
    campaigns = sorted({p['campaign'] for p in pairs})
    totals, positives = [], []
    for campaign in campaigns:
        members = [by_id[p['id']] for p in pairs if p['campaign'] == campaign]
        totals.append(len(members))
        positives.append(sum((r['verdict'] if r['json_valid'] else invalid_as) == 'malicious' for r in members))
    draws = np.random.default_rng(seed).integers(0, len(campaigns), size=(resamples, len(campaigns)))
    rates = np.asarray(positives)[draws].sum(axis=1) / np.asarray(totals)[draws].sum(axis=1)
    return dict(tpr=sum(positives) / sum(totals),
                campaign_bootstrap_95=np.percentile(rates, [2.5, 97.5]).tolist(),
                macro_campaign_tpr=float(np.mean(np.asarray(positives) / np.asarray(totals))),
                campaigns=len(campaigns), resamples=resamples, seed=seed)


def combined_metrics(old, new):
    counts = {k: old.get(k, 0) + new.get(k, 0) for k in ('TP', 'FN', 'TN', 'FP')}
    tp, fn, tn, fp = (counts[k] for k in ('TP', 'FN', 'TN', 'FP'))
    if tp + fn != 129 or tn + fp != 1868:
        raise ValueError('Expected 129 MAL and 1868 historical TYP in combined cohort')
    tpr, specificity = tp / (tp + fn), tn / (tn + fp)
    return dict(confusion=counts, tpr=tpr, historical_typ_fpr=1 - specificity,
                cohort_accuracy=(tp + tn) / (tp + fn + tn + fp),
                balanced_accuracy=(tpr + specificity) / 2,
                interpretation='Descriptive combination; TYP reused from historical evaluation, not new holdout')


def paired_rate_delta(pairs, baseline_rows, variant_rows, resamples=10000, seed=2026):
    """Campaign-resampled change in the share called malicious; vectorised for the 1.868-pair TYP set."""
    def called(rows):
        return {r['pair_id']: (r['verdict'] if r['json_valid'] else 'benign') == 'malicious' for r in rows}
    base, variant = called(baseline_rows), called(variant_rows)
    if set(base) != {p['id'] for p in pairs} or set(variant) != set(base):
        raise ValueError('Paired rate requires complete predictions for both configurations')
    campaigns = sorted({p['campaign'] for p in pairs})
    index = {c: i for i, c in enumerate(campaigns)}
    totals, diffs = np.zeros(len(campaigns)), np.zeros(len(campaigns))
    for p in pairs:
        totals[index[p['campaign']]] += 1
        diffs[index[p['campaign']]] += variant[p['id']] - base[p['id']]
    draws = np.random.default_rng(seed).integers(0, len(campaigns), size=(resamples, len(campaigns)))
    deltas = diffs[draws].sum(axis=1) / totals[draws].sum(axis=1) * 100
    return float(diffs.sum() / totals.sum() * 100), np.percentile(deltas, [2.5, 97.5]).tolist()
