# Requirements evidence and controlled incident comparison

The ordinary 450-run batch, the 18 signal validation runs, and this separate 360-run incident comparison answer different questions. The incident experiment tests route adaptation after the initial decision. It does not replace ordinary traffic results or establish how often incidents occur in practice.

## Fixed incident design

All four algorithms use the same 30 seeds at each density, original background trips, frozen binary, safety controller and stall assignment. Dynamic Mist uses advance signal requests (250 m or 20 s); Fog/Cloud and static Mist use reactive requests (100 m or 8 s). All may retry every five seconds without extending an active hold. The comparison therefore measures routing and signal policy together. The input requests three passenger vehicles on C1C2 at 90, 91 and 92 seconds, with stops until 250 seconds. SUMO safety checks may delay insertion; requested times are not assumed to be actual entry times. There is no injected routing cost or privileged incident notification: ordinary beacons and RSU reports provide observations. FCD verifies the realised obstruction in every run, with at least one incident vehicle still stopped at the end of the planned interval. Initial routes must be applied before the incident. All runs have a 900 second horizon.

Routing retains its existing minimum of three observed vehicles for a congestion adjustment. Incident vehicles and ordinary queued vehicles can provide those observations. The incident vehicles are additional to the 72/144/200 generated background trips. Demand counts are not simultaneous occupancy. Every delivered-alert run must reach the destination. Undelivered alerts remain in the matrix; delivery-dependent means exclude them and report their sample sizes.

The seed labels vary demand generation and OMNeT++ streams. Veins launchd retains the original manager default, using SUMO driving seed 0 for run number zero. Driving randomness is common across cases; route-generation seeds still vary routes and entry edges. This preserves the original experiment and does not claim independently varied SUMO driver seeds. The [retained launchd history](../artifacts/congestion_validation/launchd_history.log) records the effective seed; it includes previous suites and startup attempts as well as this matrix.

The advance-priority framework was screened on seeds 1, 4, 22 and 27 at all densities before the fixed full matrix. Screening checks mechanism operation, not an acceptance threshold for favourable results. Previous evidence and pilot workspaces are retained. Neither effect size nor significance is a pass criterion.

## Measured incident response

| Density | Algorithm | Arrived samples | Mean response s | Mean route changes per scheduled run |
| --- | --- | ---: | ---: | ---: |
| low | Fog/Cloud | 24 | 266.292 | N/A |
| low | Mist | 24 | 266.500 | N/A |
| low | Dynamic Mist | 24 | 144.521 | 0.800 |
| low | Mist + Fog | 24 | 144.417 | 0.800 |
| medium | Fog/Cloud | 29 | 272.259 | N/A |
| medium | Mist | 29 | 272.586 | N/A |
| medium | Dynamic Mist | 29 | 158.310 | 1.133 |
| medium | Mist + Fog | 29 | 158.224 | 1.133 |
| high | Fog/Cloud | 30 | 278.417 | N/A |
| high | Mist | 30 | 278.750 | N/A |
| high | Dynamic Mist | 30 | 160.050 | 1.167 |
| high | Mist + Fog | 30 | 160.083 | 1.167 |

## Realised obstruction and insertion delays

FCD measures simultaneous stopped incident vehicles during 90 to 250 seconds. All cases remain in the input-matched comparison; no input was retuned after this observation. Realised obstruction and late insertion counts match across algorithms in 90 of 90 density/seed groups. Different routing and signal policies can alter subsequent traffic and insertion states. The effect estimate includes those consequences; it does not condition on identical downstream trajectories. Every case must still realise at least one blocker through the end of the incident. Complete per-vehicle first-seen times and stopped samples are in validation_report.json.

| Density | Algorithm | Runs with 3 stopped vehicles | Runs with 2 | Runs with 1 | Vehicles inserted after 250 s |
| --- | --- | ---: | ---: | ---: | ---: |
| low | Fog/Cloud | 30 | 0 | 0 | 0 |
| low | Mist | 30 | 0 | 0 | 0 |
| low | Dynamic Mist | 30 | 0 | 0 | 0 |
| low | Mist + Fog | 30 | 0 | 0 | 0 |
| medium | Fog/Cloud | 30 | 0 | 0 | 0 |
| medium | Mist | 30 | 0 | 0 | 0 |
| medium | Dynamic Mist | 30 | 0 | 0 | 0 |
| medium | Mist + Fog | 30 | 0 | 0 | 0 |
| high | Fog/Cloud | 28 | 1 | 1 | 3 |
| high | Mist | 28 | 1 | 1 | 3 |
| high | Dynamic Mist | 28 | 1 | 1 | 3 |
| high | Mist + Fog | 28 | 1 | 1 | 3 |

## Observed incident avoidance

A run counts here only when its routing log applies a replacement during the incident that removes C1C2 from its remaining route. Reviews alone do not count.

| Density | Dynamic approach | Delivered alerts | Runs avoiding incident by reroute | Scheduled runs |
| --- | --- | ---: | ---: | ---: |
| low | Dynamic Mist | 24 | 24 | 30 |
| low | Mist + Fog | 24 | 24 | 30 |
| medium | Dynamic Mist | 29 | 29 | 30 |
| medium | Mist + Fog | 29 | 29 | 30 |
| high | Dynamic Mist | 30 | 30 | 30 |
| high | Mist + Fog | 30 | 30 | 30 |

## Matched response differences

Differences are algorithm A minus B; negative means A is faster. Intervals are Student-t 95% paired intervals. The exploratory comparisons are not corrected for multiple testing.

| Density | A | B | Paired samples | Difference s | 95% interval s |
| --- | --- | --- | ---: | ---: | --- |
| low | Mist | Fog/Cloud | 24 | 0.208 | -0.032 to 0.449 |
| low | Dynamic Mist | Mist | 24 | -121.979 | -123.468 to -120.491 |
| low | Mist + Fog | Dynamic Mist | 24 | -0.104 | -0.192 to -0.017 |
| medium | Mist | Fog/Cloud | 29 | 0.328 | -0.176 to 0.831 |
| medium | Dynamic Mist | Mist | 29 | -114.276 | -130.017 to -98.535 |
| medium | Mist + Fog | Dynamic Mist | 29 | -0.086 | -0.189 to 0.016 |
| high | Mist | Fog/Cloud | 30 | 0.333 | -0.320 to 0.986 |
| high | Dynamic Mist | Mist | 30 | -118.700 | -138.595 to -98.805 |
| high | Mist + Fog | Dynamic Mist | 30 | 0.033 | -0.121 to 0.188 |

## Controlled fallback benefit

These values use the ordinary batch, not the incident matrix. On the 23 delivered matched controlled-stall cases, compare Mist + Fog against Dynamic Mist with the same 900 ms stall. Time saved is the difference between their actual initial route application delays. This measures recovery latency; it is not a claim of a comparable journey-time reduction or organic failure.

| Density | Matched stalled cases | Mean route decision time saved ms | 95% interval ms |
| --- | ---: | ---: | --- |
| low | 7 | 399.461 | 399.447 to 399.474 |
| medium | 8 | 399.402 | 399.369 to 399.436 |
| high | 8 | 399.370 | 399.330 to 399.411 |

## Metric scope and remaining limits

EM PDR, throughput and end-to-end delay concern the shared alert-delivery mechanism before route computation. Identical results across routing algorithms are expected for those definitions and cannot establish routing superiority. EM throughput uses a fixed payload and window. The separate request/reply metrics describe routing communication; local Mist has no wireless Fog transaction. No absent packet measurements are inferred.

Normal Mist decision latency is 326 ms in this grid; Fog/Cloud is about 626.54 ms. The equality between normal Mist variants reflects the same initial computation model. Fallback adds recovery only when a controlled stall occurs. A controlled obstacle can expose adaptation benefits but does not guarantee them on uncongested roads.

Main response labels now retain three decimal places to expose small numerical differences. Underlying SUMO movement resolution remains 500 ms; the decimal display is not a claim of millisecond movement accuracy. Paired graphs show differences with confidence intervals without exaggerating bar heights.

Continuous incident response and route-change intervals are Student-t; fault recovery uses paired differences with Student-t intervals. The full incident summary also retains the established Wilson intervals for PDR/fallback and bootstrap intervals for waiting. Every graph retains a generic 95% CI label.

SUMO model references: [vehicle stops](https://sumo.dlr.de/docs/Definition_of_Vehicles%2C_Vehicle_Types%2C_and_Routes.html#stops) and [vehicle insertion safety](https://sumo.dlr.de/docs/Simulation/VehicleInsertion.html).
