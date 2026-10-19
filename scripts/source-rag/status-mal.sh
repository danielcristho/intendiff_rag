#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
exec "$ROOT/.venv/bin/python" pipeline/mal_eval_status.py \
  --out data/evaluation/source-rag-mal-20261018
