import itertools
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from paired_pvalues import exact_sign_flip, holm_adjust, paired_test


class PairedPvaluesTests(unittest.TestCase):
    def test_matches_exhaustive_sign_assignments_with_ties_and_cancellation(self):
        for ds in ([], [0, 0], [1], [1, -1], [2, 1, -1, 0], [3, -2, 2, 1, -1]):
            sums = [sum(s*d for s, d in zip(signs, ds))
                    for signs in itertools.product((-1, 1), repeat=len(ds))]
            expected = sum(abs(s) >= abs(sum(ds)) for s in sums) / len(sums)
            with self.subTest(differences=ds):
                self.assertEqual(exact_sign_flip(ds)['p_value'], expected)
                self.assertEqual(exact_sign_flip([-d for d in ds])['p_value'], expected)

    def test_singletons_match_exact_mcnemar_binomial_tail(self):
        for b, c in ((11, 2), (24, 5), (4, 4), (0, 7)):
            expected = min(1, 2*sum(math.comb(b+c, j) for j in range(min(b, c)+1))/2**(b+c))
            self.assertAlmostEqual(exact_sign_flip([1]*b + [-1]*c)['p_value'], expected)

    def test_clusters_are_flipped_together_and_invalid_is_benign(self):
        pairs = [dict(id=str(i), campaign='one-campaign') for i in range(4)]
        baseline = [dict(pair_id=str(i), verdict='benign', json_valid=True) for i in range(4)]
        variant = [dict(pair_id=str(i), verdict='malicious', json_valid=i != 3) for i in range(4)]
        result = paired_test(pairs, baseline, variant)
        self.assertEqual(result['variant_positive'], 3)
        self.assertEqual(result['delta_points'], 75)
        self.assertEqual(result['p_value'], 1)
        self.assertEqual(result['n_clusters'], 1)
        self.assertEqual(exact_sign_flip([1, 1, 1])['p_value'], 0.25)

    def test_duplicate_missing_and_error_predictions_rejected(self):
        pairs = [dict(id='a', campaign='x'), dict(id='b', campaign='y')]
        rows = [dict(pair_id=p['id'], verdict='benign', json_valid=True) for p in pairs]
        for bad in (rows[:1], [rows[0], rows[0]], [dict(rows[0], error='timeout'), rows[1]]):
            with self.assertRaises(ValueError):
                paired_test(pairs, rows, bad)

    def test_integer_counts_do_not_overflow_float_range(self):
        result = exact_sign_flip([1]*550 + [-1]*550)
        self.assertEqual(result['p_value'], 1)
        self.assertEqual(int(result['sign_assignments']), 2**1100)

    def test_holm_preserves_input_order_and_step_down_monotonicity(self):
        adjusted = holm_adjust([0.04, 0.0001, 0.03, 0.01])
        for actual, expected in zip(adjusted, [0.06, 0.0004, 0.06, 0.03]):
            self.assertAlmostEqual(actual, expected)
        self.assertEqual(holm_adjust([1, 0.9, 0.9]), [1, 1, 1])
        for invalid in ([], [float('nan')], [-0.1], [1.1]):
            with self.assertRaises(ValueError):
                holm_adjust(invalid)


if __name__ == '__main__':
    unittest.main()
