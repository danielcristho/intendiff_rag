import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from source_freeze import normalized_cohort


class NormalizationReleaseTests(unittest.TestCase):
    def test_missing_successful_or_unrecorded_pairs_cannot_be_excluded(self):
        manifest = [dict(id='a'), dict(id='b')]
        attempts = [dict(id='a'), dict(id='b', error='TimeoutExpired: limit')]
        for rows, exclusions in [(attempts[:1], []), (attempts, []),
                                  ([dict(id='a'), dict(id='b')], [dict(id='b')])]:
            with self.assertRaises(ValueError):
                normalized_cohort(manifest, rows, exclusions)

    def test_repeated_timeout_requires_matching_explicit_record(self):
        manifest = [dict(id='a'), dict(id='b')]
        failed = dict(id='b', error='TimeoutExpired: limit')
        exclusion = dict(id='b', reason='normalization_timeout_after_retry', last_error=failed['error'])
        with self.assertRaises(ValueError):
            normalized_cohort(manifest, [dict(id='a'), failed], [exclusion])
        eligible, _ = normalized_cohort(manifest, [dict(id='a'), failed, failed], [exclusion])
        self.assertEqual(eligible, [dict(id='a')])
        with self.assertRaises(ValueError):
            normalized_cohort(manifest, [dict(id='a'), failed, failed], [dict(exclusion, last_error='other')])


if __name__ == '__main__':
    unittest.main()
