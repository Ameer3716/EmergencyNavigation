#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 "$project_dir/scripts/run_batch.py" --densities medium high --seed-start 1 --seed-end 1 --force
