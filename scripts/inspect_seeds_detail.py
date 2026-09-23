from pathlib import Path
import csv

ROOT = Path("d:/Codex/EmergencyNavigation")
logs = sorted((ROOT / "artifacts/logs/batch").glob("routing-MistDynamicAStar-low-seed*.csv"))

print(f"Analyzing {len(logs)} low-density routing logs:\n")

for p in logs:
    stem = p.stem.replace("routing-MistDynamicAStar-", "")
    with open(p, newline="", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    # Filter to last run if multiple initial runs exist
    last_init_idx = 0
    for idx, r in enumerate(reader):
        if r.get("action") == "computed" and r.get("reason") == "initial":
            last_init_idx = idx
    run_records = reader[last_init_idx:]
    applied = [r for r in run_records if r.get("action") == "applied" and r.get("reason") != "initial"]
    initial = [r for r in run_records if r.get("action") == "applied" and r.get("reason") == "initial"]
    init_route = initial[0]["selectedEdges"] if initial else "?"
    init_edges = init_route.split("|") if init_route != "?" else []
    
    # Also find evaluations that preceded each applied reroute to see what triggered it
    print(f"=== {stem} ===")
    print(f"  Initial Route: {init_route} (edges={len(init_edges)})")
    print(f"  Reroutes applied: {len(applied)}")
    
    for a in applied:
        t_app = float(a["time"])
        cur_route = a.get("selectedEdges", "").split("|")
        # find matching evaluation at same time
        matching_eval = [r for r in run_records if r.get("action") == "evaluated" and abs(float(r["time"]) - t_app) < 0.1]
        below = a.get("belowThresholdEdges") or (matching_eval[0].get("belowThresholdEdges") if matching_eval else "None")
        print(f"    t={t_app:.1f}s | reason={a.get('reason')} | curEdge={a.get('currentEdge')} | belowThresh={below} | cost={float(a.get('estimatedCost', 0)):.1f}s | newLen={len(cur_route)} edges")
        print(f"      detour vs initial: {len(cur_route)} vs {len(init_edges)} edges (diff={len(cur_route) - len(init_edges)})")
        print(f"      route: {a.get('selectedEdges')}")
