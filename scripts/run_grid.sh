#!/usr/bin/env bash
set -euo pipefail
: "${VEINS_ROOT:?Run this script inside the matching opp_env Veins environment}"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config="${1:-Smoke}"
cd "$project_dir/simulations/grid"
log_file="$project_dir/artifacts/logs/grid-${config}-stdout.txt"
opp_run -u Cmdenv -c "$config" \
  -n "$VEINS_ROOT/src/veins:$project_dir/src" \
  -l "$VEINS_ROOT/src/veins" \
  -l "$project_dir/src/out/clang-release/src" \
  -f omnetpp.ini > "$log_file" 2>&1
tail -n 12 "$log_file"
