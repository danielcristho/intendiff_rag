#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
exec "$ROOT/.venv/bin/python" -u data/evaluation/source-rag-v3-20261015/code/source_experiment.py \
  --release data/evaluation/source-rag-v3-20261015 --stage "${1:?usage: run.sh dev|test}"
