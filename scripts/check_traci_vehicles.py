import os
import sys
from pathlib import Path

ROOT = Path("/mnt/d/codex/EmergencyNavigation")
SUMO_HOME = Path("/home/opp_env/sumo118_pkg/sumo")
sys.path.insert(0, str(SUMO_HOME / "tools"))
import traci

cmd = [
    str(SUMO_HOME / "bin/sumo"),
    "-c", str(ROOT / "simulations/grid/grid.sumocfg"),
    "--seed", "1"
]
traci.start(cmd)
for t in range(0, 180, 5):
    while traci.simulation.getTime() < t:
        traci.simulationStep()
    vehs = traci.vehicle.getIDList()
    print(f"t={t:3d}s: count={len(vehs)}")
traci.close()
