import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'data/evaluation/dependency-context-20261011'


def load(path, name):
    with patch.dict(sys.modules), patch.object(sys, 'path', [str(path.parent), *sys.path]):
        for dependency in ('configs', 'prompts', 'base_prompts', 'legacy_prompts', 'evidence'):
            sys.modules.pop(dependency, None)
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


class DependencyContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load(ROOT / 'pipeline/runner.py', 'guard_test_runner')
        cls.prompt = load(HERE / 'prompts.py', 'context_test_prompts')
        cls.pairs = [json.loads(line) for line in (HERE / 'pairs.jsonl').open()]
        cls.snapshots = json.loads((HERE / 'context-snapshots.json').read_text())

    def test_target_and_related_cards_are_excluded_but_unrelated_cards_remain(self):
        pair = {'name': 'target', 'campaign': 'one',
                'delta_evidence': {'dependency_change': [{'dependency': 'dep'}]},
                'retrieval_exclude_names': ['transitive-dep']}
        for card in ({'name': 'target'}, {'campaign': 'one'},
                     {'name': 'dep', 'campaign': 'two'}, {'name': 'transitive-dep'}):
            self.assertFalse(self.runner.eligible(pair, card))
        self.assertTrue(self.runner.eligible(pair, {'name': 'unrelated', 'campaign': 'two'}))
        self.assertTrue(self.runner.eligible({'name': 'target'}, {'name': 'unrelated'}))

    def test_all_real_dependency_cards_are_blocked_across_cluster_boundaries(self):
        versions = json.loads((HERE / 'dependency-audit.json').read_text())['dependency_versions']
        for pair in self.pairs:
            for card in versions:
                self.assertNotEqual(pair['name'], card['name'])
                self.assertNotEqual(pair['campaign'], card['campaign'])
                self.assertFalse(self.runner.eligible(pair, card))

    def test_context_preserves_files_and_ids_without_target_collisions(self):
        for pair in self.pairs:
            target_ids = {r['id'] for r in self.prompt.index_diff(pair['diff'])}
            for snapshot in self.snapshots.values():
                records = self.prompt.context_records(pair, snapshot)
                context_ids = {r['id'] for r in records}
                self.assertEqual(len(records), len(context_ids))
                self.assertFalse(target_ids & context_ids)
                for filename, raw in snapshot['files'].items():
                    self.assertEqual([r['text'] for r in records if r['path'] == filename], raw.splitlines())
                result = self.prompt.audit(pair, snapshot, [records[-1]['id'], 'D99999'])
                self.assertEqual(result['unknown_ids'], ['D99999'])
                self.assertEqual(result['dependency_citations'], 1)
                self.assertFalse(result['semantic_support_verified'])

    def test_labels_and_audit_metadata_cannot_enter_prompt(self):
        pair = self.pairs[0]
        changed = copy.deepcopy(pair)
        changed.update(label='SECRET_LABEL', subset='SECRET_SUBSET', campaign='SECRET_CAMPAIGN',
                       source_label='SECRET_SOURCE', retrieval_exclude_names=['SECRET_EXCLUSION'])
        for snapshot in self.snapshots.values():
            messages = self.prompt.build(pair, snapshot)
            self.assertEqual(messages, self.prompt.build(changed, snapshot))
            base = self.prompt.base_build('IDS-I', pair)
            self.assertEqual(messages[0], base[0])
            self.assertTrue(messages[1]['content'].startswith(base[1]['content'] + '\n\n' + self.prompt.INTRO))
            self.assertEqual(set(snapshot), {'name', 'version', 'files'})


if __name__ == '__main__':
    unittest.main()
