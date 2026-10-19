"""Run with python -m unittest discover -s tests -p test_full_method.py."""
import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from transformers import AutoTokenizer  # Load native extensions before temporary module isolation.

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'data/evaluation/full-method-20261012'


def load_modules():
    loaded = {}
    with patch.dict(sys.modules):
        for name in ('configs', 'legacy_prompts', 'evidence', 'prompts', 'common', 'run_batch', 'report'):
            spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
    return loaded


MODULES = load_modules()


class FullMethodTests(unittest.TestCase):
    def test_current_id_prompts_match_audited_development_implementation(self):
        source = ROOT / 'data/evaluation/mixed-validation-20261011'
        for name in ('prompts.py', 'legacy_prompts.py', 'configs.py', 'evidence.py'):
            self.assertEqual((source / name).read_bytes(), (HERE / name).read_bytes())

    def test_verifier_receives_both_verdicts_and_preserves_invalid_candidate(self):
        pair = json.loads((HERE / 'original-pairs.jsonl').read_text().splitlines()[0])
        for verdict in ('malicious', 'benign'):
            candidate = {'verdict': verdict, 'evidence_ids': ['D00001'], 'reason': 'candidate'}
            prompt = MODULES['prompts'].build('VERIFY-I', pair, candidate)[1]['content']
            self.assertTrue(prompt.endswith(json.dumps(candidate, ensure_ascii=False)))
        prior = {'parsed': None, 'raw': '{unfinished'}
        self.assertEqual(MODULES['run_batch'].candidate_for(prior), {'invalid_candidate_raw': '{unfinished'})

    def test_full_cohort_not_replaced_by_diagnostic_subset(self):
        pairs = MODULES['common'].read_rows(HERE / 'original-pairs.jsonl')
        self.assertEqual(len({p['id'] for p in pairs}), 973)
        self.assertEqual(sum(p['label'] == 'malicious' for p in pairs), 873)
        models = json.loads((HERE / 'models.json').read_text())
        self.assertEqual(len(models), 7)
        for model in models:
            with self.assertRaises(AssertionError):
                MODULES['report'].summarize(model, pairs, [])

    def test_resume_rejects_duplicate_wrong_experiment_and_failed_requests(self):
        model = {'id': 'local'}
        row = {'pair_id': 'p', 'arm': 'IDS-I', 'model': 'local', 'experiment_id': HERE.name}
        for rows in ([row, row], [dict(row, experiment_id='old')], [dict(row, transport_error='timeout')]):
            with self.assertRaises((AssertionError, RuntimeError)):
                MODULES['common'].validate_rows(rows, model, [{'id': 'p'}])

    def test_length_limited_schema_shaped_output_remains_invalid(self):
        raw = json.dumps({'verdict': 'malicious', 'evidence_ids': ['D00001'], 'reason': 'test'})
        self.assertEqual(MODULES['run_batch'].parse(raw, 'length', 'IDS-I'), (None, 'length'))
        self.assertIsNotNone(MODULES['run_batch'].parse(raw, 'stop', 'IDS-I')[0])


if __name__ == '__main__':
    unittest.main()
