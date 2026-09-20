#!/usr/bin/env bash
set -euo pipefail
: "${SUMO_HOME:?Set SUMO_HOME to the SUMO 1.18.0 installation directory}"
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$SUMO_HOME/bin/netgenerate" \
  --grid --grid.number 4 --grid.length 300 \
  --default-junction-type traffic_light \
  --default.speed 13.89 --default.lanenumber 1 \
  --no-turnarounds \
  --output-file "$project_dir/simulations/grid/grid.net.xml"
