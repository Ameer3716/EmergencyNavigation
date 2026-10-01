# EmergencyNavigation development guide

The system couples OMNeT++ 6.3.0 / Veins 5.3.1 wireless simulation to SUMO 1.18.0 via TraCI. The EV application is `src/apps/EmergencyVehicleApp.cc`; local route computation is `src/apps/MistRoutingModule.cc`; traffic-light actuation is in `src/apps/TrafficLightController.cc`; result processing is in `analysis/process_results.py`.

The current study uses four matched configurations (`FogCloudAStar`, `MistAStar`, `MistDynamicAStar`, `MistDynamicFogFallback`), three densities, and seeds 1–30: 360 runs. `simulations/grid/omnetpp.ini` sets the 400 m radio neighborhood and the 800 ms fallback watchdog. Every Mist initial route decision includes a 300 ms base, 2 ms per expanded A* node, and a modeled 20 ms validation service time per actually received V2V/V2I message in the previous three seconds. The latter is an explicit simulation assumption and must not be described as measured OBU hardware performance.

Build in the `opp_env` WSL environment, run the matrix through `scripts/run_batch_env.sh`, process with `analysis/process_results.py --batch --require-all`, extract fallbacks with `analysis/extract_fallback_evidence.py`, and audit with `scripts/audit_batch.py`. The processor rejects missing run keys and stale scalar files. Historical 650 m evidence, including the removed comparison configuration, is in `archive_raw_20261001_650m/`.

Do not manually edit raw simulation logs, result CSVs, or graphs. Regenerate them from the source pipeline. The client-facing seven primary metrics and exact statistical methods are listed in `docs/METHODOLOGY.md`.
