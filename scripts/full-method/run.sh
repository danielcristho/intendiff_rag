#!/usr/bin/env bash
# run.sh resumes D92 for the named models, or every unfinished one with --all,
# in the frozen protocol order; stops at the first model that fails.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ORDER=(qwen3 qwen25 qwen25_7b qwen3_8b phi4_mini llama31_8b granite33_8b)
usage() { echo "usage: $0 --all | TAG [TAG ...]   (tags: ${ORDER[*]})" >&2; exit 2; }
[ $# -gt 0 ] || usage
if [ "$1" = "--all" ]; then
  [ $# -eq 1 ] || usage
  TAGS=("${ORDER[@]}")
else
  TAGS=("$@")
  for t in "${TAGS[@]}"; do [[ " ${ORDER[*]} " == *" $t "* ]] || usage; done
fi
for t in "${TAGS[@]}"; do
  "$HERE/_run_one.sh" "$t" || { echo "Stopped: $t failed; later models not started." >&2; exit 1; }
done
"$HERE/status.sh"
