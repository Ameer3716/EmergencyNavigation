# EmergencyNavigation

A hierarchical **Mist / Fog / Cloud** VANET emergency-vehicle navigation framework built on **OMNeT++ 6.3.0**, **Veins 5.3.1**, and **SUMO 1.18.0**.

The simulation models an ambulance navigating a signalized urban grid. It evaluates three routing tiers (on-board Mist OBU, RSU-based Fog, remote Cloud) against five experimental configurations, measuring response time, congestion rerouting, watchdog failover, and V2I traffic-light preemption across 450 reproducible runs (30 seeds × 3 densities × 5 configs).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Repository Structure](#2-repository-structure)
3. [Installation](#3-installation)
4. [Build](#4-build)
5. [Running Experiments](#5-running-experiments)
6. [Processing Results & Graphs](#6-processing-results--graphs)
7. [Experimental Configurations](#7-experimental-configurations)
8. [Architecture Overview](#8-architecture-overview)
9. [Key Parameters](#9-key-parameters)

For a direct build-to-batch walkthrough, start at [Installation](#3-installation) and follow sections 3–6 in order. All simulation commands there run inside the `opp_env` WSL distribution, from the repository root.

---

## 1. Prerequisites

| Software | Version | Notes |
|---|---|---|
| Windows 10/11 | — | WSL2 must be enabled |
| WSL2 distribution | `opp_env` 0.36.1 | Provides the matching framework environment |
| OMNeT++ | 6.3.0 | Inside `opp_env` at `/home/opp_env/workspace/omnetpp-6.3.0` |
| Veins | 5.3.1 | Inside `opp_env` at `/home/opp_env/workspace/veins-5.3.1` |
| SUMO | 1.18.0 | Binary at `/home/opp_env/sumo118_pkg/sumo/bin/sumo` |
| Python | ≥ 3.11 | For analysis scripts; see `requirements.txt` |

### Obtain the opp_env WSL image

If the `opp_env` distribution is already installed with the versions above, continue to section 3. Otherwise, install WSL2 in an Administrator PowerShell window, restart if requested, and import the [official `opp_env` WSL image](https://github.com/omnetpp/opp_env):

```powershell
wsl --install
wsl --update
curl.exe -L https://github.com/omnetpp/opp_env/releases/download/wsl/opp_env.wsl | wsl --import opp_env -
```

Start it with `wsl -d opp_env --cd ~`. Inside WSL, install the matching frameworks in `/home/opp_env/workspace` if they are not already present:

```bash
mkdir -p /home/opp_env/workspace
cd /home/opp_env/workspace
opp_env init
opp_env install veins-5.3.1 inet-4.6.0 omnetpp-6.3.0 --no-pause
python3 -m pip install --target /home/opp_env/sumo118_pkg 'eclipse-sumo==1.18.0'
```

The build and batch commands below were tested with that installed stack. See [installation details](docs/INSTALLATION.md) for the host setup.

---

## 2. Repository Structure

```
EmergencyNavigation/
├── src/                          # C++ simulation source code
│   ├── apps/                     # Application layer modules
│   │   ├── EmergencyVehicleApp.cc/.h     # Ambulance EV logic, routing, watchdog
│   │   ├── NormalVehicleApp.cc           # Background vehicle beaconing & relay
│   │   ├── RsuApp.cc                     # RSU beacon aggregation & preemption
│   │   ├── MistRoutingModule.cc/.h       # Local A* on the OBU
│   │   ├── FogService.cc/.h              # RSU-level fog computation
│   │   ├── CloudService.cc/.h            # Cloud server with 150 ms WAN latency
│   │   ├── TrafficLightController.cc/.h  # V2I preemption via TraCI
│   │   └── EmergencyRelayApp.cc/.h       # Multi-hop EM forwarding (TTL, dup suppression)
│   ├── routing/                  # A* router and road graph
│   │   ├── AStarRouter.cc/.h
│   │   └── RoadGraph.cc/.h
│   ├── metrics/                  # Scalar & vector metric collection
│   │   └── MetricsCollector.cc/.h
│   └── messages/                 # OMNeT++ message definitions (.msg)
│       └── EmergencyNavigation.msg
├── simulations/
│   └── grid/                     # SUMO network + OMNeT++ configuration
│       ├── omnetpp.ini            # All experiment configurations
│       ├── grid.net.xml           # 4×4 signalized grid road network
│       ├── grid.sumocfg           # SUMO launch config
│       ├── grid.launchd.xml       # Veins launchd config
│       ├── normal-{low,medium,high}-seed1.rou.xml  # Traffic demand files
│       └── special.rou.xml        # EV + accident vehicle routes
├── analysis/
│   ├── process_results.py         # Aggregates .sca files → summary CSVs + 95% CIs
│   └── extract_fallback_evidence.py  # Extracts watchdog/fallback event evidence
├── scripts/
│   ├── build.sh                   # Compiles the shared library inside WSL
│   ├── run_batch.py               # Python batch orchestrator
│   ├── run_batch_env.sh           # WSL wrapper for batch runs
│   ├── generate_demand.py         # Generates SUMO traffic demand files
│   ├── validate_integrated.py     # Full automated validation suite
│   ├── validate_emergency.py      # Emergency message delivery checks
│   ├── validate_entities.py       # Entity-presence checks
│   ├── validate_sumo.py           # SUMO network/demand validation
│   ├── audit_batch.py             # Batch result auditing (425/425 runs)
│   ├── verify_response_times.py   # Response-time formula verification
│   └── run_diagnostic_timeout.sh  # Watchdog / timeout diagnostic run
├── tests/
│   ├── routing_test.cc            # C++ unit tests for A* router
│   └── test_thesis_deliverable.py # Integration test suite
├── artifacts/
│   ├── audit_report.json          # Batch audit results
│   ├── checksums.sha256           # Historical evidence-package manifest; see note below
│   ├── event_timeline_verification.csv
│   └── response_time_verification.csv
├── docs/
│   ├── INSTALLATION.md            # Detailed platform setup guide
│   ├── EXPERIMENTS.md             # Full experimental matrix & config definitions
│   ├── METHODOLOGY.md             # Mathematical models, cost functions, metric definitions
│   └── VERIFICATION.md            # 23-point verification report & statistical tables
├── results/
│   ├── raw/                       # OMNeT++ .sca/.vec/.vci files (generated, gitignored)
│   ├── processed/                 # Summary CSVs (generated, gitignored)
│   └── graphs/                    # PNG comparison charts (generated, gitignored)
├── AGENTS.md                      # Architecture reference & verified engineering decisions
├── PROJECT_SPEC.md                # Canonical project requirements specification
└── README.md
```

---

## 3. Installation

### Step 1 — Enter WSL and clone the repository

In PowerShell, start the installed `opp_env` distribution:

```powershell
wsl -d opp_env --cd /home/opp_env/workspace
```

Run every Bash command below in that WSL terminal. Clone into the WSL filesystem:

```bash
cd /home/opp_env/workspace
git clone https://github.com/Ameer3716/EmergencyNavigation.git
cd EmergencyNavigation
```

### Step 2 — Verify the exact simulation tools

```bash
/home/opp_env/sumo118_pkg/sumo/bin/sumo --version
test -d /home/opp_env/workspace/omnetpp-6.3.0
test -d /home/opp_env/workspace/veins-5.3.1
test -d /home/opp_env/workspace/inet-4.6.0
```

The SUMO output must report version 1.18.0. The three `test` commands should finish without errors. If any check fails, complete [the platform setup](docs/INSTALLATION.md) first.

### Step 3 — Enter the full `opp_env` toolchain

```bash
cd /home/opp_env/workspace
opp_env shell veins-5.3.1 inet-4.6.0 omnetpp-6.3.0
export VEINS_ROOT=/home/opp_env/workspace/veins-5.3.1
export SUMO_HOME=/home/opp_env/sumo118_pkg/sumo
cd /home/opp_env/workspace/EmergencyNavigation
opp_run --version
```

`opp_run` must report OMNeT++ 6.3.0. Enter this toolchain again in each new WSL terminal before building or running the simulation. Sourcing OMNeT++ `setenv` alone does not provide the full build toolchain in this image.

---

## 4. Build

Inside the configured `opp_env` shell, compile the custom OMNeT++ shared library. `src/Makefile` is generated by this script and is intentionally not committed:

```bash
bash scripts/build.sh
find src/out -name libsrc.so -print
```

A successful build produces `src/out/clang-release/libsrc.so` or `src/out/gcc-release/libsrc.so`. The run scripts select the available build automatically.

---

## 5. Running Experiments

### Quick single-seed smoke test

Run a single seed to verify the environment end-to-end before a full batch:

```bash
mkdir -p artifacts/logs
python3 "$VEINS_ROOT/bin/veins_launchd" -d -p 9998 -vv \
  -c /home/opp_env/sumo118_pkg/sumo/bin/sumo \
  -L "$PWD/artifacts/logs/grid-launchd.log"
bash scripts/run_grid.sh Smoke
```

The Smoke configuration ends at simulation time 120 s. It writes `simulations/grid/results/Smoke-#0.sca`, `.vec`, and `.vci`, plus `artifacts/logs/grid-Smoke-stdout.txt`. Check the last lines of that log for `End.` before continuing.

### One matched seed before the full batch

This runs all five configurations for one low-density seed. The batch wrapper starts `veins_launchd` automatically if port 9998 is not already listening.

```bash
bash scripts/run_batch_env.sh \
  --configs FogCloudAStar MistAStar MistDynamicAStar MistDynamicFogFallback NoPreemptionBaseline \
  --densities low --seed-start 1 --seed-end 1
```

Verify that each configuration has three nonempty raw files (`.sca`, `.vec`, `.vci`) and a batch stdout log:

```bash
ls -lh results/raw/*-low-seed1.{sca,vec,vci}
ls -lh artifacts/logs/batch/*-low-seed1-stdout.txt
```

### Full batch (450 runs)

Runs all 5 configurations × 3 densities × 30 seeds. Estimated time: 3–6 hours depending on hardware.

```bash
bash scripts/run_batch_env.sh \
  --configs FogCloudAStar MistAStar MistDynamicAStar MistDynamicFogFallback NoPreemptionBaseline \
  --densities low medium high --seed-start 1 --seed-end 30
```

Raw results (`.sca`, `.vec`, `.vci`) are written to `results/raw/`.  
Event logs (`.csv`) and stdout logs are written to `artifacts/logs/batch/`. Completed runs with all three nonempty raw files are skipped on a repeat invocation; use `--force` only to rerun selected cases. Plan for several gigabytes of free disk space.

### Validate generated results

Run the result processing commands in section 6 only after all 450 cases have completed. The repository does not include the original 450-run output package. Some legacy validation scripts also expect that earlier evidence package and are not suitable as a fresh-clone smoke test.

The tracked `artifacts/checksums.sha256` records the original evidence package, including generated outputs absent from a fresh clone. It cannot be fully verified against the source checkout. After reproducing and auditing the results, run `python scripts/generate_checksums.py` to create `artifacts/checksums-local.sha256` for the local package. The script preserves the historical manifest; graph image hashes can still differ with rendering environment.

---

## 6. Processing Results & Graphs

Once the full batch has finished, leave the `opp_env` shell with `exit`. From the repository root in the WSL terminal, create a separate analysis environment with `uv` (included in the tested `opp_env` image), install the pinned dependencies, and process the batch. The image's system Python lacks `ensurepip`, so `python3 -m venv` is not suitable here:

```bash
cd /home/opp_env/workspace/EmergencyNavigation
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
source .venv/bin/activate
python analysis/process_results.py --batch --require-all
python scripts/generate_final_graph.py
python analysis/extract_fallback_evidence.py
python scripts/verify_response_times.py
python scripts/audit_batch.py
python scripts/generate_checksums.py
```

`--require-all` rejects an incomplete 450-run matrix. The historical screenshot and diagnostic evidence is not bundled with the source clone, so checks that require those files may still report missing evidence; see the checksum note above.

Outputs:
- `results/processed/summary-batch.csv` — mean ± 95% CI for every metric per config/density
- `results/processed/individual_runs-batch.csv` — per-run scalars
- `results/graphs/*.png` — one chart per metric per density

---

## 7. Experimental Configurations

| Config | Routing Tier | Dynamic Rerouting | Fog Fallback | TL Preemption |
|---|---|---|---|---|
| `FogCloudAStar` | Fog → Cloud | No | — | Yes |
| `MistAStar` | Mist (OBU) | No | No | Yes |
| `MistDynamicAStar` | Mist (OBU) | Yes (5 s) | No | Yes |
| `MistDynamicFogFallback` | Mist (OBU) | Yes (5 s) | Yes (800 ms watchdog) | Yes |
| `NoPreemptionBaseline` | Fog → Cloud | No | — | **No** |

Traffic densities: `low` (~5 vehicles), `medium` (~15 vehicles), `high` (~30 vehicles).  
Seeds: 1–30 per density per configuration = **450 total runs**.

---

## 8. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  Ambulance (node[0])                                                         │
│  EmergencyVehicleApp  ──→  MistRoutingModule (local A*)                      │
│       │  watchdog 800 ms                                                     │
│       ↓  (on timeout / failure)                                              │
│  FogService request  ──→  RSU (RsuApp)  ──→  FogService (local computation) │
│                                │                                             │
│                                ↓  (if fog unavailable)                      │
│                          CloudService (150 ms WAN backhaul)                  │
│                                                                              │
│  V2I Preemption: EV → RSU → TrafficLightController → SUMO TraCI             │
│  Multi-hop EM:   EV → NormalVehicleApp relay (TTL, dup suppression)         │
└──────────────────────────────────────────────────────────────────────────────┘
```

The TraCI interface connects OMNeT++/Veins to SUMO over TCP port 9998 via `veins_launchd`.

---

## 9. Key Parameters

These are defined in `simulations/grid/omnetpp.ini` and can be changed per experiment:

| Parameter | Default | Description |
|---|---|---|
| `watchdogThreshold` | `800ms` | Mist computation deadline before fog fallback |
| `releaseSpeed` | `13.89 m/s` (50 km/h) | EV speed after route is applied |
| `maxHops` | `10` | Maximum EM relay hops |
| `minVehicles` | `3` | Min vehicles on edge to trust congestion estimate |
| `preemptionDistance` | `250 m` | Distance at which TL preemption is triggered |
| `dynamicRerouteInterval` | `5 s` | Periodic rerouting check interval |
| `fogLatency` | `~50 ms` | Wireless round-trip to RSU |
| `cloudLatency` | `150 ms` | One-way WAN backhaul to cloud server |

---

## License

This project is provided for research and academic use. See individual source files for copyright notices.
