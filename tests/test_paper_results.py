import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from paper_results import CONFIGS, checked_rows, confusion


class PaperResultsTests(unittest.TestCase):
    def test_invalid_policy_changes_both_error_types(self):
        rows = [dict(config='DIFF', label=label, verdict=None, json_valid=False)
                for label in ('malicious', 'benign')]
        self.assertEqual(confusion(rows, 'DIFF', 'benign'), dict(TP=0, FN=1, TN=1, FP=0))
        self.assertEqual(confusion(rows, 'DIFF', 'malicious'), dict(TP=1, FN=0, TN=0, FP=1))

    def test_duplicate_response_cannot_replace_a_missing_configuration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'test.pairs.jsonl').write_text(json.dumps(dict(id='p', label='malicious', diff_sha256='x'))+'\n')
            rows = [dict(pair_id='p', config=c, model='m', label='malicious', diff_sha256='x', json_valid=True)
                    for c in CONFIGS]
            (root/'test.m.verification.json').write_text(json.dumps(dict(complete=True, completed=6, json_validity=1)))
            def save():
                (root/'test.m.results.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            save()
            checked_rows(root, 'm', 'm')
            rows[-1] = rows[0]
            save()
            with self.assertRaisesRegex(ValueError, 'Incomplete or duplicate'):
                checked_rows(root, 'm', 'm')


if __name__ == '__main__':
    unittest.main()
