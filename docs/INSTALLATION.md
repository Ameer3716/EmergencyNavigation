# Installation and execution

Verified on Windows 10 Pro with WSL2, the official `opp_env` WSL distribution (`0.36.1.20260515`), OMNeT++ 6.3.0, Veins 5.3.1, and an exact SUMO 1.18.0 wheel. Python 3.14.7 and Matplotlib 3.11.1 were used for host-side analysis. This project uses native Veins IEEE 802.11p. INET 4.6.0 was installed as an optional Veins build dependency; its radio is not used in these vehicles.

The host installation used:

```powershell
wsl --install -d Ubuntu-24.04 --no-launch
curl.exe -L --fail --output D:\codex\opp_env.wsl https://github.com/omnetpp/opp_env/releases/download/wsl/opp_env.wsl
wsl --install --from-file D:\codex\opp_env.wsl --no-launch
```

The `opp_env` image needed a mount of the Windows D: drive inside the distribution:

```bash
mkdir -p /mnt/d
mount -t drvfs D: /mnt/d
```

The project uses `/home/opp_env/workspace` for the versioned stack. The following release build was used:

```bash
cd ~/workspace
opp_env install veins-5.3.1 omnetpp-6.3.0 --build-modes release
```

An `opp_env ... --smoke-test` variant compiled the optional Veins-INET integration and ran its smoke simulation, but returned exit code 1 during its launchd cleanup (`kill: No such process`). The independently run stock native Veins example passed to 200 s, exit code 0; see `artifacts/logs/veins-example-stdout.txt` and its launchd log. This is a test-wrapper cleanup failure, not a version change. The exact SUMO binary was installed from `eclipse-sumo==1.18.0` to `/home/opp_env/sumo118_pkg/sumo`:

```bash
python3 -m pip install --target /home/opp_env/sumo118_pkg 'eclipse-sumo==1.18.0'
/home/opp_env/sumo118_pkg/sumo/bin/sumo --version
```

Ubuntu runtime packages `libx11-6`, `libxext6`, `libxrender1`, and `libgl1` were needed. The `opp_env` Nix environment exposes SUMO 1.22.0, so the Veins launcher must explicitly use the 1.18.0 binary.

Start the SUMO launcher in the `opp_env` distribution before a co-simulation:

```bash
cd ~/workspace/veins-5.3.1
./bin/veins_launchd -d -p 9998 -vv -c /home/opp_env/sumo118_pkg/sumo/bin/sumo -L /mnt/d/codex/EmergencyNavigation/artifacts/logs/grid-launchd.log
```

Build and run from a WSL shell:

```bash
cd ~/workspace
opp_env run veins-5.3.1 omnetpp-6.3.0 --no-deps --no-build --build-modes release -c /mnt/d/codex/EmergencyNavigation/scripts/build.sh
EN_CONFIG=MistAStar opp_env run veins-5.3.1 omnetpp-6.3.0 --no-deps --no-build --build-modes release -k EN_CONFIG -c /mnt/d/codex/EmergencyNavigation/scripts/run_grid.sh
```

Valid comparison configuration names are `FogCloudAStar`, `MistAStar`, `MistDynamicAStar`, and `MistDynamicFogFallback`. `ForcedMistFailure` and `CongestionReroute` are validation configurations. `scripts/run_initial_suite.sh` executes the four comparison configurations and the forced-failure case, then copies their raw OMNeT++ files to `results/raw/`. From Windows, run `python analysis/process_results.py --require-all` to generate processed CSV and PNG graphs. Run `wsl -d opp_env -- python3 /mnt/d/codex/EmergencyNavigation/scripts/capture_sumo.py` for genuine SUMO-GUI frames in `artifacts/screenshots/`.
