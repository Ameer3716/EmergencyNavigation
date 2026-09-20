#!/usr/bin/env python3
"""Check final seed-1 evidence without starting another simulation."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def scalar(path: Path) -> dict[str, list[float]]:
    found: dict[str, list[float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] == "scalar":
            try:
                found.setdefault(parts[2], []).append(float(parts[3]))
            except ValueError:
                pass
    return found


checks: dict[str, object] = {}
individual = {row["configuration"]: row for row in rows(ROOT / "results/processed/individual_runs.csv")}
for config in CONFIGS:
    s = scalar(ROOT / "results/raw" / f"{config}-seed1.sca")
    e = rows(ROOT / "artifacts/logs" / f"emergency-{config}-verified.csv")
    generated = [row for row in e if row["action"] == "generated"]
    processed = [row for row in e if row["action"] == "ev_processed"]
    assert len(generated) == len(processed) == 1
    assert generated[0]["messageId"] == processed[0]["messageId"]
    assert s["accidentArrivalConfirmed"][0] == 1
    assert math.isclose(s["evResponseTime"][0], s["evArrivalTime"][0] - float(generated[0]["generationTime"]), abs_tol=1e-6)
    assert math.isclose(float(individual[config]["e2e_delay_s"]), float(processed[0]["eventTime"]) - float(generated[0]["generationTime"]), abs_tol=1e-6)
    assert math.isclose(float(individual[config]["nrl"]), (sum(s["controlTransmissions"]) + sum(s["emergencyTransmissions"]))
                        / len(processed), abs_tol=1e-6)
    assert math.isclose(float(individual[config]["control_bytes"]), sum(s["controlBytes"]), abs_tol=1e-6)
    for ext in ("sca", "vec", "vci"):
        assert (ROOT / "results/raw" / f"{config}-seed1.{ext}").stat().st_size > 0
    checks[f"{config}_arrival_and_metrics"] = "passed"

fog = rows(ROOT / "artifacts/logs/routing-FogCloudAStar-verified.csv")
assert any(row["action"] == "applied" and row["location"] == "cloud" for row in fog)
checks["fog_cloud_baseline"] = "passed"

fallback = rows(ROOT / "artifacts/logs/fallback-forced-verified.csv")
forced_routes = rows(ROOT / "artifacts/logs/routing-ForcedMistFailure-verified.csv")
assert any(row["fallbackReason"] == "forced_failure" for row in fallback)
assert any(row["action"] == "applied" and row["location"] == "fog" for row in forced_routes)
checks["forced_fog_takeover_and_route"] = "passed"

assert float(individual["MistDynamicFogFallback"]["route_decision_s"]) < 0.8
checks["mist_watchdog_success"] = "passed"

stress = rows(ROOT / "artifacts/logs/routing-CongestionReroute-stable.csv")
applied = [row for row in stress if row["action"] == "applied"]
assert len(applied) >= 2 and applied[0]["selectedEdges"] != applied[1]["selectedEdges"]
assert "Route replacement failed" not in (ROOT / "artifacts/logs/grid-CongestionReroute-stdout.txt").read_text(encoding="utf-8")
checks["dynamic_congestion_reroute"] = "passed (arrival not confirmed by 300 s)"

lights = rows(ROOT / "artifacts/logs/traffic-light-MistAStar-verified.csv")
by_light: dict[str, list[dict[str, str]]] = {}
for row in lights:
    by_light.setdefault(row["trafficLightId"], []).append(row)
for light, records in by_light.items():
    actions = [row["action"] for row in records]
    assert all(action in actions for action in ("request_received", "yellow", "all_red", "green_active", "program_restored")), light
    assert all(set(row["actualState"]) == {"r"} for row in records if row["action"] == "all_red"), light
    assert all("y" in row["actualState"] or row["actualState"] == row["originalState"]
               for row in records if row["action"] == "yellow"), light
    assert all("G" in row["actualState"] for row in records if row["action"] == "green_active"), light
checks["traffic_light_safe_transition_and_restoration"] = f"passed ({len(by_light)} lights)"

report = {"status": "passed", "checks": checks,
          "limitations": ["single seed: no estimable confidence interval",
                          "stress congestion run changed route but did not arrive by 300 s"]}
path = ROOT / "artifacts/logs/integrated-validation.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
