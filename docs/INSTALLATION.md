# Installation and execution

Verified on Windows 10 Pro with WSL2, the official `opp_env` WSL distribution (`0.36.1.20260515`), OMNeT++ 6.3.0, Veins 5.3.1, and exact SUMO 1.18.0. Python 3.14.7 and Matplotlib 3.11.1 were used for host-side data analysis and visualization. This project uses native Veins IEEE 802.11p (DSRC/WAVE at 5.89 GHz). INET 4.6.0 was installed as an optional Veins build dependency for header resolution; its radio model is not utilized for vehicular communication.

## 1. Platform Setup & Environment

The host installation used:

```powershell
wsl --install -d Ubuntu-24.04 --no-launch
curl.exe -L --fail --output D:\codex\opp_env.wsl https://github.com/omnetpp/opp_env/releases/download/wsl/opp_env.wsl
wsl --install --from-file D:\codex\opp_env.wsl --no-launch
```

The `opp_env` image mounts the Windows D: drive inside the distribution:

```bash
mkdir -p /mnt/d
mount -t drvfs D: /mnt/d
```

The versioned stack resides in `/home/opp_env/workspace`:
* OMNeT++: `/home/opp_env/workspace/omnetpp-6.3.0`
* Veins: `/home/opp_env/workspace/veins-5.3.1`
* INET (build dependency): `/home/opp_env/workspace/inet-4.6.0`

The exact SUMO 1.18.0 binary was installed from `eclipse-sumo==1.18.0` to `/home/opp_env/sumo118_pkg/sumo`:

```bash
python3 -m pip install --target /home/opp_env/sumo118_pkg 'eclipse-sumo==1.18.0'
/home/opp_env/sumo118_pkg/sumo/bin/sumo --version
```

Runtime libraries required: `libx11-6`, `libxext6`, `libxrender1`, `libgl1`. The `opp_env` Nix environment exposes SUMO 1.22.0, so the Veins launch daemon must explicitly use `/home/opp_env/sumo118_pkg/sumo/bin/sumo`.

---

## 2. Compilation

To clean and compile the custom OMNeT++/Veins shared library (`libsrc.so`) in release mode:

```powershell
wsl -d opp_env bash -l -c "source /home/opp_env/workspace/omnetpp-6.3.0/setenv && export OPP_ENV_VERSION=0.36.1 && export OMNETPP_ROOT=/home/opp_env/workspace/omnetpp-6.3.0 && export VEINS_ROOT=/home/opp_env/workspace/veins-5.3.1 && cd /mnt/d/Codex/EmergencyNavigation/src && make clean && make -j4 MODE=release"
```

---

## 3. Running Simulations

### Launching the SUMO TraCI Daemon
Before running co-simulations, start the Veins launch daemon on port 9998:

```bash
cd ~/workspace/veins-5.3.1
./bin/veins_launchd -d -p 9998 -vv -c /home/opp_env/sumo118_pkg/sumo/bin/sumo -L /mnt/d/Codex/EmergencyNavigation/artifacts/logs/grid-launchd.log
```

### Supported Experimental Configurations
The five benchmark configurations are:
1. `FogCloudAStar`: Edge/cloud route computation with static A* and active signal preemption.
2. `MistAStar`: Local ambulance OBU route computation with static A* and active signal preemption.
3. `MistDynamicAStar`: Local OBU computation with periodic 5.0 s dynamic A* updates (`minVehicles = 3`) and preemption.
4. `MistDynamicFogFallback`: Dynamic mist routing with an 800 ms watchdog delegating to nearest Fog RSU.
5. `NoPreemptionBaseline`: Control configuration using `FogCloudAStar` routing with traffic light preemption disabled.

Diagnostic configurations:
* `ForcedMistFailure`: Immediate exception-triggered fallback to the nearest Fog RSU (`fallbackReason = forced_failure`).
* `ForcedMistTimeout`: 1200 ms scheduled Mist delay exceeding the 800 ms watchdog threshold to validate genuine timeout-driven Fog takeover (`fallbackReason = watchdog_timeout`).
* `CongestionReroute`: Dynamic turn-valid rerouting around an injected downstream corridor blockage.

### Running Diagnostic & Batch Simulations

To run the individual diagnostic failover cases:

```powershell
# Diagnostic 1: Immediate exception-triggered failover
wsl -d opp_env /mnt/d/Codex/EmergencyNavigation/scripts/run_grid.sh ForcedMistFailure

# Diagnostic 2: Genuine 800 ms watchdog timeout failover
wsl -d opp_env /mnt/d/Codex/EmergencyNavigation/scripts/run_grid.sh ForcedMistTimeout
```

Execute the complete 450-run matrix (5 configurations × 3 densities × 30 seeds):

```powershell
wsl -d opp_env /mnt/d/Codex/EmergencyNavigation/scripts/run_batch_env.sh --configs FogCloudAStar MistAStar MistDynamicAStar MistDynamicFogFallback NoPreemptionBaseline --densities low medium high --seed-start 1 --seed-end 30
```

---

## 4. Result Processing & Graph Generation

To process the complete batch matrix into summary CSVs, calculate bounded Wilson confidence intervals, generate paired difference statistics, and export all 12 comparative metric figures:

```powershell
python analysis/process_results.py --batch --require-all
```

To regenerate the 3-panel thesis comparison chart:

```powershell
python scripts/generate_final_graph.py
```

To extract and summarize fallback decisions:

```powershell
python analysis/extract_fallback_evidence.py
```
