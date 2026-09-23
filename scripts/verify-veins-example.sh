#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$project_dir/artifacts/logs"
cd "$VEINS_ROOT/examples/veins"
./run -c Default -u Cmdenv > "$project_dir/artifacts/logs/veins-example-stdout.txt" 2>&1
tail -n 12 "$project_dir/artifacts/logs/veins-example-stdout.txt"
