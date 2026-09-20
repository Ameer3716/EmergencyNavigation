#!/usr/bin/env python3
"""Generate matched SUMO demand for one seed and traffic density."""

import argparse
import os
import subprocess
import sys
from pathlib import Path


PERIODS = {"low": 5.0, "medium": 2.5, "high": 1.8}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--density", choices=PERIODS, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--sumo-home", type=Path, default=os.environ.get("SUMO_HOME"))
    args = parser.parse_args()
    if not args.sumo_home:
        parser.error("--sumo-home or SUMO_HOME is required")
    root = Path(__file__).resolve().parents[1]
    net = root / "simulations" / "grid" / "grid.net.xml"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trip_file = args.output_dir / f"normal-{args.density}-seed{args.seed}.trips.xml"
    route_file = args.output_dir / f"normal-{args.density}-seed{args.seed}.rou.xml"
    command = [
        sys.executable,
        str(args.sumo_home / "tools" / "randomTrips.py"),
        "--net-file", str(net),
        "--output-trip-file", str(trip_file),
        "--route-file", str(route_file),
        "--begin", "0",
        "--end", "360",
        "--period", str(PERIODS[args.density]),
        "--seed", str(args.seed),
        "--prefix", "normal",
        "--validate",
    ]
    subprocess.run(command, check=True, env={**os.environ, "SUMO_HOME": str(args.sumo_home)})
    print(route_file)


if __name__ == "__main__":
    main()
