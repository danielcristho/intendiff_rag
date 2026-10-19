import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1] / 'data/evaluation/mixed-validation-20261011'
spec = importlib.util.spec_from_file_location('mixed_summary', HERE / 'summarize.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def row(verdict):
    return {'json_valid': verdict is not None,
            'parsed': {'verdict': verdict} if verdict else None, 'finish_reason': 'stop',
            'usage': {'prompt_tokens': 10, 'completion_tokens': 5}, 'latency_ms': 20}


class MixedValidationTests(unittest.TestCase):
    def test_invalid_stays_in_source_recall_denominator(self):
        result = module.summarize([row('malicious'), row('benign'), row(None)], 'MAL')
        self.assertEqual(result['source_recall_proxy'], 1 / 3)
        self.assertEqual(result['invalid_as_malicious_proxy'], 2 / 3)
        self.assertEqual(result['invalid'], 1)

    def test_unlabelled_hn_never_becomes_fpr(self):
        result = module.summarize([row('malicious'), row('benign')], 'HN')
        self.assertIsNone(result['fpr'])
        self.assertNotIn('source_recall_proxy', result)
        self.assertEqual(result['positive'], 1)

    def test_prompt_parser_and_runner_are_identical_to_frozen_d85(self):
        old = HERE.parent / 'evidence-dev-20261001'
        for name in ('prompts.py', 'legacy_prompts.py', 'evidence.py', 'configs.py', 'run_batch.py'):
            self.assertEqual((HERE / name).read_bytes(), (old / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
