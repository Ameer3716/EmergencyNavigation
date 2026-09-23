# Developer & Agent Guide: System Architecture & Verification Continuity

This document provides architectural context, implementation history, and operational guidelines for AI agents and developers working on the EmergencyNavigation codebase.

---

## 1. System Architecture & Components

The system couples **OMNeT++ 6.3.0 / Veins 5.3.1** (wireless communication and application logic) with **SUMO 1.18.0** (microscopic road traffic and signal actuation) over TraCI on port 9998:

* **Simulation Core (`src/apps/`)**:
  * `EmergencyVehicleApp`: Deployed on the ambulance (`node[0]`). Implements the initial speed-hold at $t=0.1\text{ s}$ (via TraCI `setSpeed(0)`), processes incoming EMs, coordinates route calculation (mist vs fog/cloud), performs periodic 5 s dynamic route evaluations, handles the 800 ms failover watchdog, and issues V2I traffic light preemption requests.
  * `NormalVehicleApp`: Deployed on background traffic (`node[1..N]`). Periodically broadcasts 1.0 s IEEE 802.11p beacons containing speed, position, and road edge ID, and participates in multi-hop EM forwarding with duplicate suppression.
  * `RsuApp`: Deployed on Roadside Units (RSU 0, 1, 2). Collects beacons, computes rolling average edge speeds, broadcasts periodic edge status tables, detects accidents via standstill duration $\ge 3\text{ s}$, and delegates preemption requests to local traffic light controllers.
  * `MistRoutingModule`: C++ routing module on the EV implementing local Static and Dynamic A*.
  * `FogService` & `CloudService`: Compute routes on behalf of the EV when fog/cloud routing is active. Fog adds local wireless delay; Cloud adds 150 ms one-way WAN backhaul latency.
  * `TrafficLightController`: TraCI interface controlling the 16 signalized intersections. Executes yellow (2s) $\to$ all-red (1s) $\to$ green hold $\to$ program restoration.
  * `MetricsCollector`: TraCI listener polling `VAR_NEXT_TLS (0x70)` every 500 ms to compute `traffic_light_wait_s` and recording mobility scalars.

---

## 2. Key Engineering Decisions & Verified Fixes

1. **Ambulance Initial Speed-Hold (`EmergencyVehicleApp.cc`)**:
   * *Issue*: SUMO accelerates vehicles immediately upon departure ($t=1.0\text{ s}$) before the EM is processed ($t=67\text{ s}$), masking route decision latency.
   * *Fix*: Ambulance is immobilized at $t=0.1\text{ s}$ via TraCI `setSpeed(0)` and released with `par("releaseSpeed")` only after initial route application. This ensures route computation latency is accurately reflected in response time.

2. **Single-Vehicle Deceleration Guard (`minVehicles = 3`) (`AStarRouter.cc`)**:
   * *Issue*: In high-density seed 3, a single background vehicle momentarily braking for a yellow signal reduced edge mean speed, causing Dynamic A* to choose an excessive 2380 m detour (+44 s response time).
   * *Fix*: Dynamic cost adjustments require at least 3 vehicles on the edge (`minVehicles = 3`). Isolated single-vehicle decelerations are ignored, eliminating false detours in low traffic and high seed 3. In high-density traffic, genuine queue accumulations (such as 3 queued vehicles at a red signal in seed 22) are legitimately evaluated as congestion, resulting in higher variance for Dynamic A*.

3. **TraCI TLS Preemption Green-Wave Timing**:
   * Preemption triggers at 250 m (~18 s before arrival at 13.89 m/s). Phase transition requires 3.15 s (150 ms delay + 2.0 s yellow + 1.0 s all-red), establishing green 14.8–16.2 s before EV arrival. The signal holds green for up to 25.0 s.
   * Preemption eliminates ~98–100% of traffic light delay (0.00 s in low and high densities; 0.59 s in medium density where an isolated wireless packet collision at RSU 1 in seed 14 dropped a single preemption request).

4. **Dual Traffic Signal Delay Metrics**:
   * `traffic_light_wait_s`: Standstill ($v < 0.1\text{ m/s}$) within $\le 20\text{ m}$ of the stop line.
   * `ev_delay_vs_freeflow_s`: Total travel delay relative to 140.0 s unimpeded green-wave travel time (`max(0.0, ev_travel_s - 140.0)`).
   * Empirical trajectory analysis of sample runs demonstrates that the gap between travel savings and stop-line waiting comprises upstream queueing (>20 m), creeping (0.1–5.0 m/s), and kinematic recovery.

5. **Configurable Hop Limit (`maxHops`)**:
   * Defined in `EmergencyRelayApp.ned` (default: 10), dynamically accessed via `par("maxHops")`, and configurable per experiment in `omnetpp.ini`. Validated via TTL=1 expiration test.

6. **Multi-Tier Fallback Architectures (`EmergencyVehicleApp.cc` & `MistRoutingModule.cc`)**:
   * *Synchronous Exception Fallback*: Triggered immediately if local Mist route computation throws an exception or aborts (`ForcedMistFailure`). Local computation is aborted without recording completion time, and an immediate request is dispatched to the nearest Fog RSU (`fallbackReason = forced_failure`, decision latency 0.3248 s, watchdog canceled/not expired).
   * *Deadline / Watchdog Timeout Fallback*: An 800 ms watchdog timer (`watchdogThreshold = 800ms`) monitors local Mist computation. If calculation delay exceeds 800 ms (`ForcedMistTimeout` with 1200 ms scheduled delay), the watchdog fires at $t = \text{mist\_start} + 0.8\text{ s}$ ($t=67.8273\text{ s}$), cancels pending Mist computation, and applies the Fog RSU route at $t=68.1540\text{ s}$ (`fallbackReason = watchdog_timeout`, latency 1.1267 s).
   * *Invalid-Route Fallback*: If a locally computed route fails turn connectivity validation, failover to the Fog RSU is triggered.
   * *Unavailable-Mist Fallback*: If local OBU telemetry or routing resources are uninitialized, route planning delegates directly to the Fog tier.

---

## 3. Environment & Execution Workflows

* **Host Platform**: Windows 10 Pro with WSL2.
* **WSL Distribution**: `opp_env` (contains OMNeT++ 6.3.0, Veins 5.3.1, Nix dependencies).
* **Exact SUMO Binary**: `/home/opp_env/sumo118_pkg/sumo/bin/sumo` (version 1.18.0).
* **Launch Daemon**: `veins_launchd` runs on port 9998 inside WSL.

### Clean Build Procedure
```bash
wsl -d opp_env bash -l -c "source /home/opp_env/workspace/omnetpp-6.3.0/setenv && export OPP_ENV_VERSION=0.36.1 && export OMNETPP_ROOT=/home/opp_env/workspace/omnetpp-6.3.0 && export VEINS_ROOT=/home/opp_env/workspace/veins-5.3.1 && cd /mnt/d/Codex/EmergencyNavigation/src && make clean && make -j4 MODE=release"
```

### Running Batch Experiments
```bash
wsl -d opp_env /mnt/d/Codex/EmergencyNavigation/scripts/run_batch_env.sh --configs FogCloudAStar MistAStar MistDynamicAStar MistDynamicFogFallback NoPreemptionBaseline --densities low medium high --seed-start 1 --seed-end 30
```

### Processing Results & Generating Graphs
```powershell
python analysis/process_results.py --batch --require-all
python scripts/generate_final_graph.py
python analysis/extract_fallback_evidence.py
```

---

## 4. Verification Check History (23/23 Checks Passed)

1. `SUMO network loads`: Passed (`sumo-validation.json`).
2. `Veins connects with SUMO`: Passed (`grid-launchd.log`).
3. `Vehicles appear and move`: Passed (TraCI mobility logs).
4. `Direct RSU → EV EM`: Passed (`emergency-DirectDelivery.csv`, hop 0).
5. `Vehicle multihop EM`: Passed (`emergency-VehicleRelay.csv`, hop 2).
6. `RSU multihop EM`: Passed (`emergency-RsuRelay.csv`, hop 1).
7. `Duplicate suppression`: Passed (283 duplicate suppressed rows).
8. `TTL termination`: Passed (TTL=1 run has 0 deliveries).
9. `Static A* connected route`: Passed.
10. `Dynamic A* route change`: Passed (`CongestionReroute` alternates route).
11. `Mist meets watchdog`: Passed (0.326 s < 0.8 s).
12. `Forced mist failure`: Passed (`fallbackReason = forced_failure`).
13. `Forced mist timeout`: Passed (`fallback-timeout-verified.csv` records genuine 800 ms watchdog timeout and fog takeover applied at t=68.15 s).
14. `Correct TL phase changes`: Passed.
15. `Safe transition phases`: Passed (yellow $\to$ all-red $\to$ green).
16. `Original program restored`: Passed (`program_restored` logged).
17. `EV reaches accident`: Passed (`accidentArrivalConfirmed = 1`).
18. `Result/log files generated`: Passed (`.sca`, `.vec`, `.vci`).
19. `Metric formulas`: Passed (`validate_integrated.py` and `audit_batch.py`; 425/425 delivered response times verified against raw `.sca` files; 25 partition runs classified as not applicable).
20. `TraCI TLS wiring & preemption`: Passed (margins +15.0 to +16.2 s).
21. `Network partition analysis`: Passed (Wilson CIs: 28/30 low, 29/30 med, 28/30 high).
22. `Balanced batch matrix`: Passed (exactly 450 runs across 5 configs and 3 densities).
23. `No-preemption baseline control`: Passed (`NoPreemptionBaseline` evaluated across all 30 seeds per density, 150 total runs).
