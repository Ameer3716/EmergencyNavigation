#!/usr/bin/env python3
"""Audit 360 primary runs and 90 waiting controls from raw evidence."""
from __future__ import annotations

import csv
import json
import re
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")
ALL_CONFIGS = CONFIGS + ("NoPreemptionBaseline",)
STALL_SEEDS = frozenset((4, 5, 9, 10, 13, 17, 18, 29))
DENSITIES = ("low", "medium", "high")
EXPECTED = {(cfg, density, seed) for cfg in ALL_CONFIGS for density in DENSITIES for seed in range(1, 31)}
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
    pattern = re.compile(r"^(FogCloudAStar|MistAStar|MistDynamicAStar|MistDynamicFogFallback|NoPreemptionBaseline)-(low|medium|high)-seed(\d+)\.sca$")
    paths = {}
    for path in raw.glob("*.sca"):
        match = pattern.match(path.name)
        if match:
            cfg, density, seed = match.groups()
            paths[(cfg, density, int(seed))] = path
    add(checks, "exact matched matrix", set(paths) == EXPECTED, len(paths), 450)

    missing_files = []
    stale_parameters = []
    manifest_errors = []
    priority_policy_errors = []
    binary_hashes = set()
    for key, path in paths.items():
        stem = path.stem
        for extension in ("vec", "vci"):
            peer = raw / f"{stem}.{extension}"
            if not peer.exists() or peer.stat().st_size == 0:
                missing_files.append(peer.name)
        content = path.read_text(encoding="utf-8")
        cfg, density, seed = key
        stall = 900 if cfg.startswith("Mist") and seed in STALL_SEEDS else 0
        required = ("config *.connectionManager.maxInterfDist 400m",
                    "config *.node[*].appl.telemetryValidationDelay 0ms",
                    "config *.node[*].appl.watchdogThreshold 500ms",
                    "config *.metrics.pollInterval 100ms",
                    "config *.tls[*].controller.minimumGreen 10s",
                    f"config *.node[*].appl.controlledMistStallDelay {stall}ms")
        if any(p not in content for p in required):
            stale_parameters.append(stem)
        # Scalar configuration entries list the selected config before inherited
        # defaults. Check the first effective value, not presence of any line.
        for parameter, expected_value in (
            ('preemptionDistance', '250m' if cfg.startswith('MistDynamic') else '100m'),
            ('preemptionEta', '20s' if cfg.startswith('MistDynamic') else '8s')):
            prefix = f'config *.node[*].appl.{parameter} '
            effective = next((line[len(prefix):] for line in content.splitlines() if line.startswith(prefix)), None)
            if effective != expected_value:
                priority_policy_errors.append(f'{stem}: {parameter}={effective}')
        manifest_path = logs / f"manifest-{stem}.json"
        if not manifest_path.exists():
            manifest_errors.append(stem)
        else:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            binary_hashes.add(m['binary_sha256'])
            if m['controlled_mist_stall_ms'] != stall:
                manifest_errors.append(stem)
            ini = ROOT / f"simulations/batch/{density}-seed{seed}/{cfg}/omnetpp.ini"
            if not ini.exists() or hashlib.sha256(ini.read_bytes()).hexdigest() != m['ini_sha256']:
                manifest_errors.append(stem + ': run input hash')
    add(checks, "raw triplets", not missing_files, missing_files[:10], "no missing .sca/.vec/.vci")
    add(checks, "new parameters in every scalar", not stale_parameters, stale_parameters[:10], "400m, 0ms, 500ms, 100ms, 10s minimum green, matched stall assignment")
    add(checks, "effective framework signal policy", not priority_policy_errors, priority_policy_errors[:10],
        "dynamic Mist 250m/20s; Fog/static Mist and waiting control 100m/8s")
    add(checks, "uniform binary and fault provenance", not manifest_errors and len(binary_hashes) == 1,
        {"errors": manifest_errors[:10], "binary_count": len(binary_hashes)}, "one binary and correct per-run manifests")
    library = ROOT / 'src/out/clang-release/libsrc.so'
    add(checks, "current rebuilt binary", library.exists() and
        binary_hashes == {hashlib.sha256(library.read_bytes()).hexdigest()},
        sorted(binary_hashes), "every run used the current binary")

    individual = read_csv(processed / "individual_runs-batch.csv")
    observed = {(r["configuration"], r["density"], int(r["seed"])) for r in individual}
    add(checks, "processed matched matrix", observed == EXPECTED and len(individual) == 450,
        len(individual), 450)
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
    expected_fallbacks = sum(int(r['delivered_messages']) > 0 and int(r['seed']) in STALL_SEEDS for r in fallback_rows)
    add(checks, "controlled fallback activation", fallback_count == expected_fallbacks and fallback_count == fallback_logs,
        {"processed": fallback_count, "logs": fallback_logs, "delivered_stall_cases": expected_fallbacks}, "every delivered controlled stall triggers; normal runs do not")
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
    baseline_keys = {key for key in summary_keys if key[0] == 'NoPreemptionBaseline'}
    expected_baseline = {('NoPreemptionBaseline',d,'traffic_light_wait_s') for d in DENSITIES}
    add(checks, "waiting-only no-preemption display", baseline_keys == expected_baseline,
        sorted(baseline_keys), sorted(expected_baseline))
    spawn_errors = []
    for cfg, density, seed in EXPECTED:
        path = logs / f'sumo-summary-{cfg}-{density}-seed{seed}.xml'
        if not path.exists():
            spawn_errors.append(str(path.name))
            continue
        steps = ET.parse(path).getroot().findall('step')
        expected_inserted = {'low': 74, 'medium': 146, 'high': 202}[density]
        # `loaded` records the vehicles SUMO has read from the route demand.
        # `inserted` can be lower at the fixed horizon when vehicles remain queued.
        if not steps or int(steps[-1].get('loaded', '-1')) != expected_inserted:
            spawn_errors.append(path.name)
    add(checks, 'actual SUMO loaded vehicle counts', not spawn_errors, spawn_errors[:10],
        '72/144/200 background vehicles plus two special vehicles loaded in every run')
    import statistics
    peak_means = {d: statistics.mean(float(r['peak_active_background']) for r in individual
                   if r['configuration'] == 'MistDynamicAStar' and r['density'] == d) for d in DENSITIES}
    add(checks, "different actual live traffic by density", peak_means['low'] < peak_means['medium'] < peak_means['high'], peak_means, "increasing peak live background counts")
    lookup = {(r['configuration'],r['density'],r['metric']):float(r['mean']) for r in summary}
    waiting = {d: {c:lookup[c,d,'traffic_light_wait_s'] for c in ALL_CONFIGS} for d in DENSITIES}
    add(checks, "priority reduces measured waiting with genuine green arrivals allowed",
        all(0 <= waiting[d][cfg] < waiting[d]['NoPreemptionBaseline'] for d in DENSITIES for cfg in CONFIGS),
        waiting, "nonnegative measured waiting, lower than matched no-priority control; short-notice red approaches are validated separately")

    graph_dir = ROOT / "results/graphs"
    missing_graphs = [f"{metric}-{density}.png" for metric in PRIMARY + SUPPLEMENTAL
                      for density in DENSITIES
                      if any(key[1] == density and key[2] == metric for key in summary_keys)
                      and not (graph_dir / f"{metric}-{density}.png").exists()]
    add(checks, "primary and supplemental graphs", not missing_graphs, missing_graphs, "all applicable graphs")
    from validate_timing_evidence import audit
    timing = audit(ROOT)
    add(checks, "minimum green clearance and timing decomposition", timing['passed'], timing,
        "no shortened green or timing/precision mismatch")
    extra_graphs = [f"{metric}-{condition}-{density}.png"
                    for metric in ('route_decision_ms', 'ev_response_s')
                    for condition in ('normal', 'controlled_stall') for density in DENSITIES]
    extra_graphs += [f"paired_{metric}-{density}.png"
                     for metric in ('route_decision_ms', 'ev_response_s') for density in DENSITIES]
    add(checks, "cohort and paired difference graphs", all((graph_dir / name).exists() for name in extra_graphs),
        extra_graphs, "12 cohort and six paired difference graphs")

    report = {"batch": "400m, 360 primary runs plus 90 waiting controls, 22 normal and 8 controlled stall seeds",
              "passed": all(r["status"] == "PASS" for r in checks), "checks": checks}
    output = ROOT / "artifacts/audit_report.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{sum(r['status'] == 'PASS' for r in checks)}/{len(checks)} checks passed; {output}")
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
