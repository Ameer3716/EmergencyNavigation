# EmergencyNavigation

Mist Computing Based Emergency Vehicle Navigation with Dynamic A*, Fog Fallback, Emergency Message Dissemination, and Traffic-Light Preemption.

This repository contains a 4 × 4 SUMO grid, a native Veins 802.11p co-simulation, four OMNeT++ configurations, a deterministic forced mist-failure run, a congestion-reroute test, event logs, result processing, and genuine SUMO-GUI exports. The scenario uses one ambulance, one stopped accident vehicle, normal traffic, three RSUs, a mist module, fog services, a cloud service, and 16 traffic lights.

The target stack is OMNeT++ 6.3.0, Veins 5.3.1, SUMO 1.18.0, and Python 3. INET 4.6.0 is an optional build dependency of Veins; this project uses the native Veins radio. The stock Veins example and the custom seed-1 suite have run on this machine. See [installation](docs/INSTALLATION.md), [methodology](docs/METHODOLOGY.md), [experiments](docs/EXPERIMENTS.md), and [progress and validation](docs/PROGRESS.md).

Run the release build and the comparison suite from the `opp_env` WSL distribution:

```bash
cd ~/workspace
opp_env run veins-5.3.1 omnetpp-6.3.0 --no-deps --no-build --build-modes release -c /mnt/d/codex/EmergencyNavigation/scripts/build.sh
opp_env run veins-5.3.1 omnetpp-6.3.0 --no-deps --no-build --build-modes release -c /mnt/d/codex/EmergencyNavigation/scripts/run_initial_suite.sh
```

Start `veins_launchd` with the exact SUMO binary first, using the command in the installation guide. Then process actual scalars and event logs:

```powershell
python analysis/process_results.py --require-all
```

The single-seed comparison is a functional prototype. Its 95% confidence intervals are left blank because one run cannot estimate sampling uncertainty. A 360-run study must follow the validation checklist and use independently generated, matched SUMO/OMNeT++ seeds.
