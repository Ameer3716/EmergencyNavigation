#!/usr/bin/env python3
"""Run matched density/seed SUMO+Veins experiments inside an opp_env shell."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRID = ROOT / "simulations/grid"
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback", "NoPreemptionBaseline")
SUMO_HOME = Path(os.environ.get("SUMO_HOME", "/home/opp_env/sumo118_pkg/sumo"))


def one_sumo_config(directory: Path, route_name: str, seed: int) -> None:
    (directory / "grid.sumocfg").write_text(
        f'''<?xml version="1.0"?>
<configuration><input><net-file value="grid.net.xml"/>
<route-files value="{route_name},special.rou.xml"/></input>
<time><begin value="0"/><end value="900"/><step-length value="0.5"/></time>
<processing><time-to-teleport value="-1"/></processing>
<random_number><seed value="{seed}"/></random_number></configuration>''', encoding="utf-8")
    (directory / "grid.launchd.xml").write_text(
        f'''<?xml version="1.0"?><launch><copy file="grid.net.xml"/>
<copy file="{route_name}"/><copy file="special.rou.xml"/>
<copy file="grid.sumocfg" type="config"/></launch>''', encoding="utf-8")


def one_omnet_config(directory: Path, config: str, density: str, seed: int) -> None:
    stem = f"{config}-{density}-seed{seed}"
    logs = ROOT / "artifacts/logs/batch"
    logs.mkdir(parents=True, exist_ok=True)
    base = (GRID / "omnetpp.ini").read_text(encoding="utf-8")
    override = f'''
[Config Batch]
extends = {config}
seed-set = {seed}
*.manager.launchConfig = xmldoc("grid.launchd.xml")
*.**.appl.eventLogPath = "{logs / ('emergency-' + stem + '.csv')}"
*.node[*].appl.routingLogPath = "{logs / ('routing-' + stem + '.csv')}"
*.node[*].appl.fallbackLogPath = "{logs / ('fallback-' + stem + '.csv')}"
*.metrics.mobilityLogPath = "{logs / ('mobility-' + stem + '.csv')}"
*.tls[*].controller.trafficLightLogPath = "{logs / ('traffic-light-' + stem + '.csv')}"
'''
    (directory / "omnetpp.ini").write_text(base + override, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--densities", nargs="+", choices=("low", "medium", "high"), default=("low", "medium", "high"))
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--seed-end", type=int, default=30)
    parser.add_argument("--configs", nargs="+", choices=CONFIGS, default=CONFIGS)
    parser.add_argument("--force", action="store_true", help="Rerun selected seeds even when raw outputs exist")
    args = parser.parse_args()
    if args.seed_start < 1 or args.seed_end < args.seed_start:
        parser.error("Invalid seed range")
    veins_root = Path(os.environ["VEINS_ROOT"])
    library = ROOT / "src/out/clang-release/src"
    if not (library.parent / "libsrc.so").exists():
        raise SystemExit("Build the custom OMNeT++ library first")
    for density in args.densities:
        for seed in range(args.seed_start, args.seed_end + 1):
            base = ROOT / "simulations/batch" / f"{density}-seed{seed}"
            base.mkdir(parents=True, exist_ok=True)
            route_name = f"normal-{density}-seed{seed}.rou.xml"
            route = base / route_name
            if not route.exists():
                subprocess.run(["python3", str(ROOT / "scripts/generate_demand.py"),
                                "--density", density, "--seed", str(seed),
                                "--output-dir", str(base), "--sumo-home", str(SUMO_HOME)], check=True)
            for common in ("grid.net.xml", "special.rou.xml", "antenna.xml", "config.xml"):
                shutil.copyfile(GRID / common, base / common)
            one_sumo_config(base, route_name, seed)
            for config in args.configs:
                stem = f"{config}-{density}-seed{seed}"
                outputs = [ROOT / "results/raw" / f"{stem}.{extension}" for extension in ("sca", "vec", "vci")]
                if not args.force and all(path.exists() and path.stat().st_size > 0 for path in outputs):
                    print(f"Skip completed {stem}", flush=True)
                    continue
                run_dir = base / config
                run_dir.mkdir(exist_ok=True)
                logs_dir = ROOT / "artifacts/logs/batch"
                for prefix in ("emergency-", "routing-", "fallback-", "mobility-", "traffic-light-"):
                    old_log = logs_dir / f"{prefix}{stem}.csv"
                    if old_log.exists():
                        old_log.unlink()
                for common in ("grid.net.xml", "special.rou.xml", "antenna.xml", "config.xml", route_name,
                               "grid.sumocfg", "grid.launchd.xml"):
                    shutil.copyfile(base / common, run_dir / common)
                one_omnet_config(run_dir, config, density, seed)
                output = ROOT / "artifacts/logs/batch" / f"{stem}-stdout.txt"
                with output.open("w", encoding="utf-8") as log:
                    subprocess.run(["opp_run", "-u", "Cmdenv", "-c", "Batch",
                                    "-n", f"{veins_root / 'src/veins'}:{ROOT / 'src'}",
                                    "-l", str(veins_root / "src/veins"), "-l", str(library),
                                    "-f", "omnetpp.ini"], cwd=run_dir, stdout=log,
                                   stderr=subprocess.STDOUT, check=True)
                for extension in ("sca", "vec", "vci"):
                    source = run_dir / "results" / f"Batch-#0.{extension}"
                    if not source.exists():
                        raise RuntimeError(f"Missing result: {source}")
                    destination = ROOT / "results/raw" / f"{stem}.{extension}"
                    shutil.copyfile(source, destination)
                print(f"Complete {stem}", flush=True)


if __name__ == "__main__":
    main()
