import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'data/evaluation/evidence-dev-20261001'


class DevelopmentPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(HERE))
        spec = importlib.util.spec_from_file_location('evidence_dev_prompts', HERE / 'prompts.py')
        cls.prompts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.prompts)
        cls.pair = {'id': 'not-in-prompt', 'name': 'hidden-name', 'label': 'malicious',
                    'subset': 'HN', 'before': '1', 'after': '2',
                    'intent': {'description': 'A color detector.'},
                    'diff': '@@ -1 +1 @@\n-old\n+new'}

    def test_decoder_control_has_identical_messages(self):
        self.assertEqual(self.prompts.build('LEGACY-I', self.pair),
                         self.prompts.build('SCHEMA-I', self.pair))

    def test_intent_ablation_does_not_leak_labels_or_identity(self):
        without = self.prompts.build('IDS-D', self.pair)[1]['content']
        with_intent = self.prompts.build('IDS-I', self.pair)[1]['content']
        self.assertNotIn('A color detector.', without)
        self.assertIn('A color detector.', with_intent)
        for content in [without, with_intent]:
            self.assertNotIn('hidden-name', content)
            self.assertNotIn('not-in-prompt', content)
            self.assertNotIn('HN', content)

    def test_verifier_accepts_both_classes_without_automatic_relabeling(self):
        for verdict in ['malicious', 'benign']:
            candidate = {'verdict': verdict, 'evidence_ids': ['D00003'], 'reason': 'A hypothesis.'}
            text = self.prompts.build('VERIFY-I', self.pair, candidate)[1]['content']
            self.assertIn('untrusted hypothesis', text)
            self.assertIn('change either verdict', text)
            self.assertIn('A hypothesis.', text)


if __name__ == '__main__':
    unittest.main()
