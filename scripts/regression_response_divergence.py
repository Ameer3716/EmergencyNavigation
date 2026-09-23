#!/usr/bin/env python3
"""Fail when a materially congested high-traffic seed collapses all responses."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")

def check_divergence(seeds=range(1, 6)):
    results_by_seed = {}
    dynamic_diffs = []
    mist_static_faster_or_equal = 0

    for seed in seeds:
        seed_vals = {}
        for config in CONFIGS:
            path = ROOT / "results/raw" / f"{config}-high-seed{seed}.sca"
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            match = re.search(r"scalar .*? evResponseTime ([0-9.eE+-]+)", text)
            if match:
                seed_vals[config] = float(match.group(1))
        if len(seed_vals) == len(CONFIGS):
            results_by_seed[seed] = seed_vals
            diff_dyn = abs(seed_vals["MistDynamicAStar"] - seed_vals["FogCloudAStar"])
            diff_fallback = abs(seed_vals["MistDynamicFogFallback"] - seed_vals["FogCloudAStar"])
            dynamic_diffs.append((seed, diff_dyn, diff_fallback))
            if seed_vals["MistAStar"] <= seed_vals["FogCloudAStar"]:
                mist_static_faster_or_equal += 1

    if not results_by_seed:
        raise SystemExit("No complete high-traffic seed results found")

    print(f"Evaluated {len(results_by_seed)} seeds: {results_by_seed}")

    # Condition 1: MistAStar and MistDynamicAStar should consistently match or beat FogCloud baseline (never slower)
    if mist_static_faster_or_equal < len(results_by_seed):
        raise SystemExit(f"Regression failed: MistAStar was slower than FogCloud on {len(results_by_seed) - mist_static_faster_or_equal} seeds")

    # Condition 2: MistDynamicAStar must match or beat FogCloud on all seeds
    mist_dynamic_faster_or_equal = sum(1 for d in dynamic_diffs if results_by_seed[d[0]]["MistDynamicAStar"] <= results_by_seed[d[0]]["FogCloudAStar"])
    if mist_dynamic_faster_or_equal < len(results_by_seed):
        raise SystemExit(f"Regression failed: MistDynamicAStar was slower than FogCloud on {len(results_by_seed) - mist_dynamic_faster_or_equal} seeds")

    # Condition 3: Significant dynamic divergence (saving >= 2.0s over FogCloud) under congestion
    significant_divergence = [d for d in dynamic_diffs if d[1] >= 2.0 and d[2] >= 2.0]
    divergence_ratio = len(significant_divergence) / len(results_by_seed)
    print(f"Significant dynamic divergence (>=2.0s difference from FogCloud): {len(significant_divergence)}/{len(results_by_seed)} seeds ({divergence_ratio:.0%})")

    if divergence_ratio < 0.4:
        raise SystemExit(f"Regression failed: Dynamic A* diverged by >= 2.0s on only {divergence_ratio:.0%} of seeds (< 40% threshold)")

    print("All regression divergence checks PASSED cleanly.")

if __name__ == "__main__":
    check_divergence()

