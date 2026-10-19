import sys
import unittest
from collections import defaultdict
from array import array
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from campaign_audit_graph import complete_forest, exposure_paths, covered_candidates
from campaign_fingerprints import similarity
from expansion_annotation import prepare


class CampaignAuditTests(unittest.TestCase):
    def test_identical_nonempty_code_links_even_without_shared_file_hashes(self):
        rows = [dict(id=i, reports=[], added_hashes=[], code_key='same') for i in 'abc']
        edges, _ = complete_forest(rows, dict.fromkeys('abc', 'a'),
                                  {'same': dict(total=1, counts={'x': 1})})
        self.assertEqual(len(edges), 2)
        self.assertTrue(all(e['criterion'] == 'dolos' and e['score'] == 1 for e in edges))

    def test_inverted_scores_equal_cached_dolos_with_repeated_tokens(self):
        fingerprints = [dict(counts={'a': 5, 'b': 2}, total=7),
                        dict(counts={'a': 1, 'c': 3}, total=4),
                        dict(counts={'b': 8, 'a': 4}, total=12),
                        dict(counts={}, total=0)]
        postings = defaultdict(lambda: array('I'))
        for index, row in enumerate(fingerprints):
            for token, count in row['counts'].items():
                postings[token].extend((index, count))
        for index, left in enumerate(fingerprints):
            covered = covered_candidates(left['counts'], postings, index)
            for other in range(index + 1, len(fingerprints)):
                right = fingerprints[other]
                observed = covered.get(other, 0) / (left['total'] + right['total'])
                self.assertEqual(observed, similarity(left, right))

    def test_annotation_queue_excludes_dev_and_hides_selection_metadata(self):
        reviews = [dict(id=i, name=i, subset='HN', signal_categories=[1],
                        pair_exposed=False, gold_label='not_a_human_label') for i in 'ab']
        splits = [dict(id='a', proposed_partition='hn-pending-annotation',
                       holdout_eligible=True, final=False, gold_label=None),
                  dict(id='b', proposed_partition='dev')]
        rows, forms = prepare(reviews, splits)
        self.assertEqual(rows, [dict(id='a', name='a')])
        self.assertIsNone(forms[0]['label'])
        self.assertEqual(forms[0]['status'], 'pending')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            prepare(reviews + reviews, splits)

    def test_mixed_transitive_path_has_verifiable_edges_to_exposure(self):
        rows = [dict(id='a', reports=['R'], added_hashes=[], code_key='empty'),
                dict(id='b', reports=['R'], added_hashes=['H'], code_key='empty'),
                dict(id='c', reports=[], added_hashes=['H'], code_key='left'),
                dict(id='d', reports=[], added_hashes=[], code_key='right')]
        fingerprints = {'empty': dict(total=0, counts={}),
                        'left': dict(total=2, counts={'shared': 1, 'left': 1}),
                        'right': dict(total=2, counts={'shared': 1, 'right': 1})}
        edges, _ = complete_forest(rows, dict.fromkeys('abcd', 'a'), fingerprints)
        self.assertEqual({e['criterion'] for e in edges}, {'reports', 'added_hashes', 'dolos'})
        path = exposure_paths(edges, {'a'}, {'d'})[0]
        self.assertEqual(path['exposed_item'], 'a')
        self.assertEqual(len(path['edge_indices']), 3)
        self.assertEqual(next(e['score'] for e in edges if e['criterion'] == 'dolos'), 0.5)

    def test_empty_code_cannot_certify_a_merge(self):
        rows = [dict(id=i, reports=[], added_hashes=[], code_key='empty') for i in 'ab']
        with self.assertRaisesRegex(ValueError, 'disconnected'):
            complete_forest(rows, dict.fromkeys('ab', 'a'), {'empty': dict(total=0, counts={})})

    def test_certificate_rejects_missing_ids_and_cross_group_exact_links(self):
        rows = [dict(id=i, reports=['R'], added_hashes=[], code_key='empty') for i in 'ab']
        with self.assertRaisesRegex(ValueError, 'exactly once'):
            complete_forest(rows, {'a': 'a'}, {})
        with self.assertRaisesRegex(ValueError, 'crosses'):
            complete_forest(rows, {'a': 'a', 'b': 'b'}, {})


if __name__ == '__main__':
    unittest.main()
