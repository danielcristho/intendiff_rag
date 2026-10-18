#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
scripts/source-rag/run.sh test
exec "$ROOT/.venv/bin/python" data/evaluation/source-rag-v3-20261015/code/source_report.py \
  --release data/evaluation/source-rag-v3-20261015
