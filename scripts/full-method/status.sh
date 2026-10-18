#!/usr/bin/env bash
# status.sh prints how many of the 2,919 generations per model exist and the last driver stage.
DIR="$(cd "$(dirname "$0")/../.." && pwd)/data/evaluation/full-method-20261012"
for t in qwen3 qwen25 qwen25_7b qwen3_8b phi4_mini llama31_8b granite33_8b; do
  n=$( [ -f "$DIR/$t.results.jsonl" ] && grep -c . "$DIR/$t.results.jsonl" || echo 0 )
  v=$( [ -f "$DIR/$t.verification.json" ] && echo verified || echo - )
  printf '%-14s %5s/2919  %s\n' "$t" "$n" "$v"
done
python3 -c "import json;s=json.load(open('$DIR/status.json'));print('last stage:',s['stage'],s.get('model',''),s.get('error',''))"
