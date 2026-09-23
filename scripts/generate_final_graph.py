"""Regenerate final-ev-response-graph.png directly from results/processed/summary-batch.csv."""
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results/processed/summary-batch.csv"
OUTPUT = ROOT / "artifacts/screenshots/final-ev-response-graph.png"

CONFIG_NAMES = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback", "NoPreemptionBaseline")
CONFIG_LABELS = ("FogCloud", "Mist", "MistDyn.", "MistDyn+Fog", "NoPreempt")
COLORS = ["#4e6d9b", "#439775", "#d98a3e", "#8c62a8", "#b85450"]

def main():
    if not SUMMARY.exists():
        raise SystemExit(f"Missing {SUMMARY}")

    with open(SUMMARY, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Focus on High and Medium traffic, or 3-panel / grouped
    # Let's create a grouped comparison across Low, Medium, High traffic
    densities = ("low", "medium", "high")
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=True)

    for ax, density in zip(axes, densities):
        d_rows = [r for r in rows if r["density"] == density and r["metric"] == "ev_response_s"]
        d_dict = {r["configuration"]: r for r in d_rows}
        
        means = []
        errors = []
        for cfg in CONFIG_NAMES:
            if cfg in d_dict:
                m = float(d_dict[cfg]["mean"])
                means.append(m)
                ci_high = float(d_dict[cfg]["ci95_upper"]) if d_dict[cfg]["ci95_upper"] else m
                errors.append(ci_high - m)
            else:
                means.append(0)
                errors.append(0)

        bars = ax.bar(CONFIG_LABELS, means, yerr=errors, capsize=4.5, color=COLORS, width=0.68, edgecolor="#222222", linewidth=0.8)
        
        # Add value labels on top of bars
        for bar, mean in zip(bars, means):
            if mean > 0:
                ax.annotate(f"{mean:.1f}s",
                            xy=(bar.get_x() + bar.get_width() / 2, mean),
                            xytext=(0, 5),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8.5, fontweight='bold')

        n_val = d_rows[0]["n"] if d_rows else "?"
        ax.set_title(f"{density.capitalize()} Traffic (n={n_val})", fontsize=13, fontweight="bold")
        ax.tick_params(axis="x", rotation=18, labelsize=9.5)
        ax.grid(axis="y", linestyle="--", alpha=0.25)

    axes[0].set_ylabel("EV Response Time (s)", fontsize=12, fontweight="bold")
    fig.suptitle("Emergency Vehicle Response Time Across Configurations (95% CI)", fontsize=14, fontweight="bold", y=0.98)
    fig.tight_layout()
    
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=200)
    plt.close(fig)
    print(f"Generated: {OUTPUT}")

if __name__ == "__main__":
    main()
