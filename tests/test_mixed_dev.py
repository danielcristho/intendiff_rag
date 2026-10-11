import unittest

from pipeline.annotation_readiness import assess, decision_issues
from pipeline.mixed_dev import blinded_pair, select_malicious_candidates


DIFF = '--- a/x.js\n+++ b/x.js\n@@ -1 +1 @@\n-old\n+new'


def pair(identifier, campaign):
    return {'id': identifier, 'name': identifier, 'campaign': campaign, 'subset': 'MAL',
            'diff': DIFF, 'diff_sha256': identifier, 'diff_tokens': 20, 'truncated': False}


class MixedDevTests(unittest.TestCase):
    def test_selection_is_order_independent_and_caps_campaigns(self):
        rows = [pair('a', 'one'), pair('b', 'one'), pair('c', 'two'), pair('d', 'three')]
        first, _ = select_malicious_candidates(rows, [], 3)
        second, _ = select_malicious_candidates(rows[::-1], [], 3)
        self.assertEqual(first, second)
        self.assertEqual(len({p['campaign'] for p in first}), 3)
        with self.assertRaises(ValueError):
            select_malicious_candidates(rows, [], 4)

    def test_selection_excludes_shared_package_diff_and_archive(self):
        existing = {**pair('used', 'old'), 'sha256_after': 'archive'}
        rows = [{**pair('a', 'one'), 'name': 'used'},
                {**pair('b', 'two'), 'diff_sha256': 'used'},
                {**pair('c', 'three'), 'sha256_before': 'archive'}, pair('d', 'four')]
        selected, _ = select_malicious_candidates(rows, [existing], 1)
        self.assertEqual([p['id'] for p in selected], ['d'])

    def test_blinded_projection_excludes_source_and_predictions(self):
        source = {**pair('a', 'one'), 'label': 'MAL', 'pred': 'malicious', 'source': 'database',
                  'gold_evidence': ['+new'], 'signal_categories': [1]}
        blind = blinded_pair(source, 'review-001')
        self.assertTrue(blind['annotation_blinded'])
        for key in ('subset', 'campaign', 'label', 'pred', 'source', 'gold_evidence', 'signal_categories'):
            self.assertNotIn(key, blind)

    def test_matching_header_or_paraphrase_is_not_acceptable_changed_evidence(self):
        for evidence in [['+++ b/x.js'], ['+paraphrase']]:
            self.assertTrue(decision_issues(pair('a', 'one'),
                {'label': 'malicious', 'note': 'source reference', 'gold_evidence': evidence}))
        self.assertEqual(decision_issues(pair('a', 'one'),
            {'label': 'malicious', 'note': 'source reference', 'gold_evidence': ['+new']}), [])

    def test_missing_disagreeing_skip_and_matching_votes_never_auto_export_gold(self):
        rows = [pair('a', 'one')]
        mapping = [{'review_id': 'review-001', 'pair_id': 'a'}]
        benign = {'label': 'benign', 'note': 'verified reference'}
        malicious = {'label': 'malicious', 'note': 'verified reference', 'gold_evidence': ['+new']}
        cases = [(None, 'incomplete'), (malicious, 'label_disagreement'),
                 ({'label': 'skip', 'note': 'insufficient context'}, 'skip_requires_review'),
                 (benign, 'agreement_requires_semantic_review')]
        for other, state in cases:
            report = assess(rows, mapping, {'alice': {'review-001': benign},
                                            'bob': {'review-001': other}})
            self.assertEqual(report['counts'], {state: 1})
            self.assertFalse(report['gold_ready'])
        with self.assertRaises(ValueError):
            assess(rows, mapping, {'alice': {}})

    def test_hn_category_must_be_integer_and_agreed(self):
        hn = {**pair('a', 'one'), 'subset': 'HN'}
        vote = {'label': 'benign', 'note': 'purpose reference', 'category': True}
        self.assertIn('missing_hn_purpose_category', decision_issues(hn, vote))
        report = assess([hn], [{'review_id': 'r', 'pair_id': 'a'}],
                        {'alice': {'r': {**vote, 'category': 1}}, 'bob': {'r': {**vote, 'category': 2}}})
        self.assertEqual(report['counts'], {'category_disagreement': 1})


if __name__ == '__main__':
    unittest.main()
