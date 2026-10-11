"""Save the completed D85 artifact manifest, retaining the preparation manifest."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'data/evaluation/evidence-dev-20261001'
verification = json.loads((HERE / 'verification.json').read_text())
assert verification['completed_inference'] and verification['actual_generations'] == 160
status = json.loads((HERE / 'status.json').read_text())
assert status['stage'] == 'complete'
manifest = HERE / 'artifact-manifest.json'
archived = HERE / 'artifact-manifest.pre-run.json'
if not archived.exists():
    shutil.copyfile(manifest, archived)
notes = {'complete': True, 'decision': 'D85', 'new_llm_calls': 160,
         'completed_unix': status['unix'], 'model_server_stopped': True,
         'prior_failure': 'CUDA SIGSEGV before any generation, retained in server.log',
         'recovery': 'CUDA probe and tensor operation succeeded after user-authorized WSL restart',
         'inference_protocol_changed': False, 'gold_labels_created': False,
         'accuracy_claim': None,
         'findings': ['Schema validity 29/32 to 32/32 on this dev cohort',
                      'ID-format decisions all benign; no recall estimate available',
                      'Verifier retained all 32 candidate verdicts',
                      'Existing citation IDs do not establish semantic support'],
         'shutdown_note': 'One leaked semaphore cleanup warning after normal API shutdown'}
(HERE / 'execution-notes.json').write_text(json.dumps(notes, indent=2) + '\n')
files = [p for p in HERE.iterdir() if p.is_file() and p.name not in ['artifact-manifest.json', '.evaluation.lock']]
files += [p for p in Path(__file__).resolve().parent.iterdir() if p.is_file()]
files += [ROOT / name for name in ['docs/evidence-dev-results-20261001.md',
          'docs/evidence-dev-status-20261001.md', 'docs/cuda-recovery-20261001.md',
          'pipeline/evidence.py', 'tests/test_evidence.py', 'tests/test_evidence_dev.py',
          'tests/test_cuda_resume.py']]
hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(files))}
manifest.write_text(json.dumps({'stage': 'complete', 'generations': 160, 'sha256': hashes}, indent=2) + '\n')
assert all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == h for name, h in hashes.items())
print(json.dumps({'complete': True, 'verified_artifact_count': len(hashes)}))
