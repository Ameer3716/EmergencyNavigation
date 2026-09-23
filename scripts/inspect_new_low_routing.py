from pathlib import Path
import csv

ROOT = Path("d:/Codex/EmergencyNavigation")
logs = sorted((ROOT / "artifacts/logs/batch").glob("routing-MistDynamicAStar-low-seed*.csv"))
print(f"Inspecting {len(logs)} low-density routing logs:\n")

total_reroutes = 0
for p in logs:
    stem = p.stem.replace("routing-MistDynamicAStar-", "")
    with open(p, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    applied = [r for r in reader if r.get("action") == "applied" and r.get("reason") != "initial"]
    initial = [r for r in reader if r.get("action") == "applied" and r.get("reason") == "initial"]
    init_route = initial[0]["selectedEdges"] if initial else "?"
    init_edges = init_route.split("|") if init_route != "?" else []
    total_reroutes += len(applied)

    print(f"=== {stem} ===")
    print(f"  Initial Route: {init_route} ({len(init_edges)} edges)")
    print(f"  Reroutes applied: {len(applied)}")
    for a in applied:
        t_app = float(a["time"])
        cur_route = a.get("selectedEdges", "").split("|")
        print(f"    t={t_app:.1f}s | reason={a.get('reason')} | curEdge={a.get('currentEdge')} | belowThresh={a.get('belowThresholdEdges')} | cost={float(a.get('estimatedCost', 0)):.1f}s | edges={len(cur_route)}")
        print(f"      route: {a.get('selectedEdges')}")

print(f"\nTotal reroutes across all {len(logs)} seeds: {total_reroutes}")
