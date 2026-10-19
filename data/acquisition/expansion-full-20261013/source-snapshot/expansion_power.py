"""Write exact paired-test power sensitivity, without treating scenarios as observations."""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.stats import binom


def directional_power(n, fixes, regressions, alpha=0.05 / 6):
    if fixes + regressions <= 0:
        return 0.0
    discordant = np.arange(1, n + 1)
    cutoff = binom.ppf(alpha / 2, discordant, 0.5).astype(int)
    cutoff -= binom.cdf(cutoff, discordant, 0.5) > alpha / 2
    # Only rejection in the hypothesized direction supports a reduction in FPR.
    rejection = binom.sf(discordant - cutoff - 1, discordant, fixes / (fixes + regressions))
    return float(np.clip(np.dot(binom.pmf(discordant, n, fixes + regressions), rejection), 0, 1))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert directional_power(5, 1, 0, alpha=0.05) == 0
    assert directional_power(6, 1, 0, alpha=0.05) == 1
    rows = []
    for fixes, regressions in [(0.12, 0.02), (0.075, 0.025), (0.065, 0.035)]:
        rows.append(dict(hypothetical_fp_to_tn=fixes, hypothetical_tn_to_fp=regressions,
                         hypothetical_net_fpr_reduction=fixes-regressions,
                         power_by_n={str(n): directional_power(n, fixes, regressions)
                                     for n in (100, 300, 500, 1000, 2000)}))
    document = dict(method='Exact unconditional power for two-sided McNemar, desired direction only',
                    per_test_alpha=0.05/6, correction='Conservative Bonferroni bound for six planned tests',
                    assumptions='Independent pairs; specified discordance probabilities; no campaign correlation',
                    observed_effects=False, recall_noninferiority_power_evaluated=False, scenarios=rows)
    Path(args.out).write_text(json.dumps(document, indent=2) + '\n')
    print(json.dumps(document))


if __name__ == '__main__':
    main()
