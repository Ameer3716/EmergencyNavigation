#!/usr/bin/env python3
"""Capture actual SUMO-GUI frames through TraCI from the seed-1 grid."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMO_HOME = Path(os.environ.get("SUMO_HOME", "/home/opp_env/sumo118_pkg/sumo"))
sys.path.insert(0, str(SUMO_HOME / "tools"))
import traci  # noqa: E402


def main() -> None:
    output = ROOT / "artifacts/screenshots"
    output.mkdir(parents=True, exist_ok=True)
    config = ROOT / "simulations/grid/grid.sumocfg"
    binary = SUMO_HOME / "bin/sumo-gui"
    traci.start([str(binary), "-c", str(config), "--start", "--quit-on-end", "--seed", "1"])
    try:
        view = traci.gui.DEFAULT_VIEW
        traci.gui.setBoundary(view, -100, -100, 1000, 1000)
        captures = {20: "sumo-grid-normal-traffic.png",
                    67: "sumo-ev-accident-positions.png"}
        while traci.simulation.getTime() < max(captures):
            traci.simulationStep()
            now = int(traci.simulation.getTime())
            if now in captures and abs(traci.simulation.getTime() - now) < 1e-6:
                path = output / captures.pop(now)
                traci.gui.screenshot(view, str(path), 1200, 900)
                print(path)
                if now == 67:
                    traci.gui.setBoundary(view, -50, -50, 350, 350)
                    traci.simulationStep()
                    traci.gui.screenshot(view, str(output / "sumo-ambulance-closeup.png"), 1000, 800)
                    traci.simulationStep()
                    traci.gui.setBoundary(view, 600, 600, 1000, 1000)
                    traci.simulationStep()
                    traci.gui.screenshot(view, str(output / "sumo-accident-closeup.png"), 1000, 800)
            if not captures:
                traci.simulationStep()
                break
    finally:
        traci.close()


if __name__ == "__main__":
    main()
