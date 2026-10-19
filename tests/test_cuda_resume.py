import contextlib
import io
import runpy
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scratchpad/cuda-recovery-20261001/resume.py'


class CudaResumeTests(unittest.TestCase):
    def test_failed_probe_never_starts_inference(self):
        failure = subprocess.CompletedProcess([], -11, 'loaded', '')
        with patch('subprocess.run', return_value=failure) as run:
            with patch.object(Path, 'write_text'), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    runpy.run_path(str(SCRIPT))
            self.assertEqual(run.call_count, 1)

    def test_successful_probe_launches_only_frozen_evaluator(self):
        success = subprocess.CompletedProcess([], 0, 'cuInit: 0', '')
        with patch('subprocess.run', return_value=success) as run:
            with patch.object(Path, 'write_text'), contextlib.redirect_stdout(io.StringIO()):
                runpy.run_path(str(SCRIPT))
            self.assertEqual(run.call_count, 2)
            command = run.call_args.args[0]
            self.assertEqual(command[-1], str(ROOT / 'data/evaluation/evidence-dev-20261001/evaluate.py'))
            self.assertTrue(run.call_args.kwargs['check'])

    def test_probe_timeout_never_starts_inference(self):
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired('probe', 60)) as run:
            with patch.object(Path, 'write_text'), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit):
                    runpy.run_path(str(SCRIPT))
            self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
