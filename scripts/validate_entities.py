#!/usr/bin/env python3
"""Verify TraCI type mapping and application module construction."""

import json
import re
from pathlib import Path


root = Path(__file__).resolve().parents[1]
sca = (root / "simulations/grid/results/Smoke-#0.sca").read_text(encoding="utf-8")
stdout = (root / "artifacts/logs/grid-Smoke-stdout.txt").read_text(encoding="utf-8")
launch = (root / "artifacts/logs/grid-launchd.log").read_text(encoding="utf-8")

def module_indexes(type_name: str) -> set[int]:
    pattern = rf'par EmergencyGridScenario\.node\[(\d+)\]\.appl typename "\\"emergencynavigation\.apps\.{type_name}\\""'
    return {int(value) for value in re.findall(pattern, sca)}


normal = module_indexes("NormalVehicleApp")
emergency = module_indexes("EmergencyVehicleApp")
rsus = {
    int(value)
    for value in re.findall(
        r'par EmergencyGridScenario\.rsu\[(\d+)\]\.appl typename "\\"emergencynavigation\.apps\.RsuApp\\""',
        sca,
    )
}
assert len(normal) >= 1, "no normal vehicle application instantiated"
assert len(emergency) == 1, f"expected one emergency app, got {emergency}"
assert rsus == {0, 1, 2}, f"expected three RSU apps, got {rsus}"
assert "scalar EmergencyGridScenario.node[0].mist initialized 1" in sca
for index in (0, 1, 2):
    assert f"scalar EmergencyGridScenario.rsu[{index}].fog initialized 1" in sca
assert "scalar EmergencyGridScenario.cloud initialized 1" in sca
assert "scalar EmergencyGridScenario.metrics initialized 1" in sca
controllers = {
    int(value)
    for value in re.findall(r"scalar EmergencyGridScenario\.tls\[(\d+)\]\.controller initialized 1", sca)
}
assert controllers == set(range(16)), f"expected controllers at all traffic lights, got {controllers}"
assert "Simulation time limit reached -- at t=120s" in stdout
assert "grid.sumocfg" in launch and "<exit-code>0</exit-code>" in launch
result = {
    "normal_vehicle_app_modules": len(normal),
    "emergency_vehicle_app_modules": len(emergency),
    "rsu_app_indexes": sorted(rsus),
    "fog_modules": 3,
    "mist_modules": 1,
    "cloud_modules": 1,
    "traffic_light_controllers": len(controllers),
    "metrics_modules": 1,
    "co_simulation_completed": True,
    "status": "passed",
}
print(json.dumps(result, indent=2))
