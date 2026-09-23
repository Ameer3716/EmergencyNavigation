#!/usr/bin/env bash
set -euo pipefail
: "${VEINS_ROOT:?Run this script inside the matching opp_env Veins environment}"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config="${1:-${EN_CONFIG:-Smoke}}"
library=""
for candidate in "$project_dir/src/out/clang-release/src" "$project_dir/src/out/gcc-release/src"; do
  if [[ -f "$(dirname "$candidate")/libsrc.so" ]]; then
    library="$candidate"
    break
  fi
done
if [[ -z "$library" ]]; then
  echo "Missing libsrc.so; run bash scripts/build.sh first" >&2
  exit 1
fi
mkdir -p "$project_dir/artifacts/logs"
cd "$project_dir/simulations/grid"
log_file="$project_dir/artifacts/logs/grid-${config}-stdout.txt"
opp_run -u Cmdenv -c "$config" \
  -n "$VEINS_ROOT/src/veins:$project_dir/src" \
  -l "$VEINS_ROOT/src/veins" \
  -l "$library" \
  -f omnetpp.ini > "$log_file" 2>&1
tail -n 12 "$log_file"
