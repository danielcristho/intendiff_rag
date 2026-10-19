#!/usr/bin/env bash
# _run_one.sh TAG resumes the frozen D92 batch for one model through the official
# run_model, so pins, token checks and verification match run_all.
set -euo pipefail
TAG="${1:?usage: _run_one.sh MODEL_TAG}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="$ROOT/data/evaluation/full-method-20261012"
cd "$DIR"
exec 9>>"$DIR/.evaluation.lock"
flock -n 9 || { echo "Another evaluation holds $DIR/.evaluation.lock; not starting." >&2; exit 1; }
echo "[$(date -Is)] start $TAG" | tee -a "$DIR/$TAG.run.log"
"$ROOT/.venv/bin/python" - "$TAG" <<'PY' 2>&1 | tee -a "$DIR/$TAG.run.log"
import json, signal, sys
from evaluate import run_model, status, HERE
from report import report

def interrupted(signum, frame):
    raise KeyboardInterrupt(signum)
signal.signal(signal.SIGTERM, interrupted)

tag = sys.argv[1]
protocol = json.loads((HERE / 'protocol.json').read_text())
model = next((m for m in protocol['models'] if m['tag'] == tag), None)
if model is None:
    sys.exit(f"unknown tag {tag}; frozen tags: {[m['tag'] for m in protocol['models']]}")
try:
    run_model(protocol, model)
except BaseException as error:
    status('error', model=model['id'], error=repr(error))
    raise
result = report()
print(json.dumps({'model': model['id'], 'model_complete': True,
                  'verification': f"{tag}.verification.json",
                  'all_models_complete': result.get('complete')}))
PY
echo "[$(date -Is)] end $TAG" | tee -a "$DIR/$TAG.run.log"
