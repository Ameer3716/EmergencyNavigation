#!/usr/bin/env python3
"""Audit the current 400 m, four-configuration matched batch from raw evidence."""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")
DENSITIES = ("low", "medium", "high")
EXPECTED = {(cfg, density, seed) for cfg in CONFIGS for density in DENSITIES for seed in range(1, 31)}
PRIMARY = ("pdr", "nrl", "throughput_bps", "e2e_delay_ms", "route_decision_ms",
           "ev_response_s", "traffic_light_wait_s")
SUPPLEMENTAL = ("route_changes", "route_reviews", "fallback_triggered", "fallback_decision_ms")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def add(checks: list[dict[str, object]], name: str, passed: bool, observed: object, expected: object) -> None:
    checks.append({"check": name, "status": "PASS" if passed else "FAIL",
                   "observed": observed, "expected": expected})


def main() -> None:
    raw = ROOT / "results/raw"
    logs = ROOT / "artifacts/logs/batch"
    processed = ROOT / "results/processed"
    checks: list[dict[str, object]] = []
    pattern = re.compile(r"^(FogCloudAStar|MistAStar|MistDynamicAStar|MistDynamicFogFallback)-(low|medium|high)-seed(\d+)\.sca$")
    paths = {}
    for path in raw.glob("*.sca"):
        match = pattern.match(path.name)
        if match:
            cfg, density, seed = match.groups()
            paths[(cfg, density, int(seed))] = path
    add(checks, "exact matched matrix", set(paths) == EXPECTED, len(paths), 360)

    missing_files = []
    stale_parameters = []
    for key, path in paths.items():
        stem = path.stem
        for extension in ("vec", "vci"):
            peer = raw / f"{stem}.{extension}"
            if not peer.exists() or peer.stat().st_size == 0:
                missing_files.append(peer.name)
        content = path.read_text(encoding="utf-8")
        if ("config *.connectionManager.maxInterfDist 400m" not in content
                or "config *.node[*].appl.telemetryValidationDelay 20ms" not in content):
            stale_parameters.append(stem)
    add(checks, "raw triplets", not missing_files, missing_files[:10], "no missing .sca/.vec/.vci")
    add(checks, "new parameters in every scalar", not stale_parameters, stale_parameters[:10], "400m and 20ms")

    individual = read_csv(processed / "individual_runs-batch.csv")
    observed = {(r["configuration"], r["density"], int(r["seed"])) for r in individual}
    add(checks, "processed matched matrix", observed == EXPECTED and len(individual) == 360,
        len(individual), 360)
    summary = read_csv(processed / "summary-batch.csv")
    summary_keys = {(r["configuration"], r["density"], r["metric"]) for r in summary}
    missing_primary = [(cfg, density, metric) for cfg in CONFIGS for density in DENSITIES
                       for metric in PRIMARY if (cfg, density, metric) not in summary_keys]
    add(checks, "seven primary metrics", not missing_primary, missing_primary[:10], "84 summary groups")
    missing_extra = [(cfg, density, metric) for cfg in CONFIGS[2:] for density in DENSITIES
                     for metric in ("route_changes", "route_reviews") if (cfg, density, metric) not in summary_keys]
    missing_extra += [("MistDynamicFogFallback", density, "fallback_triggered") for density in DENSITIES
                      if ("MistDynamicFogFallback", density, "fallback_triggered") not in summary_keys]
    add(checks, "routing and fallback metrics", not missing_extra, missing_extra, "all applicable summaries")

    fallback_rows = [r for r in individual if r["configuration"] == "MistDynamicFogFallback"]
    fallback_count = sum(int(float(r["fallback_triggered"])) for r in fallback_rows)
    fallback_logs = sum((logs / f"fallback-MistDynamicFogFallback-{r['density']}-seed{r['seed']}.csv").exists()
                        for r in fallback_rows)
    add(checks, "organic fallback activation", fallback_count > 0 and fallback_count == fallback_logs,
        {"processed": fallback_count, "logs": fallback_logs}, "positive matching counts")
    unresolved = [r for r in fallback_rows if r["fallback_triggered"] == "1" and not r["route_decision_ms"]]
    add(checks, "fallback route completion", not unresolved, len(unresolved), 0)

    reroute_mismatch = []
    review_mismatch = []
    for row in individual:
        if row["configuration"] not in CONFIGS[2:]:
            continue
        stem = f"{row['configuration']}-{row['density']}-seed{row['seed']}"
        route = read_csv(logs / f"routing-{stem}.csv")
        reroutes = sum(r["action"] == "applied" and r["reason"] in ("cost_improvement", "low_speed") for r in route)
        reviews = sum(r["action"] == "evaluated" for r in route)
        if reroutes != int(float(row["route_changes"])):
            reroute_mismatch.append(stem)
        if reviews != int(float(row["route_reviews"])):
            review_mismatch.append(stem)
    add(checks, "route change counts match logs", not reroute_mismatch, reroute_mismatch[:10], "no mismatch")
    add(checks, "review counts match logs", not review_mismatch, review_mismatch[:10], "no mismatch")

    graph_dir = ROOT / "results/graphs"
    missing_graphs = [f"{metric}-{density}.png" for metric in PRIMARY + SUPPLEMENTAL
                      for density in DENSITIES
                      if any(key[1] == density and key[2] == metric for key in summary_keys)
                      and not (graph_dir / f"{metric}-{density}.png").exists()]
    add(checks, "primary and supplemental graphs", not missing_graphs, missing_graphs, "all applicable graphs")

    report = {"batch": "400m, four configurations, three densities, 30 matched seeds",
              "passed": all(r["status"] == "PASS" for r in checks), "checks": checks}
    output = ROOT / "artifacts/audit_report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{sum(r['status'] == 'PASS' for r in checks)}/{len(checks)} checks passed; {output}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
