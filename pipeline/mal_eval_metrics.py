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
