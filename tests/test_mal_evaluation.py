import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from mal_eval_prepare import check_candidates
from mal_eval_metrics import campaign_recall, combined_metrics


class MalEvaluationTests(unittest.TestCase):
    def test_holdout_requires_unique_ids_and_frozen_campaign_count(self):
        pairs = [dict(id=str(i), campaign=str(i % 65), label='malicious', subset='MAL') for i in range(96)]
        check_candidates(pairs)
        pairs[-1]['id'] = pairs[0]['id']
        with self.assertRaisesRegex(ValueError, 'unique'):
            check_candidates(pairs)

    def test_campaign_resampling_keeps_related_pairs_together(self):
        pairs = [dict(id='a', campaign='one'), dict(id='b', campaign='one'), dict(id='c', campaign='two')]
        rows = [dict(pair_id='a', verdict='malicious', json_valid=True),
                dict(pair_id='b', verdict='malicious', json_valid=True),
                dict(pair_id='c', verdict=None, json_valid=False)]
        result = campaign_recall(pairs, rows, 'benign', resamples=1000)
        self.assertEqual(result['tpr'], 2 / 3)
        self.assertEqual(result['macro_campaign_tpr'], 0.5)
        self.assertEqual(result['campaign_bootstrap_95'], [0., 1.])
        self.assertEqual(campaign_recall(pairs, rows, 'malicious', 1000)['tpr'], 1.)
        with self.assertRaisesRegex(ValueError, 'complete unique'):
            campaign_recall(pairs, rows[:-1], 'benign')

    def test_combination_reuses_historical_negatives_without_duplicating_them(self):
        result = combined_metrics(dict(TP=19, FN=14, TN=1768, FP=100), dict(TP=48, FN=48))
        self.assertEqual(result['confusion'], dict(TP=67, FN=62, TN=1768, FP=100))
        self.assertAlmostEqual(result['historical_typ_fpr'], 100 / 1868)
        self.assertAlmostEqual(result['balanced_accuracy'], (67 / 129 + 1768 / 1868) / 2)
        with self.assertRaisesRegex(ValueError, '129 MAL'):
            combined_metrics(dict(TP=19, FN=14, TN=1768, FP=100), dict(TP=47, FN=48))


if __name__ == '__main__':
    unittest.main()
