#!/usr/bin/env python3
"""Check the genuine SUMO-only medium/seed-1 run."""

import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.project.resolve()
    net = ET.parse(root / "simulations/grid/grid.net.xml").getroot()
    tls = [node for node in net.findall("tlLogic")]
    road_edges = [node for node in net.findall("edge") if node.get("function") != "internal"]
    assert len(tls) >= 4, f"expected traffic lights, found {len(tls)}"
    assert len(road_edges) >= 40, f"expected urban grid, found {len(road_edges)} edges"

    fcd = root / "artifacts/logs/sumo-medium-fcd.xml"
    samples: dict[str, list[tuple[float, float, float, float]]] = {}
    for event, element in ET.iterparse(fcd, events=("end",)):
        if element.tag == "timestep":
            time = float(element.get("time"))
            for vehicle in element.findall("vehicle"):
                vid = vehicle.get("id", "")
                samples.setdefault(vid, []).append(
                    (time, float(vehicle.get("x")), float(vehicle.get("y")), float(vehicle.get("speed")))
                )
            element.clear()
    normal_ids = [vid for vid in samples if vid.startswith("normal")]
    assert len(normal_ids) >= 100, f"expected normal traffic, found {len(normal_ids)}"
    moving_normal_ids = [
        vid for vid in normal_ids
        if len({(round(x, 1), round(y, 1)) for _, x, y, _ in samples[vid]}) > 1
    ]
    assert len(moving_normal_ids) >= 100, "normal vehicles did not move"
    ambulance = samples["ambulance"]
    assert ambulance[0][0] <= 1, "ambulance did not appear at startup"
    assert any(t >= 66 and speed > 1 for t, _, _, speed in ambulance), "ambulance did not move after initial stop"
    accident = samples["accident"]
    stopped_after_event = [speed for t, _, _, speed in accident if 63 <= t <= 66]
    assert stopped_after_event and max(stopped_after_event) < 0.1, "accident vehicle was not stopped near event"
    tripinfos = ET.parse(root / "artifacts/logs/sumo-medium-tripinfo.xml").getroot()
    ambulance_trip = next((node for node in tripinfos.findall("tripinfo") if node.get("id") == "ambulance"), None)
    assert ambulance_trip is not None, "ambulance did not finish its SUMO route"
    assert float(ambulance_trip.get("arrival")) < 900, "ambulance arrived after scenario end"
    assert ambulance_trip.get("arrivalLane", "").startswith("D2D3"), "ambulance reached wrong edge"
    accident_at_event = min(accident, key=lambda row: abs(row[0] - 63))
    distance_to_accident = math.hypot(ambulance[-1][1] - accident_at_event[1], ambulance[-1][2] - accident_at_event[2])
    assert distance_to_accident <= 50, f"ambulance destination is {distance_to_accident:.1f} m from accident"
    density_arrivals = {"medium": float(ambulance_trip.get("arrival"))}
    for density in ("low", "high"):
        density_trips = ET.parse(root / f"artifacts/logs/sumo-{density}-tripinfo.xml").getroot()
        ev_trip = next((node for node in density_trips.findall("tripinfo") if node.get("id") == "ambulance"), None)
        assert ev_trip is not None, f"ambulance did not finish in {density} traffic"
        density_arrivals[density] = float(ev_trip.get("arrival"))
        assert density_arrivals[density] < 900, f"ambulance arrived too late in {density} traffic"
    result = {
        "network_road_edges": len(road_edges),
        "traffic_lights": len(tls),
        "normal_vehicles_observed": len(normal_ids),
        "normal_vehicles_moved": len(moving_normal_ids),
        "ambulance_first_time": ambulance[0][0],
        "ambulance_last_time": ambulance[-1][0],
        "ambulance_arrival_time": float(ambulance_trip.get("arrival")),
        "ambulance_distance_to_accident_m": round(distance_to_accident, 2),
        "ambulance_arrival_by_density_s": density_arrivals,
        "ambulance_last_x_y_speed": ambulance[-1][1:],
        "ambulance_max_x_y": [max(row[1] for row in ambulance), max(row[2] for row in ambulance)],
        "accident_first_time": accident[0][0],
        "accident_speed_max_63_to_66": max(stopped_after_event),
        "status": "passed",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
