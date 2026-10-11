#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v clang++ >/dev/null 2>&1; then
  for candidate in /nix/store/*-clang-wrapper-19.1.7/bin; do PATH="$candidate:$PATH"; break; done
  for candidate in /nix/store/*-lld-19.1.7/bin; do PATH="$candidate:$PATH"; break; done
  export PATH
fi
clang++ -std=c++17 -O2 -I "$project_dir/src" \
  "$project_dir/tests/routing_test.cc" \
  "$project_dir/src/routing/RoadGraph.cc" \
  "$project_dir/src/routing/AStarRouter.cc" \
  -o "$project_dir/tests/routing_test"
"$project_dir/tests/routing_test" "$project_dir/simulations/grid/grid.net.xml"
