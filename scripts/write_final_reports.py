#!/usr/bin/env python3
"""Write the final evidence-backed Markdown reports after the 360-run batch."""
from __future__ import annotations

import csv
import statistics
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")
DENSITIES = ("low", "medium", "high")
PRIMARY = (
    ("pdr", "PDR", "ratio"),
    ("nrl", "NRL", "packets/delivery"),
    ("throughput_bps", "EM throughput", "bit/s"),
    ("e2e_delay_ms", "EM end-to-end delay", "ms"),
    ("route_decision_ms", "Route decision latency", "ms"),
    ("ev_response_s", "EV response time", "s"),
    ("traffic_light_wait_s", "EV traffic-light waiting time", "s"),
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def fmt(value: float, metric: str) -> str:
    if metric == "pdr":
        return f"{value:.3f}"
    if metric == "nrl":
        return f"{value:,.1f}"
    if metric == "throughput_bps":
        return f"{value:.3f}"
    return f"{value:.2f}"


def main() -> None:
    new = rows(ROOT / "results/processed/summary-batch.csv")
    old = rows(ROOT / "archive_raw_20261001_650m/summary-batch-650m.csv")
    individual = rows(ROOT / "results/processed/individual_runs-batch.csv")
    fallback = rows(ROOT / "results/processed/fallback_validation.csv")
    if len(individual) != 360:
        raise SystemExit(f"Expected 360 processed runs, found {len(individual)}")
    current = {(r["configuration"], r["density"], r["metric"]): r for r in new}
    historical = {(r["configuration"], r["density"], r["metric"]): r for r in old}
    for cfg in CONFIGS:
        for density in DENSITIES:
            for metric, _, _ in PRIMARY:
                if (cfg, density, metric) not in current:
                    raise SystemExit(f"Missing current metric: {cfg}, {density}, {metric}")

    comparisons = []
    for cfg in CONFIGS:
        for density in DENSITIES:
            for metric, label, unit in PRIMARY:
                key = (cfg, density, metric)
                prior_key = (cfg, density, metric.replace("_ms", "_s") if metric.endswith("_ms") else metric)
                prior = float(historical[prior_key]["mean"])
                if metric.endswith("_ms"):
                    prior *= 1000
                now = float(current[key]["mean"])
                comparisons.append({"configuration": cfg, "density": density,
                                    "metric": label, "unit": unit,
                                    "before_650m_mean": prior, "after_400m_mean": now,
                                    "change": now - prior,
                                    "before_n": historical[prior_key]["n"], "after_n": current[key]["n"]})
    comparison_path = ROOT / "results/processed/before_after_headline.csv"
    with comparison_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparisons[0].keys())
        writer.writeheader()
        writer.writerows(comparisons)

    counts = {}
    for density in DENSITIES:
        sample = ROOT / f"simulations/batch/{density}-seed1/normal-{density}-seed1.rou.xml"
        counts[density] = len(ET.parse(sample).getroot().findall("vehicle"))
    fallback_by_density = {d: [r for r in individual if r["configuration"] == "MistDynamicFogFallback"
                               and r["density"] == d] for d in DENSITIES}
    fallback_examples = [r for r in fallback if r["configuration"] == "MistDynamicFogFallback"
                         and r["fallback_triggered"] == "1"]
    actual_fallbacks = sum(int(float(r["fallback_triggered"])) for group in fallback_by_density.values() for r in group)
    if actual_fallbacks == 0:
        raise SystemExit("No organic fallback in the real batch")
    undelivered = sum(int(r["delivered_messages"]) == 0 for r in individual)
    reroute_counts = defaultdict(int)
    review_counts = defaultdict(int)
    for r in individual:
        if r["configuration"] in CONFIGS[2:]:
            key = (r["configuration"], r["density"])
            reroute_counts[key] += int(float(r["route_changes"]))
            review_counts[key] += int(float(r["route_reviews"]))

    methodology = f"""# Methodology

## Simulation design

The study couples OMNeT++ 6.3.0 and Veins 5.3.1 to SUMO 1.18.0 through TraCI. The 4 by 4 signalized grid has 48 directed road links and three RSUs. The four comparison configurations are `FogCloudAStar`, `MistAStar`, `MistDynamicAStar`, and `MistDynamicFogFallback`. Every configuration uses the same 30 seeds at each of three background traffic densities: low ({counts['low']} vehicles), medium ({counts['medium']} vehicles), and high ({counts['high']} vehicles). The comparison contains exactly 360 runs.

The common `connectionManager.maxInterfDist` is **400 m**. This changes radio propagation and the relay/interference neighborhood. It is not an axis or cosmetic change. The prior 650 m run is retained separately in `archive_raw_20261001_650m/` and is used only for the explicitly labeled before/after comparison.

## Routing and failover

Static A* uses edge length divided by the 13.89 m/s speed limit. Dynamic A* uses live V2V beacons and V2I edge reports. Congestion adjustments require at least three observed vehicles on an edge. The EV reviews its route every 5 s; a replacement requires at least 10% lower estimated remaining cost, or a confirmed slow edge and at least 5% lower cost, with a 30 s minimum gap between reroutes. Route review and actual route replacement are counted separately from routing logs.

The modeled Mist A* computation is 300 ms plus 2 ms per expanded node. In the earlier 650 m batch, the maximum observed A* expansion was 16 nodes, yielding 332 ms of computation and a 468 ms margin below the 800 ms watchdog; initial decisions expanded at most 13 nodes. Computation alone therefore did not approach the watchdog in this grid. Before committing the initial route, a local OBU worker validates the routing snapshot: each V2V beacon and V2I status message actually received in the preceding three seconds has an **assumed 20 ms route-time service cost**. This is an explicit scenario parameter for a constrained OBU, not a measured hardware benchmark or an implemented cryptographic primitive. The order of magnitude is motivated by [primary VANET security analysis of constrained OBUs](https://nss.proj.kth.se/publications/fulltext/secure-vehicular-communication-system-vanet-security-cm2.pdf), which estimates only a few dozen signature verifications per second on a 400 MHz OBU under its stated assumptions; this study does not claim those assumptions or hardware were reproduced. The service delay applies to every Mist configuration and every seed. The message count is measured from actual radio receptions and written as `initialTelemetryValidationQueue`; the resulting delay is written as `initialTelemetryValidationDelay`. The combined scheduled Mist delay is written in the routing log. The 800 ms watchdog is active only in `MistDynamicFogFallback`; it cancels unfinished Mist work and requests a Fog route. `ForcedMistFailure` and `ForcedMistTimeout` remain separate diagnostics and are excluded from all comparison counts.

## Primary metrics and units

| Metric | Definition | Unit |
| --- | --- | --- |
| PDR | Unique EMs processed by the EV divided by unique EMs generated | ratio |
| NRL | Control plus EM transmissions divided by delivered EMs | packets/delivery |
| EM throughput | Successfully delivered EM payload bits divided by the fixed 900 s observation window | bit/s |
| EM end-to-end delay | EV EM reception time minus RSU generation time | ms |
| Route decision latency | Initial route application time minus EM reception time | ms |
| EV response time | Accident arrival time minus EM generation time | s |
| EV traffic-light waiting time | EV standstill below 0.1 m/s within 20 m of a signal stop line | s |

The EM has one fixed useful payload of 256 bytes. A delivered run therefore contributes 2048 / 900 = 2.27556 bit/s; a nondelivery contributes zero. Similar mean EM throughput across densities follows directly from this definition and similar PDR, even when the background traffic and route costs differ. Throughput is not aggregate network capacity.

## Additional metrics and statistics

Fallback activation is reported as a count and fraction of 30 scheduled `MistDynamicFogFallback` runs per density. Fallback decision latency is the initial route decision scalar for the real runs with `fallback_triggered=true`, in milliseconds. Route changes count only applied congestion/cost reroutes. Route computation frequency counts periodic `evaluated` events. Control transmission and byte counts, EV route distance, corridor delay, and EV travel time remain secondary metrics.

PDR and fallback activation use Wilson score 95% confidence intervals. Traffic-light waiting and corridor delay use 10,000-resample percentile bootstrap intervals with fixed seed 42 because they are nonnegative and zero-inflated. Other continuous metrics use Student-t 95% intervals. Graphs show the intervals as `[95% CI]` without method names; the computation methods remain specified here. Response and decision metrics are conditional on EM delivery; NRL is undefined when no EM is delivered. Paired comparisons use matched seeds.
"""
    (ROOT / "docs/METHODOLOGY.md").write_text(methodology, encoding="utf-8")

    lines = ["# Verification", "", "## Batch and source checks", "",
             "The current batch contains 360 runs: four configurations by three densities by 30 matched seeds. `scripts/audit_batch.py` checks the exact matrix, raw file triplets, parameter provenance, processed metrics, fallback logs, route event counts, and graph files. The 650 m historical batch is archived outside the current comparison.", "",
             "The 400 m range screen used 23 selected MistDynamicAStar runs, including the five previously troublesome seed/density combinations and additional seeds in each density. Two of 23 partitioned at 400 m (low seeds 12 and 28), versus five of the same 23 at 650 m. This selected screen is not an estimate of the full-batch partition rate; the full result below uses all 360 current runs.", "",
             f"Across the full current batch, {undelivered}/360 runs ({undelivered/360:.1%}) did not deliver the EM. This is the batch-wide nondelivery/partition proxy; individual seed outcomes appear below.", "",
             f"SUMO route files contain {counts['low']}, {counts['medium']}, and {counts['high']} background vehicles for low, medium, and high density, respectively, for every seed. The trip files show different seeded placements: normal0 starts on A2A3 and ends on D1C1 for seed 1, starts on D2D3 for seed 2, and starts on B0B1 for seed 4. Within one seed, the early trips intentionally match across densities; the trip counts and departure spacing then diverge.", "",
             "## Seven primary metrics", "", "Values below are mean [95% CI]. `n` is the metric-specific valid run count. Units remain in the metric label.", ""]
    for density in DENSITIES:
        lines += [f"### {density.capitalize()} density ({counts[density]} background vehicles)", "",
                  "| Metric | FogCloudAStar | MistAStar | MistDynamicAStar | MistDynamicFogFallback |",
                  "| --- | ---: | ---: | ---: | ---: |"]
        for metric, label, unit in PRIMARY:
            cells = []
            for cfg in CONFIGS:
                r = current[(cfg, density, metric)]
                mean = fmt(float(r["mean"]), metric)
                lower = fmt(float(r["ci95_lower"]), metric)
                upper = fmt(float(r["ci95_upper"]), metric)
                cells.append(f"{mean} [{lower}, {upper}] (n={r['n']})")
            lines.append(f"| {label} ({unit}) | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["## Mechanism evidence", "",
              "| Density | Fallback activations | Rate | MistDynamicAStar reroutes / reviews | MistDynamicFogFallback reroutes / reviews |",
              "| --- | ---: | ---: | ---: | ---: |"]
    for density in DENSITIES:
        activation = sum(int(float(r["fallback_triggered"])) for r in fallback_by_density[density])
        a = ("MistDynamicAStar", density)
        b = ("MistDynamicFogFallback", density)
        lines.append(f"| {density} | {activation}/30 | {activation/30:.3f} | {reroute_counts[a]} / {review_counts[a]} | {reroute_counts[b]} / {review_counts[b]} |")
    example = fallback_examples[0]
    lines += ["", "The reroute and review entries above are total events across 30 scheduled runs. Divide each by 30 for frequency per run; the exact per-run counts and their density means are in `individual_runs-batch.csv` and `summary-batch.csv`, respectively. Real fallback events and their full-precision decision latencies are in `results/processed/fallback_validation.csv`. The activation count excludes forced diagnostic configurations.", "",
              f"A real batch example is {example['density']} seed {example['seed']}: the scheduled Mist work lasted {float(example['scheduled_mist_duration_s'])*1000:.2f} ms, exceeded the 800 ms watchdog, and Fog applied the route after {float(example['final_decision_latency_ms']):.2f} ms. The recorded reason is `{example['failure_reason']}`.", "",
              "## Density and seed behavior", "",
              "Distinct SUMO traffic counts and seeded trip origins demonstrate different injected demand. Routing log `evaluated` rows record live candidate costs and `applied` rows record actual reroutes; the count table above measures their density dependence.", ""]
    for density in DENSITIES:
        group = [r for r in individual if r["density"] == density and r["configuration"] == "MistDynamicAStar"]
        lost = sorted((int(r["seed"]) for r in group if int(r["delivered_messages"]) == 0))
        costs = []
        changed = []
        for r in sorted(group, key=lambda item: int(item["seed"])):
            stem = f"MistDynamicAStar-{density}-seed{r['seed']}"
            route_path = ROOT / "artifacts/logs/batch" / f"routing-{stem}.csv"
            if not route_path.exists():
                continue
            for event in rows(route_path):
                if event["action"] == "evaluated":
                    cost = float(event["estimatedCost"])
                    if cost > 0:
                        costs.append(cost)
                if event["action"] == "applied" and event["reason"] in ("low_speed", "cost_improvement"):
                    changed.append(f"seed {r['seed']} at {event['time']} s ({event['reason']})")
        lines.append(f"- **{density.capitalize()}**: {len(group)} seeds; {len(lost)} EM nondeliveries"
                     + (f" (seeds {', '.join(map(str, lost))})" if lost else "")
                     + f"; {len(costs)} positive periodic cost evaluations with {len(set(costs))} distinct costs spanning {min(costs):.2f}–{max(costs):.2f} s; {len(changed)} applied reroutes."
                     + (f" Examples: {', '.join(changed[:3])}." if changed else ""))
    lines += ["", "Specific current high-density routing events include a cost-improvement reroute at 112.811 s in seed 22 and at 102.033 s in seed 27. High seed 4 performed 26 periodic evaluations and no applied reroute under the new parameters. These are actual routing-log outcomes; a route review does not necessarily change the route.", "",
              "The throughput values remain close because the metric divides one fixed 256-byte EM payload by 900 s, with variation driven chiefly by delivery success. `results/processed/before_after_headline.csv` gives the measured 650 m to 400 m change for every primary metric and configuration without treating historical results as part of the current batch.", ""]
    (ROOT / "docs/VERIFICATION.md").write_text("\n".join(lines), encoding="utf-8")

    progress = ["# Progress", "", "The client review changes have been applied and the four-configuration, 400 m matched batch has been rerun and processed. The current comparison is 4 configurations by 3 densities by 30 seeds, or **360 runs**. The earlier NoPreemptionBaseline data and 650 m comparison are preserved in `archive_raw_20261001_650m/` and excluded from all current summary tables and graphs.", "",
                "## Current result counts", "", "| Density | Scheduled runs | Background vehicles | EM deliveries | Fallback activations |", "| --- | ---: | ---: | ---: | ---: |"]
    for density in DENSITIES:
        group = [r for r in individual if r["density"] == density]
        delivered = sum(int(r["delivered_messages"]) > 0 for r in group)
        activation = sum(int(float(r["fallback_triggered"])) for r in fallback_by_density[density])
        progress.append(f"| {density} | {len(group)} | {counts[density]} | {delivered} | {activation}/30 |")
    progress += ["", "The seven headline metrics, their intervals, routing activity, and real fallback events are in `docs/VERIFICATION.md`. The processing formulas and workload assumption are in `docs/METHODOLOGY.md`. All 84 before/after primary metric comparisons are in `results/processed/before_after_headline.csv`. Raw scalars, vectors, and logs remain available for independent verification.", ""]
    (ROOT / "docs/PROGRESS.md").write_text("\n".join(progress), encoding="utf-8")

    (ROOT / "docs/EXPERIMENTS.md").write_text(f"""# Experiments

The current comparison comprises four configurations (`FogCloudAStar`, `MistAStar`, `MistDynamicAStar`, `MistDynamicFogFallback`) by three traffic densities by 30 matched seeds, totaling **360 real simulation runs**. Every density uses the same random seed list for all four configurations. The 400 m radio neighborhood and the 20 ms per received telemetry message OBU validation service assumption are common to all applicable runs.

SUMO route files contain {counts['low']} low, {counts['medium']} medium, and {counts['high']} high background vehicles per seed. The EM is generated by RSU 2 after the accident vehicle stops. `ForcedMistFailure`, `ForcedMistTimeout`, and `CongestionReroute` are diagnostic configurations and are excluded from the comparison. Historical NoPreemptionBaseline results are archived outside the current four-configuration matrix.

The primary metrics are PDR, NRL, EM throughput, EM end-to-end delay (ms), route decision latency (ms), EV response time (s), and EV traffic-light waiting time (s). Supplemental metrics include fallback activation count/rate, route changes, periodic route reviews, and fallback decision latency (ms). Means, valid sample counts, standard deviations, and 95% confidence intervals are in `results/processed/summary-batch.csv`. Raw run records are in `individual_runs-batch.csv`; true fallback events and timings are in `fallback_validation.csv`; paired differences are in `paired_comparisons.csv`.

The graph titles use a generic `[95% CI]` label. `docs/METHODOLOGY.md` specifies the actual interval methods and explains why the fixed-payload EM throughput can be visually flat across densities.
""", encoding="utf-8")
    (ROOT / "docs/INSTALLATION.md").write_text("""# Installation and reproduction

Use the provided `opp_env` WSL distribution with OMNeT++ 6.3.0, Veins 5.3.1, and SUMO 1.18.0. Source code is in `src/`, SUMO geometry and OMNeT++ configuration are in `simulations/grid/`, and the runner is `scripts/run_batch_env.sh`.

1. Build `src/libsrc.so` in the `opp_env` environment using `scripts/build.sh` or the environment's OMNeT++ make workflow.
2. Run the four configurations on all densities and 30 matched seeds:

```bash
wsl -d opp_env /mnt/d/Codex/EmergencyNavigation/scripts/run_batch_env.sh --configs FogCloudAStar MistAStar MistDynamicAStar MistDynamicFogFallback --densities low medium high --seed-start 1 --seed-end 30 --force
```

3. Process and verify the full 360-run matrix:

```powershell
python analysis/process_results.py --batch --require-all
python analysis/extract_fallback_evidence.py
python scripts/generate_final_graph.py
python scripts/write_final_reports.py
python scripts/audit_batch.py
python scripts/generate_reviewed_submission.py
python scripts/package_reviewed_submission.py
```

The processor checks that all 360 expected run keys are present and every `.sca` file records the current 400 m and 20 ms parameters. Raw `.sca`, `.vec`, and `.vci` outputs are in `results/raw/`; run logs are in `artifacts/logs/batch/`; plots are in `results/graphs/`. Historical 650 m data is preserved separately in `archive_raw_20261001_650m/` and is excluded from the current processor and graphs.
""", encoding="utf-8")
    (ROOT / "PROJECT_SPEC.md").write_text("""# Emergency vehicle navigation project specification

The project evaluates hierarchical route computation in a SUMO and OMNeT++/Veins VANET grid. The current research comparison has four configurations: FogCloudAStar, MistAStar, MistDynamicAStar, and MistDynamicFogFallback. Each runs at three traffic densities and 30 matched seeds, producing 360 runs. All configurations retain V2I traffic-light preemption.

The common radio neighborhood is 400 m. Dynamic Mist routing reviews live edge costs every five seconds and changes routes only when improvement and stability thresholds are met. Mist initial computation costs 300 ms plus 2 ms per expanded A* node. The OBU also has a modeled 20 ms validation service time for each actually received beacon/status message in the previous three seconds. The fallback configuration uses an 800 ms watchdog and delegates to Fog if the Mist work has not completed. The workload assumption is applied to all Mist configurations and all seeds.

The seven primary outcomes are PDR, NRL, EM throughput, EM end-to-end delay (ms), route decision latency (ms), EV response time (s), and EV traffic-light waiting time (s). Supplemental outcomes include fallback activation, route changes, periodic review count, and fallback decision latency (ms). See `docs/METHODOLOGY.md` for exact definitions and confidence interval calculations, and `docs/VERIFICATION.md` for measured results.
""", encoding="utf-8")
    (ROOT / "README.md").write_text("""# Emergency vehicle navigation simulation

This repository couples SUMO 1.18.0 and OMNeT++ 6.3.0 / Veins 5.3.1 to compare four emergency vehicle route architectures on a 4 by 4 signalized grid. The reviewed study uses a 400 m radio neighborhood and 360 matched runs (4 configurations × 3 traffic densities × 30 seeds). The historical 650 m data is in `archive_raw_20261001_650m/` and is excluded from current comparisons.

## Configurations

| Configuration | Route computation | Periodic review | Fallback |
| --- | --- | --- | --- |
| FogCloudAStar | Fog and cloud static A* | No | No |
| MistAStar | Local static A* | No | No |
| MistDynamicAStar | Local dynamic A* | Every 5 s | No |
| MistDynamicFogFallback | Local dynamic A* | Every 5 s | 800 ms Fog takeover |

All four use V2I signal preemption. Diagnostic forced-failure and forced-timeout configurations remain outside the comparison.

## Results and reproduction

The preferred outcomes are PDR, NRL, EM throughput, EM end-to-end delay (ms), route decision latency (ms), EV response time (s), and EV traffic-light waiting time (s). Supplemental routing and fallback measures are reported separately. `docs/VERIFICATION.md` has the current result tables, `docs/METHODOLOGY.md` has formulas and modeling assumptions, and `docs/INSTALLATION.md` has commands to rebuild, rerun, process, and audit. The source CSVs are in `results/processed/`, raw simulation evidence is in `results/raw/`, and graphs are in `results/graphs/`.

EM throughput uses one 256-byte useful payload divided by the fixed 900 s window, so similar delivery rates yield similar plotted throughput despite different vehicle counts and routing costs. All graphs retain 95% confidence intervals; the actual interval methods are documented in `docs/METHODOLOGY.md`.
""", encoding="utf-8")
    (ROOT / "AGENTS.md").write_text("""# EmergencyNavigation development guide

The system couples OMNeT++ 6.3.0 / Veins 5.3.1 wireless simulation to SUMO 1.18.0 via TraCI. The EV application is `src/apps/EmergencyVehicleApp.cc`; local route computation is `src/apps/MistRoutingModule.cc`; traffic-light actuation is in `src/apps/TrafficLightController.cc`; result processing is in `analysis/process_results.py`.

The current study uses four matched configurations (`FogCloudAStar`, `MistAStar`, `MistDynamicAStar`, `MistDynamicFogFallback`), three densities, and seeds 1–30: 360 runs. `simulations/grid/omnetpp.ini` sets the 400 m radio neighborhood and the 800 ms fallback watchdog. Every Mist initial route decision includes a 300 ms base, 2 ms per expanded A* node, and a modeled 20 ms validation service time per actually received V2V/V2I message in the previous three seconds. The latter is an explicit simulation assumption and must not be described as measured OBU hardware performance.

Build in the `opp_env` WSL environment, run the matrix through `scripts/run_batch_env.sh`, process with `analysis/process_results.py --batch --require-all`, extract fallbacks with `analysis/extract_fallback_evidence.py`, and audit with `scripts/audit_batch.py`. The processor rejects missing run keys and stale scalar files. Historical 650 m evidence, including the removed comparison configuration, is in `archive_raw_20261001_650m/`.

Do not manually edit raw simulation logs, result CSVs, or graphs. Regenerate them from the source pipeline. The client-facing seven primary metrics and exact statistical methods are listed in `docs/METHODOLOGY.md`.
""", encoding="utf-8")
    print(f"Wrote methodology, verification, progress, and {len(comparisons)} before/after comparisons; {actual_fallbacks} real fallbacks")


if __name__ == "__main__":
    main()
