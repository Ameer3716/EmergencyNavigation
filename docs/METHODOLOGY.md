# Methodology

The network is a 4 × 4 bidirectional grid with 300 m junction spacing, 48 directed road edges, and 16 signalized junctions. SUMO controls motion, stops, traffic lights, and route execution. Veins/OMNeT++ controls messages, decisions, processing delays, fallback, and statistics. Low, medium, and high demand uses normal-vehicle headways of 5.0, 2.5, and 1.8 s from 0–360 s. The accident vehicle stops near D3; the accident event is marked at 60 s and RSU[2] requires at least three seconds below 0.1 m/s before generation. The ambulance starts on A0A1 and targets D2D3.

All four configurations share the same grid, demand file, accident, signal programs, radio parameters, and seed. The comparison changes only the route-decision policy:

| Configuration | Decision path |
| --- | --- |
| `FogCloudAStar` | EV radio request → nearest fog RSU → cloud when outside fog service area → fog radio reply → static A* route |
| `MistAStar` | Local static A* in the EV's mist module |
| `MistDynamicAStar` | Local dynamic A* in the mist module, with five-second updates |
| `MistDynamicFogFallback` | Same dynamic route computation, with 800 ms watchdog and fog takeover on failure |

The accident RSU creates a single Emergency Message with a 10-hop limit and 256-byte useful payload. Nodes cache message IDs for 60 s, discard duplicate copies, and forward with a uniformly random 5–20 ms delay only if remaining hops exceed one. Normal vehicles broadcast one-second beacons with speed and edge. RSUs aggregate recent beacons into per-edge status broadcasts. The ambulance uses fresh V2V observations and fresher RSU status when both cover an edge. Only Veins IEEE 802.11p models wireless delay; no extra fixed radio delay is applied.

The road graph loads `grid.net.xml`, including SUMO's explicit permitted edge connections. This matters because geometrically connected roads can still have forbidden turns. Static cost is `length / speedLimit`. The A* heuristic is Euclidean distance to the destination entry node divided by maximum network speed. Dynamic cost for an occupied edge is `(length / max(meanSpeed, 1 m/s)) × (1 + λ × min(1, vehicleCount / capacity))`, where λ defaults to 0.5 and one vehicle per 7.5 m is the capacity estimate. Empty edges retain free-flow cost. The dynamic router evaluates every five seconds. It considers an alternate route if a future edge has remained below 30% of its speed limit for two samples or the alternate lowers estimated remaining cost by at least 10%; a slow-edge reroute also requires at least 5% estimated improvement. A 30-second minimum gap limits oscillation. These parameters are configurable in NED/`omnetpp.ini`.

Mist, fog, and cloud use the same computation-delay model, `300 ms + 2 ms × expandedNodes`. The cloud adds a 150 ms one-way backhaul delay, represented twice for a request and reply. The fog service radius defaults to 500 m. Route replies travel back to the EV over the native Veins radio. The watchdog defaults to 800 ms; `ForcedMistFailure` deliberately bypasses mist and demonstrates fog takeover. Application processing, backhaul, radio time, and total decision latency are recorded separately where relevant.

On each selected route, the EV requests preemption of the next signal within 250 m or 15 s ETA. An RSU receives the radio request and delegates to that junction's OMNeT++ controller. After a 150 ms control delay, the controller sets existing green lamps yellow for 2 s, sets all-red for 1 s, activates the incoming movement's green, holds it for at most 25 s, and restores the original SUMO program. The real TraCI state is logged at each transition.

Metrics use simulator timestamps and unmodified raw logs. `PDR = unique EM IDs processed by EV / unique EM IDs generated`; `E2E = EV processing time − EM generation time`; `throughput = useful EM bits processed by EV / simulation measurement duration`; `NRL = (control-packet transmissions + EM transmissions) / delivered unique EM packets`; `EV response time = SUMO EV disappearance at destination − EM generation time`; `decision latency = final applied route time − decision start`. The 0.5 s mobility polling gives arrival times a resolution of 0.5 s. Accumulated traffic-light waiting counts EV speed below 0.1 m/s with a SUMO next-signal distance no more than 20 m, after EM reception. Distance comes from SUMO's vehicle distance-travelled API.

For repeated seeds, use the sample standard deviation. The processing script reports `mean ± 1.96 × s / √n` as an approximate 95% confidence interval only when at least two observations exist; single-run intervals remain empty. No simulated values are replaced or manually adjusted in analysis.
