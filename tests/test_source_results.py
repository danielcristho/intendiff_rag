import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from configs import CONFIGS
from runner import build, request_hash, retrieve, retrieval_log, run_key
from source_results import verify


class SourceResultsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.model = dict(id='fixture', tag='fixture')
        self.pair = dict(id='target@2', name='target', campaign='c', subset='MAL', label='malicious', diff_sha256='diff')
        self.cards = [dict(id=n, name=n, campaign=n, label=label) for n, label in
                      [('m1', 'malicious'), ('m2', 'malicious'), ('b1', 'benign')]]
        self.write('dev.pairs.jsonl', [self.pair])
        self.write('kb.jsonl', self.cards)
        self.write('dev.prompt-tokens.jsonl', [dict(model='fixture', pair_id='target@2', config=c, prompt_tokens=10) for c in CONFIGS])
        self.rows = [dict(model='fixture', pair_id='target@2', config=c, seed=0, temperature=0.0,
                          top_p=1.0, top_k=None, label='malicious', diff_sha256='diff',
                          run_key=run_key('fixture', c, 'target@2', 0, 0.0),
                          cards=retrieval_log(self.pair, retrieve(c, self.pair, self.cards)),
                          prompt_tokens=10, completion_tokens=8, raw='{"verdict":"malicious","evidence":[],"reason":"r"}',
                          verdict='malicious', evidence=[], reason='r', json_valid=True, finish_reason='stop') for c in CONFIGS]
        for index, row in enumerate(self.rows):
            row.update(response_id=f'response-{index}', response_model='fixture',
                request_sha256=request_hash('fixture', build(row['config'], self.pair,
                    retrieve(row['config'], self.pair, self.cards)), 0, dict(temperature=0.0, top_p=1.0)))

    def write(self, name, rows):
        (self.root / name).write_text(''.join(json.dumps(r) + '\n' for r in rows))

    def test_complete_matrix_is_checked_and_partial_results_are_not_complete(self):
        self.write('dev.fixture.results.jsonl', self.rows[:-1])
        self.assertFalse(verify(self.root, 'dev', self.model)['complete'])
        self.write('dev.fixture.results.jsonl', self.rows)
        result = verify(self.root, 'dev', self.model)
        self.assertTrue(result['complete'])
        self.assertEqual(result['completed'], 6)
        self.assertEqual(result['groups'][0]['tpr_source'], 1)

    def test_duplicate_generations_and_changed_retrieval_fail(self):
        self.write('dev.fixture.results.jsonl', self.rows + self.rows[:1])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            verify(self.root, 'dev', self.model)
        self.rows[-1]['cards'] = []
        self.write('dev.fixture.results.jsonl', self.rows)
        with self.assertRaisesRegex(ValueError, 'retrieval differs'):
            verify(self.root, 'dev', self.model)

    def test_guided_schema_and_request_identity_cannot_be_silently_dropped(self):
        self.rows[0]['request_sha256'] = 'different'
        self.write('dev.fixture.results.jsonl', self.rows)
        with self.assertRaisesRegex(ValueError, 'Request or response identity'):
            verify(self.root, 'dev', self.model)

    def test_truncation_counts_as_invalid_even_when_raw_json_parses(self):
        self.rows[0].update(finish_reason='length', json_valid=False)
        self.write('dev.fixture.results.jsonl', self.rows)
        result = verify(self.root, 'dev', self.model)
        self.assertEqual(result['groups'][0]['tpr_source'], 0)
        self.assertEqual(result['groups'][1]['tpr_source'], 1)

    def test_report_reproduces_known_confusion_and_paired_comparisons(self):
        benign = dict(self.pair, id='typ@2', name='typ', campaign='typ-c',
                      subset='TYP', group='random', label='benign')
        self.write('test.pairs.jsonl', [self.pair, benign])
        self.write('test.prompt-tokens.jsonl', [dict(model='fixture', pair_id=p['id'], config=c,
                   prompt_tokens=10) for p in (self.pair, benign) for c in CONFIGS])
        extra = []
        for row in self.rows:
            config = row['config']
            extra.append(dict(row, pair_id=benign['id'], label='benign',
                run_key=run_key('fixture', config, benign['id'], 0, 0.0),
                response_id=row['response_id'] + '-typ',
                cards=retrieval_log(benign, retrieve(config, benign, self.cards)),
                request_sha256=request_hash('fixture', build(config, benign,
                    retrieve(config, benign, self.cards)), 0, dict(temperature=0.0, top_p=1.0))))
        self.write('test.fixture.results.jsonl', self.rows + extra)
        (self.root / 'protocol.json').write_text(json.dumps(dict(models=[self.model], test_released=True)))
        subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] / 'pipeline/source_report.py'),
                        '--release', str(self.root)], check=True, capture_output=True)
        report = json.loads((self.root / 'summary.json').read_text())
        self.assertEqual(len(report['paired_comparisons']), 6)
        for metric in report['metrics']:
            self.assertEqual(metric['tpr_source'], 1)
            self.assertEqual(metric['cohort_accuracy'], 0.5)
            self.assertEqual(metric['balanced_accuracy'], 0.5)
            self.assertEqual(metric['typ_strata']['random']['fpr'], 1)
        self.assertTrue(all(r['alarm_rate_delta_points'] == 0 for r in report['paired_comparisons']))


if __name__ == '__main__':
    unittest.main()
