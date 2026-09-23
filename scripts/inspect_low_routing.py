from pathlib import Path
import csv
import re

ROOT = Path(__file__).resolve().parents[1]
logs = sorted((ROOT / "artifacts/logs/batch").glob("routing-MistDynamicAStar-low-seed*.csv"))
print(f"Found {len(logs)} low-seed routing logs.")

for p in logs:
    stem = p.stem.replace("routing-MistDynamicAStar-", "")
    with open(p, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    applied = [r for r in reader if r.get("action") == "applied" and r.get("reason") != "initial"]
    evals = [r for r in reader if r.get("action") == "evaluated"]
    
    # Get EV response time from sca if available
    sca_path = ROOT / "results/raw" / f"MistDynamicAStar-{stem}.sca"
    resp_time = "?"
    if sca_path.exists():
        m = re.search(r"scalar .*? evResponseTime ([0-9.eE+-]+)", sca_path.read_text(encoding="utf-8"))
        if m: resp_time = f"{float(m.group(1)):.1f}s"

    print(f"\n=== {stem} (evResponseTime={resp_time}) ===")
    print(f"Total evaluations: {len(evals)}, Total reroutes applied: {len(applied)}")
    for a in applied:
        t = float(a["time"])
        cur = a.get("currentEdge")
        below = a.get("belowThresholdEdges")
        reason = a.get("reason")
        route = a.get("selectedEdges")
        cost = a.get("estimatedCost")
        print(f"  [REROUTE at t={t:.1f}s] reason={reason}, edge={cur}, belowThresholdEdges={below}, cost={cost}")
        print(f"    New route: {route}")
