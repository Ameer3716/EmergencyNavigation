import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / "results/processed/summary-batch.csv") as f:
    rows = list(csv.DictReader(f))

print(f"{'Density':8s} | {'Configuration':25s} | {'n':2s} | {'Mean':8s} | {'StdDev':8s} | {'95% CI':16s}")
print("-" * 75)
for row in rows:
    if row["metric"] == "ev_response_s":
        sd = f"{float(row['stddev']):.2f}s" if row["stddev"] else "N/A"
        ci = f"[{float(row['ci95_lower']):.2f}, {float(row['ci95_upper']):.2f}]" if row["ci95_lower"] else "N/A"
        print(f"{row['density']:8s} | {row['configuration']:25s} | {row['n']:2s} | {float(row['mean']):.2f}s  | {sd:8s} | {ci:16s}")
