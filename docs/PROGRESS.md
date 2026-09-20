# Progress and verification

## Stage 1: machine audit — complete

Audit date: 2026-09-20, Windows host in Asia/Karachi timezone.

| Component | Observed state |
| --- | --- |
| Windows | Windows 10 Pro, 64-bit (`Get-ComputerInfo`); WSL 2.7.12.0 kernel 6.18.33.2 |
| WSL distributions | None installed (`wsl --list --verbose`) |
| Git | 2.55.0.windows.4 |
| Python | 3.14.7 |
| SUMO | Not found on PATH |
| OMNeT++ | `opp_run` not found on PATH |
| Veins | Not present in empty project workspace |
| opp_env | Not found on PATH |
| INET | Not found; optional unless needed directly |

The version-command transcript is in `artifacts/logs/machine-audit.txt`. This audit establishes that the requested Veins example and custom simulations cannot yet run.

## Stage 2: repository structure — complete

Git repository and required directories created and committed as `ed239d8` and `28d04ce`. No simulation validation tests have passed yet.

## Stage 3: simulator installation — in progress

Ubuntu 24.04.5 LTS installed through `wsl --install -d Ubuntu-24.04 --no-launch`; launch and `/etc/os-release` inspection succeeded. The official `opp_env.wsl` image was downloaded and installed through `wsl --install --from-file D:\codex\opp_env.wsl --no-launch`. Its `opp_env --version` command reports `0.36.1.20260515`. The image is also a WSL2 distribution. Both launches reported a WSL NAT configuration fallback to VirtioProxy; neither failed.

An `opp_env` workspace was initialized at `/home/opp_env/workspace`. Dependency resolution selected `inet-4.6.0` automatically. This does not change the chosen native Veins radio model. `opp_env info veins-5.3.1` explicitly lists OMNeT++ 6.3.0 and INET 4.6.0 as compatible requirements. The `opp_env` Nix environment provides SUMO 1.22.0, so SUMO 1.18.0 was installed separately from the exact versioned `eclipse-sumo` Linux wheel at `/home/opp_env/sumo118_pkg`. Its `sumo --version` command succeeds and reports 1.18.0. Four missing Ubuntu runtime libraries were installed: `libx11-6`, `libxext6`, `libxrender1`, and `libgl1`.

OMNeT++ 6.3.0 and Veins 5.3.1 core completed release builds. An attempted Veins build with `--no-deps` failed because `opp_env` also compiles Veins' `veins_inet` subproject, which requires INET headers. This is a missing dependency in that attempted build, not evidence of a version incompatibility. A release-only build with INET 4.6.0 restored is in progress. The native Veins radio remains the planned radio model for custom vehicles.

## Stage 4: original Veins example — passed

The unmodified Veins `examples/veins` `Default` configuration ran under Cmdenv with OMNeT++ 6.3.0 and Veins 5.3.1 to its 200-second simulation time limit, finishing at event 15,933 with exit code 0. The launcher was explicitly configured with `/home/opp_env/sumo118_pkg/sumo/bin/sumo`; its log shows that exact command and SUMO exit code 0. Evidence: `artifacts/logs/veins-example-stdout.txt` and `artifacts/logs/veins-example-launchd.log`. This verifies the requested core version combination before custom scenario development. It does not validate any custom project feature.

## Stage 5: SUMO-only grid — passed for seed 1

`grid.net.xml` is a 4 × 4, 300-metre grid with 48 directed road edges and 16 traffic lights. Normal trips use fixed random seed 1 and low, medium, and high headways of 5.0, 2.5, and 1.8 seconds during the first 360 seconds. The ambulance starts on A0A1, waits until 65 seconds in the SUMO-only run, and has a connected initial route to D2D3. The accident vehicle enters D3C3 at 57.5 seconds, stops near the destination intersection, and is parked so it does not permanently block the only lane. The comparison runs will use an accident occurrence time of 60 seconds and detect a stationary vehicle after three seconds.

All three density/seed-1 SUMO runs reached their 900-second end without SUMO errors. The ambulance arrived at 295.0 seconds (low), 296.5 seconds (medium), and 325.5 seconds (high). The medium-run FCD file shows 144 normal vehicles observed and moving, the accident vehicle at zero speed from 63 through 66 seconds, and the ambulance finishing within 36.25 metres of the accident vehicle. `scripts/validate_sumo.py` passed; see `artifacts/logs/sumo-validation.json`, per-density SUMO logs, tripinfo files, and `sumo-medium-fcd.xml`. This validates the SUMO-only scenario, not any Veins communication or routing feature.

The first high-demand setting of 1.25 seconds created a persistent gridlock; that exploratory failed run is retained as `sumo-high-1800.log`. The accident vehicle initially blocked the destination approach; moving it to the adjacent approach and using SUMO roadside parking resolved this. The accepted high setting remains above medium demand and reaches the accident within the run duration.

## Stage 6: custom grid connected to Veins — passed

`EmergencyGridScenario.ned` extends the native Veins scenario with three RSUs. The initial connection test uses the stock Veins vehicle, RSU, and traffic-light applications; custom applications are not yet implemented. A dedicated launcher on port 9998 started SUMO 1.18.0 with the grid network and traffic files. OMNeT++ Cmdenv ran the custom `Smoke` configuration to 120 s, event 27,503, with exit code 0. The launcher's SUMO process also exited 0, with 50 vehicles known to SUMO and 47 active at t=120 s. Raw `.sca`, `.vec`, and `.vci` results were copied to `results/raw/`. Evidence: `artifacts/logs/grid-Smoke-stdout.txt` and `artifacts/logs/grid-launchd.log`.

The first custom run exposed a copied Veins obstacle-shadowing model that requires map buildings; this synthetic grid has none. Removing that model from the custom `config.xml` allowed the run to complete. The physical radio remains Veins IEEE 802.11p with path loss and MAC/channel delays.

## Stage 7: entity module instantiation — passed; behavior pending

The custom C++/NED library builds in release mode using `scripts/build.sh`. A second 120-second co-simulation completed with 49 normal vehicle applications, one emergency vehicle application, three RSU applications, one mist module inside the emergency vehicle, three fog service modules inside the RSUs, one cloud service, one metrics collector, and 16 traffic-light controller modules. `scripts/validate_entities.py` passed using the generated OMNeT++ scalar file; evidence is `artifacts/logs/entity-validation.json`. These modules currently establish topology and application roles only; message dissemination, routing, fallback, preemption, and metrics behavior remain unimplemented.

`EmergencyNavigation.msg` defines the requested emergency, traffic, routing, cloud, and traffic-light packet types and compiles with OMNeT++ 6.3.0. Packet definitions alone do not validate delivery.
