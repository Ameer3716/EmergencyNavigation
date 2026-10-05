#!/usr/bin/env python3
"""Process unmodified OMNeT++ scalars and emergency event logs."""
from __future__ import annotations

import argparse
import csv
import math
import itertools
import re
import shutil
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")
ALL_CONFIGS = CONFIGS + ("NoPreemptionBaseline",)
STALL_SEEDS = frozenset((4, 5, 9, 10, 13, 17, 18, 29))
METRICS = {
    "pdr": ("Packet delivery ratio", "ratio"),
    "e2e_delay_ms": ("EM end-to-end delay", "ms"),
    "throughput_bps": ("EM throughput", "bit/s"),
    "nrl": ("Normalized routing load", "packets/delivery"),
    "control_transmissions": ("Control transmissions", "packets"),
    "control_bytes": ("Control bytes", "bytes"),
    "ev_response_s": ("EV response time", "s"),
    "route_decision_ms": ("Route decision latency", "ms"),
    "traffic_light_wait_s": ("EV traffic-light waiting", "s"),
    "route_changes": ("Route changes", "events/run"),
    "route_reviews": ("Route computation frequency", "reviews/run"),
    "fallback_triggered": ("Fallback activation rate", "ratio"),
    "fallback_decision_ms": ("Fallback decision latency", "ms"),
    "ev_delay_vs_freeflow_s": ("EV corridor delay vs free-flow", "s"),
    "ev_distance_m": ("EV route distance", "m"),
    "ev_travel_s": ("EV travel time", "s"),
}


def scalars(path: Path) -> dict[str, list[float]]:
    data: dict[str, list[float]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) == 4 and fields[0] == "scalar":
            try:
                data[fields[2]].append(float(fields[3]))
            except ValueError:
                pass
    return data


def events(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def one_run(config: str, scalar_path: Path, density: str = "medium", seed: int = 1,
            event_path: Path | None = None) -> dict[str, object]:
    value = scalars(scalar_path)
    em = events(event_path or ROOT / "artifacts/logs" / f"emergency-{config}-verified.csv")
    stem = f"{config}-{density}-seed{seed}"
    log_dir = event_path.parent if event_path else ROOT / "artifacts/logs/batch"
    routing = events(log_dir / f"routing-{stem}.csv")
    fallback = events(log_dir / f"fallback-{stem}.csv")
    generated = {row["messageId"]: row for row in em if row["action"] == "generated"}
    delivered = {row["messageId"]: row for row in em if row["action"] == "ev_processed"}
    transmissions = [row for row in em if row["action"] == "transmit"]
    duration = 120.0 if config == "ForcedMistFailure" else 900.0
    payload_bits = sum(max(0, int(row["packetBytes"]) - 10) * 8 for row in delivered.values())
    control_tx = sum(value.get("controlTransmissions", []))
    control_bytes = sum(value.get("controlBytes", []))
    em_tx = sum(value.get("emergencyTransmissions", [])) if value.get("emergencyTransmissions") else len(transmissions)
    def first(name: str) -> float | None:
        return value[name][0] if value.get(name) else None
    def delay() -> float | None:
        ids = generated.keys() & delivered.keys()
        return statistics.mean(float(delivered[key]["eventTime"]) - float(generated[key]["generationTime"]) for key in ids) if ids else None
    delivery_count = len(delivered.keys() & generated.keys())
    return {
        "configuration": config,
        "density": density,
        "seed": seed,
        "scenario_condition": "controlled_stall" if seed in STALL_SEEDS else "normal",
        "controlled_mist_stall_s": first("controlledMistStallDelay"),
        "source_scalar": str(scalar_path.relative_to(ROOT)),
        "generated_messages": len(generated),
        "delivered_messages": delivery_count,
        "pdr": delivery_count / len(generated) if generated else None,
        "e2e_delay_ms": delay() * 1000 if delay() is not None else None,
        "throughput_bps": payload_bits / duration,
        "nrl": (control_tx + em_tx) / delivery_count if delivery_count else None,
        "control_transmissions": control_tx if value.get("controlTransmissions") else None,
        "control_bytes": control_bytes if value.get("controlBytes") else None,
        "emergency_transmissions": em_tx,
        "ev_response_s": first("evResponseTime"),
        "route_decision_ms": first("routeDecisionLatency") * 1000 if first("routeDecisionLatency") is not None else None,
        "traffic_light_wait_s": first("evTrafficLightWaitingTime"),
        "route_changes": sum(r["action"] == "applied" and r["reason"] in ("low_speed", "cost_improvement") for r in routing) if config.startswith("MistDynamic") else None,
        "route_reviews": sum(r["action"] == "evaluated" for r in routing) if config.startswith("MistDynamic") else None,
        "fallback_triggered": int(bool(fallback)) if config == "MistDynamicFogFallback" else None,
        "fallback_decision_ms": first("routeDecisionLatency") * 1000 if fallback and first("routeDecisionLatency") is not None else None,
        "ev_delay_vs_freeflow_s": max(0.0, first("evTravelTime") - first("evDistance") / 13.9) if first("evTravelTime") is not None and first("evDistance") is not None else None,
        "ev_distance_m": first("evDistance"),
        "ev_travel_s": first("evTravelTime"),
        "arrival_confirmed": first("accidentArrivalConfirmed"),
        "fog_processing_s": first("fogProcessingDelay"),
        "cloud_backhaul_s": first("cloudBackhaulDelay"),
        "communication_s": first("routeCommunicationDelay"),
        "background_seen_until_arrival": first("backgroundVehiclesSeenUntilArrival"),
        "peak_active_background": first("peakActiveBackgroundVehicles"),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def wilson_interval(successes: int, trials: int, confidence: float = 0.95) -> tuple[float, float]:
    if trials == 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = successes / trials
    denom = 1.0 + (z**2) / trials
    centre = (p + (z**2) / (2 * trials)) / denom
    spread = (z * math.sqrt((p * (1 - p) / trials) + ((z**2) / (4 * trials**2)))) / denom
    return (max(0.0, centre - spread), min(1.0, centre + spread))


import numpy as np
import scipy.stats as st

NONNEGATIVE_METRICS = {
    "traffic_light_wait_s", "ev_delay_vs_freeflow_s", "ev_response_s",
    "ev_travel_s", "ev_distance_m", "e2e_delay_ms", "route_decision_ms",
    "route_changes", "route_reviews", "fallback_triggered", "fallback_decision_ms",
    "throughput_bps", "control_transmissions", "control_bytes", "nrl"
}


def bootstrap_ci(values: list[float], n_boot: int = 10000, seed: int = 42) -> tuple[float, float]:
    """Compute empirical bootstrap percentile 95% confidence interval for zero-inflated nonnegative metrics.
    Uses fixed seed 42 and at least 10,000 resamples without manual clamping."""
    if not values:
        return (0.0, 0.0)
    if all(v == 0.0 for v in values):
        return (0.0, 0.0)
    rng = np.random.default_rng(seed)
    n = len(values)
    boot_means = [float(np.mean(rng.choice(values, size=n, replace=True))) for _ in range(n_boot)]
    low, high = np.percentile(boot_means, [2.5, 97.5])
    return (float(low), float(high))


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    result = []
    for density in sorted({str(row["density"]) for row in rows}):
      for config in ALL_CONFIGS:
        group = [row for row in rows if row["configuration"] == config and row["density"] == density]
        for key in METRICS:
            if config == "NoPreemptionBaseline" and key != "traffic_light_wait_s":
                continue
            values = [float(row[key]) for row in group if row[key] is not None]
            if not values:
                continue
            n = len(values)
            sd = statistics.stdev(values) if n > 1 else 0.0
            mean_val = statistics.mean(values)

            if key in ("pdr", "fallback_triggered"):
                successes = sum(1 for row in group if row.get("delivered_messages", 0) > 0) if key == "pdr" else int(sum(values))
                ci_low, ci_high = wilson_interval(successes, n)
            elif key in ("traffic_light_wait_s", "ev_delay_vs_freeflow_s"):
                # Bounded nonnegative zero-inflated metrics: use reproducible bootstrap percentile interval (10,000 resamples, seed=42)
                ci_low, ci_high = bootstrap_ci(values, n_boot=10000, seed=42)
            else:
                # Ordinary continuous metrics: exact Student-t 95% confidence interval (no silent clamping)
                if n > 1 and sd > 1e-9:
                    t_crit = float(st.t.ppf(0.975, df=n - 1))
                    margin = t_crit * sd / math.sqrt(n)
                    ci_low = mean_val - margin
                    ci_high = mean_val + margin
                else:
                    ci_low = mean_val
                    ci_high = mean_val

            result.append({
                "configuration": config,
                "density": density,
                "metric": key,
                "n": n,
                "mean": mean_val,
                "stddev": sd,
                "ci95_lower": ci_low,
                "ci95_upper": ci_high,
                "event_count": int(sum(values)) if key == "fallback_triggered" else ""
            })
    return result


def paired_comparisons(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    comparisons = [
        ("MistAStar", "FogCloudAStar", ["ev_response_s", "ev_travel_s", "route_decision_ms"]),
        ("MistDynamicAStar", "MistAStar", ["ev_response_s", "ev_travel_s", "ev_distance_m"]),
        ("MistDynamicFogFallback", "MistDynamicAStar", ["ev_response_s", "route_decision_ms", "ev_travel_s"]),
    ]
    results = []
    for density in ("low", "medium", "high"):
        by_seed = defaultdict(dict)
        for row in rows:
            if row["density"] == density:
                by_seed[int(row["seed"])][str(row["configuration"])] = row

        for cfg_a, cfg_b, metric_list in comparisons:
            for metric in metric_list:
                diffs = []
                vals_a = []
                vals_b = []
                for seed, configs in sorted(by_seed.items()):
                    if cfg_a in configs and cfg_b in configs:
                        va = configs[cfg_a].get(metric)
                        vb = configs[cfg_b].get(metric)
                        if va is not None and vb is not None:
                            vals_a.append(float(va))
                            vals_b.append(float(vb))
                            diffs.append(float(va) - float(vb))
                if not diffs:
                    continue

                n_pairs = len(diffs)
                mean_a = statistics.mean(vals_a)
                mean_b = statistics.mean(vals_b)
                mean_diff = statistics.mean(diffs)
                sd_diff = statistics.stdev(diffs) if n_pairs > 1 else 0.0
                se_diff = sd_diff / math.sqrt(n_pairs) if n_pairs > 0 else 0.0

                if n_pairs > 1:
                    t_crit = float(st.t.ppf(0.975, df=n_pairs - 1))
                else:
                    t_crit = 1.96

                # Handle zero variance identical observations
                if all(abs(d) < 1e-9 for d in diffs) or sd_diff < 1e-9:
                    results.append({
                        "density": density,
                        "config_A": cfg_a,
                        "config_B": cfg_b,
                        "metric": metric,
                        "N_scheduled": 30,
                        "n_pairs": n_pairs,
                        "mean_A": mean_a,
                        "mean_B": mean_b,
                        "mean_paired_diff": mean_diff,
                        "stddev_diff": 0.0,
                        "se_diff": 0.0,
                        "t_critical_95": t_crit,
                        "ci95_lower": mean_diff,
                        "ci95_upper": mean_diff,
                        "t_statistic": "NA",
                        "p_value": "NA",
                        "cohen_dz": 0.0,
                        "test_status": "not_applicable_zero_variance"
                    })
                else:
                    t_stat = mean_diff / se_diff if se_diff > 1e-9 else 0.0
                    p_val = float(st.t.sf(abs(t_stat), df=n_pairs - 1) * 2.0)
                    cohen_dz = mean_diff / sd_diff if sd_diff > 1e-9 else 0.0
                    ci_margin = t_crit * se_diff
                    status = "statistically_significant" if p_val < 0.05 else "not_significant"

                    results.append({
                        "density": density,
                        "config_A": cfg_a,
                        "config_B": cfg_b,
                        "metric": metric,
                        "N_scheduled": 30,
                        "n_pairs": n_pairs,
                        "mean_A": mean_a,
                        "mean_B": mean_b,
                        "mean_paired_diff": mean_diff,
                        "stddev_diff": sd_diff,
                        "se_diff": se_diff,
                        "t_critical_95": t_crit,
                        "ci95_lower": mean_diff - ci_margin,
                        "ci95_upper": mean_diff + ci_margin,
                        "t_statistic": t_stat,
                        "p_value": p_val,
                        "cohen_dz": cohen_dz,
                        "test_status": status
                    })
    return results


def archive_legacy_graphs() -> None:
    folder = ROOT / "results/graphs"
    legacy_dir = ROOT / "archive_raw_20261001_650m" / "graphs"
    legacy_dir.mkdir(parents=True, exist_ok=True)
    for p in folder.glob("*.png"):
        target = legacy_dir / p.name
        if not target.exists():
            shutil.copyfile(p, target)
        p.unlink()


def graphs(summary: list[dict[str, object]], metric_filter: list[str] | None = None,
           density_filter: list[str] | None = None) -> None:
    if metric_filter is None and density_filter is None:
        archive_legacy_graphs()
    folder = ROOT / "results/graphs"
    folder.mkdir(parents=True, exist_ok=True)

    plot_data_records = []

    for density, key in itertools.product(sorted({str(row["density"]) for row in summary}), METRICS):
        title, unit = METRICS[key]
        if density_filter and density not in density_filter:
            continue
        if metric_filter and key not in metric_filter:
            continue
        rows = [row for row in summary if row["metric"] == key and row["density"] == density]
        if not rows:
            continue
        names = [str(row["configuration"]).replace("DynamicFogFallback", "Dyn+Fog").replace("Dynamic", "Dyn.") for row in rows]
        means = [float(row["mean"]) for row in rows]
        
        # Exact metric-appropriate valid sample size
        n_valid = min(int(row["n"]) for row in rows)
        n_label = f"n={n_valid}"

        # Error bar computation
        if key in ("pdr", "fallback_triggered"):
            err_low = [max(0.0, float(row["mean"]) - float(row["ci95_lower"])) if row["ci95_lower"] is not None else 0 for row in rows]
            err_high = [max(0.0, float(row["ci95_upper"]) - float(row["mean"])) if row["ci95_upper"] is not None else 0 for row in rows]
            errors = [err_low, err_high]
            ci_label = "Wilson 95% CI"
        elif key in ("traffic_light_wait_s", "ev_delay_vs_freeflow_s"):
            err_low = [max(0.0, float(row["mean"]) - float(row["ci95_lower"])) if row["ci95_lower"] is not None else 0 for row in rows]
            err_high = [max(0.0, float(row["ci95_upper"]) - float(row["mean"])) if row["ci95_upper"] is not None else 0 for row in rows]
            errors = [err_low, err_high]
            ci_label = "Bootstrap percentile 95% CI"
        else:
            errors = [max(0.0, float(row["ci95_upper"]) - float(row["mean"])) if row["ci95_upper"] is not None else 0 for row in rows]
            ci_label = "Student-t 95% CI"

        # Accumulate sidecar plot data
        for r in rows:
            plot_data_records.append({
                "density": density,
                "metric": key,
                "configuration": r["configuration"],
                "mean": r["mean"],
                "stddev": r["stddev"],
                "n_scheduled": 30,
                "n_valid": r["n"],
                "ci95_lower": r["ci95_lower"],
                "ci95_upper": r["ci95_upper"],
                "ci_method": ci_label
            })
        
        fig, ax = plt.subplots(figsize=(9.5, 5.2))
        colors = ["#576b95", "#5c9e73", "#d49748", "#8f6bb1", "#b85450"][:len(rows)]
        bars = ax.bar(names, means, color=colors, yerr=errors, capsize=5, edgecolor="#333333", linewidth=0.8, error_kw={"elinewidth": 1.2, "capthick": 1.2})
        
        # Annotate mean values above upper error bar endpoint to avoid overlapping error bars
        for bar, mean, r in zip(bars, means, rows):
            if key in ("pdr", "fallback_triggered", "throughput_bps"):
                val_text = f"{mean:.3f}"
            elif key in ("route_changes", "route_reviews"):
                val_text = f"{mean:.2f}"
            elif key in ("e2e_delay_ms", "route_decision_ms", "fallback_decision_ms"):
                val_text = f"{mean:.1f}"
            else:
                val_text = f"{mean:.1f}"

            top_pos = max(mean, float(r["ci95_upper"]) if r.get("ci95_upper") is not None else mean)
            ax.annotate(val_text,
                        xy=(bar.get_x() + bar.get_width() / 2, top_pos),
                        xytext=(0, 6),
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=9.0, fontweight='bold')

        ax.set_title(f"{title} — {density.capitalize()} Traffic ({n_label})\n[95% CI]", fontsize=12, fontweight="bold", pad=12)
        ax.set_ylabel(f"{title} ({unit})" if unit != "ratio" else title, fontsize=10.5)
        if key in ("pdr", "fallback_triggered"):
            ax.set_ylim(0.0, 1.05)
        elif key in NONNEGATIVE_METRICS:
            uppers = [float(r["ci95_upper"]) for r in rows if r.get("ci95_upper") is not None]
            max_peak = max(uppers) if uppers and max(uppers) > 0 else 1.0
            ax.set_ylim(bottom=0.0, top=max(1.0, max_peak * 1.18))

        ax.tick_params(axis="x", rotation=16, labelsize=9.5)
        ax.tick_params(axis="y", labelsize=9.5)
        ax.grid(axis="y", alpha=0.25, linestyle="--")
        fig.tight_layout()
        fig.savefig(folder / f"{key}-{density}.png", dpi=180)
        plt.close(fig)

    # Export sidecar table only if full plot suite rendered
    if metric_filter is None and density_filter is None and plot_data_records:
        sidecar_path = ROOT / "results/processed/graph_plot_data.csv"
        sidecar_path.parent.mkdir(parents=True, exist_ok=True)
        with sidecar_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=plot_data_records[0].keys())
            writer.writeheader()
            writer.writerows(plot_data_records)



def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-all", action="store_true")
    parser.add_argument("--batch", action="store_true", help="Process density/seed batch instead of the seed-1 prototype")
    parser.add_argument("--render-graphs-only", action="store_true", help="Render graphs directly from existing summary-batch.csv without re-extracting simulation runs")
    parser.add_argument("--metrics", nargs="+", help="Specific metric(s) to render")
    parser.add_argument("--densities", nargs="+", help="Specific density/densities to render")
    parser.add_argument("--artifact-root", type=Path, default=ROOT, help="Process an isolated sample")
    parser.add_argument("--no-graphs", action="store_true")
    args = parser.parse_args()

    if args.render_graphs_only:
        summary_path = ROOT / "results/processed/summary-batch.csv"
        if not summary_path.exists():
            raise SystemExit(f"Missing {summary_path}")
        with summary_path.open("r", encoding="utf-8") as f:
            summary_rows = list(csv.DictReader(f))
        graphs(summary_rows, metric_filter=args.metrics, density_filter=args.densities)
        print(f"Rendered graphs for metric(s): {args.metrics or 'all'}, densities: {args.densities or 'all'}")
        return

    if args.batch:
        rows = []
        artifact_root = args.artifact_root.resolve()
        pattern = re.compile(r"^(FogCloudAStar|MistAStar|MistDynamicAStar|MistDynamicFogFallback|NoPreemptionBaseline)-(low|medium|high)-seed(\d+)\.sca$")
        for path in sorted((artifact_root / "results/raw").glob("*.sca")):
            match = pattern.match(path.name)
            if match:
                if args.require_all:
                    raw_text = path.read_text(encoding="utf-8")
                    if any(p not in raw_text for p in (
                        "config *.connectionManager.maxInterfDist 400m",
                        "config *.node[*].appl.telemetryValidationDelay 0ms",
                        "config *.node[*].appl.watchdogThreshold 500ms",
                        "config *.metrics.pollInterval 100ms")):
                        raise SystemExit(f"Stale or mismatched simulation parameters: {path}")
                config, density, seed_text = match.groups()
                stem = path.stem
                rows.append(one_run(config, path, density, int(seed_text),
                                    artifact_root / "artifacts/logs/batch" / f"emergency-{stem}.csv"))
        if args.require_all:
            expected = {(config, density, seed) for config in ALL_CONFIGS
                        for density in ("low", "medium", "high") for seed in range(1, 31)}
            actual = {(row["configuration"], row["density"], row["seed"]) for row in rows}
            if actual != expected or len(rows) != 450:
                raise SystemExit(f"Expected exact 450-run matrix; missing={len(expected - actual)}, extra={len(actual - expected)}")
    else:
        paths = [ROOT / "results/raw" / f"{config}-seed1.sca" for config in CONFIGS]
        if args.require_all and any(not path.exists() for path in paths):
            raise SystemExit("Required raw scalar file missing")
        rows = [one_run(config, path) for config, path in zip(CONFIGS, paths) if path.exists()]
    if not rows:
        raise SystemExit("No raw scalar files found")
    summary = summarize(rows)
    suffix = "-batch" if args.batch else ""
    output_root = args.artifact_root.resolve()
    write_csv(output_root / f"results/processed/individual_runs{suffix}.csv", rows)
    write_csv(output_root / f"results/processed/summary{suffix}.csv", summary)
    if args.batch:
        paired = paired_comparisons(rows)
        write_csv(output_root / "results/processed/paired_comparisons.csv", paired)
        cohorts = []
        for condition in ("normal", "controlled_stall"):
            for item in summarize([r for r in rows if r["scenario_condition"] == condition]):
                cohorts.append({"scenario_condition": condition, **item})
        write_csv(output_root / "results/processed/summary-cohorts.csv", cohorts)
    if not args.no_graphs:
        graphs(summary)
    print(f"Processed {len(rows)} genuine simulation runs; generated {len(METRICS)} graph types")


if __name__ == "__main__":
    main()

