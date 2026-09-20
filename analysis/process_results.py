#!/usr/bin/env python3
"""Process unmodified OMNeT++ scalars and emergency event logs."""
from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")
METRICS = {
    "pdr": ("Packet delivery ratio", "ratio"),
    "e2e_delay_s": ("EM end-to-end delay", "s"),
    "throughput_bps": ("Useful EM throughput", "bit/s"),
    "nrl": ("Normalized routing load", "packets/delivery"),
    "control_transmissions": ("Control transmissions", "packets"),
    "control_bytes": ("Control bytes", "bytes"),
    "ev_response_s": ("EV response time", "s"),
    "route_decision_s": ("Route decision latency", "s"),
    "traffic_light_wait_s": ("EV traffic-light waiting", "s"),
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
        "source_scalar": str(scalar_path.relative_to(ROOT)),
        "generated_messages": len(generated),
        "delivered_messages": delivery_count,
        "pdr": delivery_count / len(generated) if generated else None,
        "e2e_delay_s": delay(),
        "throughput_bps": payload_bits / duration,
        "nrl": (control_tx + em_tx) / delivery_count if delivery_count else None,
        "control_transmissions": control_tx if value.get("controlTransmissions") else None,
        "control_bytes": control_bytes if value.get("controlBytes") else None,
        "emergency_transmissions": em_tx,
        "ev_response_s": first("evResponseTime"),
        "route_decision_s": first("routeDecisionLatency"),
        "traffic_light_wait_s": first("evTrafficLightWaitingTime"),
        "ev_distance_m": first("evDistance"),
        "ev_travel_s": first("evTravelTime"),
        "arrival_confirmed": first("accidentArrivalConfirmed"),
        "fog_processing_s": first("fogProcessingDelay"),
        "cloud_backhaul_s": first("cloudBackhaulDelay"),
        "communication_s": first("routeCommunicationDelay"),
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    result = []
    for density in sorted({str(row["density"]) for row in rows}):
      for config in CONFIGS:
        group = [row for row in rows if row["configuration"] == config and row["density"] == density]
        for key in METRICS:
            values = [float(row[key]) for row in group if row[key] is not None]
            if not values:
                continue
            n = len(values)
            sd = statistics.stdev(values) if n > 1 else None
            ci = 1.96 * sd / math.sqrt(n) if sd is not None else None
            result.append({"configuration": config, "density": density, "metric": key, "n": n,
                           "mean": statistics.mean(values), "stddev": sd,
                           "ci95_lower": statistics.mean(values) - ci if ci is not None else None,
                           "ci95_upper": statistics.mean(values) + ci if ci is not None else None})
    return result


def graphs(summary: list[dict[str, object]]) -> None:
    folder = ROOT / "results/graphs"
    folder.mkdir(parents=True, exist_ok=True)
    for density in sorted({str(row["density"]) for row in summary}):
      for key, (title, unit) in METRICS.items():
        rows = [row for row in summary if row["metric"] == key and row["density"] == density]
        if not rows:
            continue
        names = [str(row["configuration"]).replace("Dynamic", "Dyn.").replace("Fallback", "+Fog") for row in rows]
        means = [float(row["mean"]) for row in rows]
        errors = [(float(row["ci95_upper"]) - float(row["mean"])) if row["ci95_upper"] is not None else 0 for row in rows]
        fig, ax = plt.subplots(figsize=(8.5, 4.7))
        ax.bar(names, means, color=["#576b95", "#5c9e73", "#d49748", "#8f6bb1"][:len(rows)], yerr=errors, capsize=4)
        ax.set_title(f"{title} — {density} traffic")
        ax.set_ylabel(unit)
        ax.tick_params(axis="x", rotation=16)
        ax.grid(axis="y", alpha=0.2)
        fig.tight_layout()
        fig.savefig(folder / f"{key}-{density}.png", dpi=180)
        plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-all", action="store_true")
    parser.add_argument("--batch", action="store_true", help="Process density/seed batch instead of the seed-1 prototype")
    args = parser.parse_args()
    if args.batch:
        rows = []
        pattern = re.compile(r"^(FogCloudAStar|MistAStar|MistDynamicAStar|MistDynamicFogFallback)-(low|medium|high)-seed(\d+)\.sca$")
        for path in sorted((ROOT / "results/raw").glob("*.sca")):
            match = pattern.match(path.name)
            if match:
                config, density, seed_text = match.groups()
                stem = path.stem
                rows.append(one_run(config, path, density, int(seed_text),
                                    ROOT / "artifacts/logs/batch" / f"emergency-{stem}.csv"))
        if args.require_all and len(rows) != 360:
            raise SystemExit(f"Expected 360 batch runs, found {len(rows)}")
    else:
        paths = [ROOT / "results/raw" / f"{config}-seed1.sca" for config in CONFIGS]
        if args.require_all and any(not path.exists() for path in paths):
            raise SystemExit("Required raw scalar file missing")
        rows = [one_run(config, path) for config, path in zip(CONFIGS, paths) if path.exists()]
    if not rows:
        raise SystemExit("No raw scalar files found")
    summary = summarize(rows)
    suffix = "-batch" if args.batch else ""
    write_csv(ROOT / f"results/processed/individual_runs{suffix}.csv", rows)
    write_csv(ROOT / f"results/processed/summary{suffix}.csv", summary)
    graphs(summary)
    print(f"Processed {len(rows)} genuine simulation runs; generated {len(METRICS)} graph types")


if __name__ == "__main__":
    main()

