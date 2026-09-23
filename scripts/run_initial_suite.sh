#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for config in FogCloudAStar MistAStar MistDynamicAStar MistDynamicFogFallback ForcedMistFailure; do
    echo "Running ${config}"
    "$project_dir/scripts/run_grid.sh" "$config"
    for extension in sca vec vci; do
        result="$project_dir/simulations/grid/results/${config}-#0.${extension}"
        if [[ -f "$result" ]]; then
            cp "$result" "$project_dir/results/raw/${config}-seed1.${extension}"
        fi
    done
done
