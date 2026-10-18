import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
import runner
from configs import CONFIGS
from final_readiness import assess
from retrieval_audit import audit_retrieval


class FinalReadinessTests(unittest.TestCase):
    def setUp(self):
        self.pair = dict(id='target@2', name='target', campaign='target-campaign', delta=['network'])
        self.cards = [dict(id=i, name=i, campaign=i, label=label, delta=['network'])
                      for i, label in [('m1', 'malicious'), ('m2', 'malicious'), ('b1', 'benign')]]

    def test_full_contrasts_preserve_anchor_and_intent_independent_retrieval(self):
        pairs = [dict(self.pair, id=f'target@{n}') for n in range(20)]
        issues, plan = audit_retrieval(pairs, self.cards, list(CONFIGS), runner.retrieve)
        self.assertFalse(issues)
        self.assertEqual(len(plan), 120)
        for pair in pairs:
            selected = {r['config']: r['card_ids'] for r in plan if r['pair_id'] == pair['id']}
            self.assertEqual(selected['DIFF+I+MB'], selected['DIFF+MB'])
            malicious = next(i for i in selected['DIFF+I+MB'] if i.startswith('m'))
            self.assertEqual(selected['DIFF+I+MM'].index(malicious), selected['DIFF+I+MB'].index(malicious))

    def test_filtering_can_make_a_nonempty_kb_insufficient(self):
        pair = dict(self.pair, retrieval_exclude_names=['m2'])
        issues, _ = audit_retrieval([pair], self.cards, list(CONFIGS), runner.retrieve)
        self.assertTrue(any(r.get('config') == 'DIFF+I+MM' for r in issues))

    def test_duplicates_and_missing_campaign_cannot_pass(self):
        for cards in (self.cards + self.cards[:1], [dict(c, campaign=None) for c in self.cards]):
            issues, plan = audit_retrieval([self.pair], cards, list(CONFIGS), runner.retrieve)
            self.assertTrue(issues)
            self.assertFalse(plan)

    def test_runner_rejects_thin_pool_before_network_or_result_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'pairs').write_text(json.dumps(self.pair) + '\n')
            (root / 'kb').write_text(json.dumps(self.cards[0]) + '\n')
            with patch.object(runner, 'call_llm') as call:
                with self.assertRaisesRegex(SystemExit, 'retrieval preflight failed'):
                    runner.main(['--model', 'fixture', '--pairs', str(root / 'pairs'),
                                 '--kb', str(root / 'kb'), '--out', str(root / 'results')])
                call.assert_not_called()
            self.assertFalse((root / 'results').exists())

    def test_readiness_never_promotes_exposed_candidates_or_boolean_gold_to_release(self):
        row = dict(self.pair, subset='HN', label='benign', before='1', intent_from='1',
                   evaluation_scope='candidate', human_annotation_verified=True)
        report = assess([row], self.cards, [dict(id=row['id'], name=row['name'])])
        reasons = {r['reason'] for r in report['issues']}
        self.assertIn('development_exposure', reasons)
        self.assertIn('not_declared_final_holdout', reasons)
        self.assertIn('missing_hn_category', reasons)
        self.assertFalse(report['launch_ready'])

    def test_changed_intent_retrieval_is_detected(self):
        def broken(config, pair, kb):
            cards = runner.retrieve(config, pair, kb)
            return list(reversed(cards)) if config == 'DIFF+MB' else cards
        issues, _ = audit_retrieval([self.pair], self.cards, list(CONFIGS), broken)
        self.assertTrue(any(r['reason'] == 'intent_changes_retrieval' for r in issues))


if __name__ == '__main__':
    unittest.main()
