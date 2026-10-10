#!/usr/bin/env python3
"""Check signal clearance, minimum green and route timing against real raw runs."""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
from raw_data import events, scalars


def audit(root):
    binaries = set()
    failures, counts = [], {"runs": 0, "green_transitions": 0, "phase_rechecks": 0,
                            "bounded_priority_holds": 0,
                            "fog_timing_balances": 0, "em_precision_checks": 0}
    for path in sorted((root / "results/raw").glob("*.sca")):
        if "-seed" not in path.stem:
            continue
        counts["runs"] += 1
        value = scalars(path)
        logs = root / "artifacts/logs/batch"
        manifest = logs / f"manifest-{path.stem}.json"
        if manifest.exists():
            binaries.add(json.loads(manifest.read_text())["binary_sha256"])
        else:
            failures.append([path.stem, "missing binary provenance"])
        def first(name):
            return value[name][0] if value.get(name) else None
        if first("fogProcessingDelay") is not None:
            latency = first("routeDecisionLatency")
            parts = sum(first(k) for k in ("routeWaitBeforeFog", "fogProcessingDelay",
                                           "cloudBackhaulDelay", "routeCommunicationDelay"))
            counts["fog_timing_balances"] += 1
            if not math.isclose(latency, parts, abs_tol=1e-10) or first("routeCommunicationDelay") < -1e-10:
                failures.append([path.stem, "fog timing balance"])
            if events(logs / f"fallback-{path.stem}.csv") and not math.isclose(first("routeWaitBeforeFog"), .5, abs_tol=1e-10):
                failures.append([path.stem, "watchdog waiting must be separate"])
        for row in events(logs / f"emergency-{path.stem}.csv"):
            if row["action"] == "ev_processed":
                delay = float(row["eventTime"]) - float(row["generationTime"])
                counts["em_precision_checks"] += 1
                if not math.isclose(delay, first("emEndToEndDelay"), abs_tol=2e-11):
                    failures.append([path.stem, "EM timestamp precision"])
        last, priority_start = {}, {}
        for row in events(logs / f"traffic-light-{path.stem}.csv"):
            action, light = row["action"], row["trafficLightId"]
            time = float(row["eventTime"])
            if action == 'green_active':
                priority_start[light] = time
            if action == 'release_yellow' and light in priority_start:
                counts['bounded_priority_holds'] += 1
                if time - priority_start[light] > 25.5 + 1e-8:
                    failures.append([path.stem, light, 'priority hold exceeded 25 s plus one polling step'])
            if action == "minimum_green_recheck":
                counts["phase_rechecks"] += 1
            if action in ("yellow", "release_yellow") and any(c in row["stateBeforeTransition"] for c in "Gg"):
                counts["green_transitions"] += 1
                if float(row["greenAgeAtTransition_s"]) < 10 - 1e-8:
                    failures.append([path.stem, light, action, "green shorter than 10 s"])
            expected = {"all_red": ("yellow", 2), "release_all_red": ("release_yellow", 2),
                        "green_active": ("all_red", 1), "program_restored": ("release_all_red", 1)}
            if action in expected and light in last and last[light][0] == expected[action][0]:
                if not math.isclose(time - last[light][1], expected[action][1], abs_tol=1e-8):
                    failures.append([path.stem, light, action, "clearance duration"])
            last[light] = action, time
    return {"passed": bool(counts["runs"]) and len(binaries) == 1 and not failures,
            **counts, "binary_sha256": sorted(binaries), "failures": failures}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = audit(args.artifact_root.resolve())
    destination = args.artifact_root / "artifacts/timing_validation.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["passed"]:
        raise SystemExit(1)
