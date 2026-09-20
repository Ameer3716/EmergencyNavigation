# Verification report

Verified on 2026-09-20 using OMNeT++ 6.3.0, Veins 5.3.1, SUMO 1.18.0, and seed 1 unless stated otherwise. The stock Veins example completed at t=200 s. The custom four-configuration suite completed at t=900 s for each configuration. `scripts/validate_emergency.py`, `scripts/test_routing.sh`, and `scripts/validate_integrated.py` passed. Evidence is under `artifacts/logs/`, `results/raw/`, and `results/processed/`.

| # | Test | Result and evidence |
| --- | --- | --- |
| 1 | SUMO network loads | Passed: SUMO-only validation for all three seed-1 densities, `sumo-validation.json`. |
| 2 | Veins connects with SUMO | Passed: stock example and custom `grid-*-stdout.txt`/launcher logs. |
| 3 | Vehicles appear and move | Passed: SUMO FCD and OMNeT++ mobility logs. |
| 4 | Direct RSU → EV EM | Passed: `emergency-DirectDelivery.csv`, hop count 0. |
| 5 | Vehicle multihop EM | Passed: `emergency-VehicleRelay.csv`, hop count 2. |
| 6 | RSU multihop EM | Passed: `emergency-RsuRelay.csv`, hop count 1. |
| 7 | Duplicate suppression | Passed: 283 duplicate rows in the vehicle-relay validation log. |
| 8 | TTL termination | Passed: TTL=1 run has one source transmission, seven expiration rows, no EV delivery. |
| 9 | Static A* connected route | Passed: independent C++ routing test and applied SUMO route. |
| 10 | Dynamic A* route change | Passed: `CongestionReroute` selected an alternate edge sequence after injected C1C2 congestion; SUMO accepted the turn-valid route. |
| 11 | Mist meets watchdog | Passed: normal fallback configuration decision completed in 0.324 s, under 0.8 s. |
| 12 | Forced mist failure | Passed: `fallback-forced-verified.csv` records `forced_failure`. |
| 13 | Fog route reaches EV | Passed: `routing-ForcedMistFailure-verified.csv` records a fog route applied by the EV. |
| 14 | Correct TL phase changes | Passed: `traffic-light-MistAStar-verified.csv` records the requested incoming edge and actual green state for six lights. |
| 15 | Safe transition phases | Passed: actual SUMO states show yellow followed by all-red before green. |
| 16 | Original program restored | Passed: all six recorded preemptions have `program_restored` events. |
| 17 | EV reaches accident | Passed: all four main configurations record `accidentArrivalConfirmed=1`, at t=205 s. |
| 18 | Result/log files generated | Passed: nonempty `.sca`, `.vec`, `.vci` for each main run and CSV event logs. |
| 19 | Metric formulas | Passed: `validate_integrated.py` recomputes PDR, E2E delay, NRL, control bytes, and response time from raw rows/scalars. Manual seed-1 check follows. |

Manual check for `MistAStar`, medium traffic, seed 1: one EM generated at t=67 s and processed by the ambulance at t=67.0188 s, so PDR is 1/1=1 and E2E delay is 0.0188 s. SUMO arrival is t=205 s, so response time is 205−67=138 s. The raw application scalars sum to 46,655 control transmissions and 30 EM transmissions; NRL is (46,655+30)/1=46,685. The useful payload is 256 bytes, so throughput over the 900-second measurement period is 256×8/900=2.2756 bit/s. The route decision began at t≈67.0188 s and was applied 0.326 s later. These numbers match `results/processed/individual_runs.csv` within printed rounding.

The single-seed comparison cannot estimate standard deviation or 95% confidence intervals. All four main runs arrived at t=205 s, so this seed does not demonstrate an EV response-time advantage. The isolated congestion stress test changed route but did not confirm arrival before its 300-second time limit; it validates the reroute trigger and SUMO route acceptance, not improved response time under congestion. A full matched-seed experiment is required for an efficacy conclusion. GUI screenshots of RSU placement and individual radio events have not been captured; their event logs are preserved instead. The available SUMO-GUI frames are genuine exports from a SUMO-only run and must not be interpreted as Veins radio screenshots.
