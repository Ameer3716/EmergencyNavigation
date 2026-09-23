#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
clang++ -std=c++17 -O2 -I "$project_dir/src" \
  "$project_dir/tests/routing_test.cc" \
  "$project_dir/src/routing/RoadGraph.cc" \
  "$project_dir/src/routing/AStarRouter.cc" \
  -o "$project_dir/tests/routing_test"
"$project_dir/tests/routing_test" "$project_dir/simulations/grid/grid.net.xml"
