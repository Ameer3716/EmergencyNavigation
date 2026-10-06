#!/usr/bin/env python3
"""Run matched density/seed SUMO+Veins experiments inside an opp_env shell."""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import random
import json
import hashlib
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
GRID = ROOT / "simulations/grid"
CONFIGS = ("FogCloudAStar", "MistAStar", "MistDynamicAStar", "MistDynamicFogFallback", "NoPreemptionBaseline")
# Fixed independent selection, identical across densities and every Mist approach.
STALL_SEEDS = frozenset(random.Random(20261005).sample(range(1, 31), 8))
SUMO_HOME = Path(os.environ.get("SUMO_HOME", "/home/opp_env/sumo118_pkg/sumo"))


def one_sumo_config(directory: Path, route_name: str, seed: int, summary_path: Path | None = None) -> None:
    output = f'<output><summary-output value="{summary_path}"/></output>' if summary_path else ""
    (directory / "grid.sumocfg").write_text(
        f'''<?xml version="1.0"?>
<configuration><input><net-file value="grid.net.xml"/>
<route-files value="{route_name},special.rou.xml"/></input>
<time><begin value="0"/><end value="900"/><step-length value="0.5"/></time>
<processing><time-to-teleport value="-1"/></processing>
<random_number><seed value="{seed}"/></random_number>{output}</configuration>''', encoding="utf-8")
    (directory / "grid.launchd.xml").write_text(
        f'''<?xml version="1.0"?><launch><copy file="grid.net.xml"/>
<copy file="{route_name}"/><copy file="special.rou.xml"/>
<copy file="grid.sumocfg" type="config"/></launch>''', encoding="utf-8")


def one_omnet_config(directory: Path, config: str, density: str, seed: int, logs: Path, sim_time_limit: int | None) -> None:
    stem = f"{config}-{density}-seed{seed}"
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
    if sim_time_limit is not None:
        override += f"sim-time-limit = {sim_time_limit}s\n"
    stall = "900ms" if config.startswith("Mist") and seed in STALL_SEEDS else "0ms"
    override += f"*.node[*].appl.controlledMistStallDelay = {stall}\n"
    (directory / "omnetpp.ini").write_text(base + override, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--densities", nargs="+", choices=("low", "medium", "high"), default=("low", "medium", "high"))
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--seed-end", type=int, default=30)
    parser.add_argument("--configs", nargs="+", choices=CONFIGS, default=CONFIGS)
    parser.add_argument("--jobs", type=int, default=1, help="Independent density/seed groups to run concurrently")
    parser.add_argument("--force", action="store_true", help="Rerun selected seeds even when raw outputs exist")
    parser.add_argument("--resume-incomplete", action="store_true", help="Keep complete raw triplets and rerun only missing/incomplete run keys")
    parser.add_argument("--seeds", nargs="+", type=int, help="Explicit matched seeds for a sample")
    parser.add_argument("--artifact-root", type=Path, default=ROOT, help="Store raw results and logs under a separate root")
    parser.add_argument("--sim-time-limit", type=int, help="Shorter simulation horizon for partition screening")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.seed_start < 1 or args.seed_end < args.seed_start:
        parser.error("Invalid seed range")
    veins_root = Path(os.environ["VEINS_ROOT"])
    library = next((candidate for candidate in (
        ROOT / "src/out/clang-release/src",
        ROOT / "src/out/gcc-release/src",
    ) if (candidate.parent / "libsrc.so").is_file()), None)
    if library is None:
        raise SystemExit("Missing libsrc.so; run bash scripts/build.sh first")
    with (library.parent / "libsrc.so").open("rb") as handle:
        binary_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    artifact_root = args.artifact_root.resolve()
    raw_dir = artifact_root / "results/raw"
    logs_dir = artifact_root / "artifacts/logs/batch"
    raw_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    def run_seed(key):
        density, seed = key
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
            outputs = [raw_dir / f"{stem}.{extension}" for extension in ("sca", "vec", "vci")]
            if args.resume_incomplete and all(path.exists() and path.stat().st_size > 0 for path in outputs):
                print(f"Retain completed {stem}", flush=True)
                continue
            if not args.force and all(path.exists() and path.stat().st_size > 0 for path in outputs):
                print(f"Skip completed {stem}", flush=True)
                continue
            run_dir = base / config
            run_dir.mkdir(exist_ok=True)
            for prefix in ("emergency-", "routing-", "fallback-", "mobility-", "traffic-light-"):
                old_log = logs_dir / f"{prefix}{stem}.csv"
                if old_log.exists():
                    old_log.unlink()
            for common in ("grid.net.xml", "special.rou.xml", "antenna.xml", "config.xml", route_name,
                           "grid.sumocfg", "grid.launchd.xml"):
                shutil.copyfile(base / common, run_dir / common)
            one_omnet_config(run_dir, config, density, seed, logs_dir, args.sim_time_limit)
            one_sumo_config(run_dir, route_name, seed, logs_dir / f"sumo-summary-{stem}.xml")
            manifest = {"configuration": config, "density": density, "seed": seed,
                        "binary_sha256": binary_hash,
                        "scenario_condition": "controlled_stall" if seed in STALL_SEEDS else "normal",
                        "controlled_mist_stall_ms": 900 if config.startswith("Mist") and seed in STALL_SEEDS else 0,
                        "ini_sha256": hashlib.sha256((run_dir / "omnetpp.ini").read_bytes()).hexdigest()}
            (logs_dir / f"manifest-{stem}.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            output = logs_dir / f"{stem}-stdout.txt"
            command = ["opp_run", "-u", "Cmdenv", "-c", "Batch",
                       "-n", f"{veins_root / 'src/veins'}:{ROOT / 'src'}",
                       "-l", str(veins_root / "src/veins"), "-l", str(library),
                       "-f", "omnetpp.ini"]
            for attempt in range(1, 4):
                with output.open("w", encoding="utf-8") as log:
                    result = subprocess.run(command, cwd=run_dir, stdout=log,
                                            stderr=subprocess.STDOUT)
                if result.returncode == 0:
                    break
                text = output.read_text(encoding="utf-8", errors="replace")
                startup_disconnect = ("Connection to TraCI server lost." in text
                                      and "at t=0s, event #1" in text)
                if not startup_disconnect:
                    result.check_returncode()
                attempts_dir = artifact_root / "artifacts/logs/startup_failures"
                attempts_dir.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(output, attempts_dir / f"{stem}-{time.time_ns()}.txt")
                if attempt == 3:
                    result.check_returncode()
                print(f"Retry startup connection {stem} (attempt {attempt + 1}/3)", flush=True)
                time.sleep(3 * attempt)
            for extension in ("sca", "vec", "vci"):
                source = run_dir / "results" / f"Batch-#0.{extension}"
                if not source.exists():
                    raise RuntimeError(f"Missing result: {source}")
                destination = raw_dir / f"{stem}.{extension}"
                shutil.copyfile(source, destination)
            print(f"Complete {stem}", flush=True)

    keys = [(density, seed) for density in args.densities
            for seed in (args.seeds if args.seeds is not None else range(args.seed_start, args.seed_end + 1))]
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        for _ in executor.map(run_seed, keys):
            pass



if __name__ == "__main__":
    main()
