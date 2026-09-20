#!/usr/bin/env bash
set -euo pipefail
: "${VEINS_ROOT:?Run inside the matching opp_env Veins environment}"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir/src"
opp_makemake -f --make-so --deep \
  -I "$VEINS_ROOT/src" -L "$VEINS_ROOT/src" -l veins
make -j4 MODE=release
