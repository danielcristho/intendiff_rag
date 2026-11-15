#!/bin/bash
# Resume the D111 batch; after a failure, re-encode unreadable result files and retry (max 3).
cd ~/intendiff_rag
R=data/evaluation/sampling-ablation-20261109
.venv/bin/python $R/recovery/evict_cache.py $$ $R data/evaluation/source-rag-v3-20261015 \
  data/evaluation/source-rag-mal-20261018 data/upstream/models \
  "$HOME/.cache/huggingface/hub/models--Qwen--Qwen2.5-Coder-3B-Instruct" &
for attempt in 1 2 3 4; do
  .venv/bin/python $R/recovery/reencode.py $R $R/recovery
  .venv/bin/python -u pipeline/sampling_batch.py --release $R && exit 0
  echo "resume.sh: batch exited non-zero (attempt $attempt)"
done
exit 1
