# Methodology

## Simulation design

The study couples OMNeT++ 6.3.0 and Veins 5.3.1 to SUMO 1.18.0 through TraCI. The 4 by 4 signalized grid has 48 directed road links and three RSUs. The four comparison configurations are `FogCloudAStar`, `MistAStar`, `MistDynamicAStar`, and `MistDynamicFogFallback`. Every configuration uses the same 30 seeds at each of three background traffic densities: low (72 vehicles), medium (144 vehicles), and high (200 vehicles). The comparison contains exactly 360 runs.

The common `connectionManager.maxInterfDist` is **400 m**. This changes radio propagation and the relay/interference neighborhood. It is not an axis or cosmetic change. The prior 650 m run is retained separately in `archive_raw_20261001_650m/` and is used only for the explicitly labeled before/after comparison.

## Routing and failover

Static A* uses edge length divided by the 13.89 m/s speed limit. Dynamic A* uses live V2V beacons and V2I edge reports. Congestion adjustments require at least three observed vehicles on an edge. The EV reviews its route every 5 s; a replacement requires at least 10% lower estimated remaining cost, or a confirmed slow edge and at least 5% lower cost, with a 30 s minimum gap between reroutes. Route review and actual route replacement are counted separately from routing logs.

The modeled Mist A* computation is 300 ms plus 2 ms per expanded node. In the earlier 650 m batch, the maximum observed A* expansion was 16 nodes, yielding 332 ms of computation and a 468 ms margin below the 800 ms watchdog; initial decisions expanded at most 13 nodes. Computation alone therefore did not approach the watchdog in this grid. Before committing the initial route, a local OBU worker validates the routing snapshot: each V2V beacon and V2I status message actually received in the preceding three seconds has an **assumed 20 ms route-time service cost**. This is an explicit scenario parameter for a constrained OBU, not a measured hardware benchmark or an implemented cryptographic primitive. The order of magnitude is motivated by [primary VANET security analysis of constrained OBUs](https://nss.proj.kth.se/publications/fulltext/secure-vehicular-communication-system-vanet-security-cm2.pdf), which estimates only a few dozen signature verifications per second on a 400 MHz OBU under its stated assumptions; this study does not claim those assumptions or hardware were reproduced. The service delay applies to every Mist configuration and every seed. The message count is measured from actual radio receptions and written as `initialTelemetryValidationQueue`; the resulting delay is written as `initialTelemetryValidationDelay`. The combined scheduled Mist delay is written in the routing log. The 800 ms watchdog is active only in `MistDynamicFogFallback`; it cancels unfinished Mist work and requests a Fog route. `ForcedMistFailure` and `ForcedMistTimeout` remain separate diagnostics and are excluded from all comparison counts.

## Primary metrics and units

| Metric | Definition | Unit |
| --- | --- | --- |
| PDR | Unique EMs processed by the EV divided by unique EMs generated | ratio |
| NRL | Control plus EM transmissions divided by delivered EMs | packets/delivery |
| EM throughput | Successfully delivered EM payload bits divided by the fixed 900 s observation window | bit/s |
| EM end-to-end delay | EV EM reception time minus RSU generation time | ms |
| Route decision latency | Initial route application time minus EM reception time | ms |
| EV response time | Accident arrival time minus EM generation time | s |
| EV traffic-light waiting time | EV standstill below 0.1 m/s within 20 m of a signal stop line | s |

The EM has one fixed useful payload of 256 bytes. A delivered run therefore contributes 2048 / 900 = 2.27556 bit/s; a nondelivery contributes zero. Similar mean EM throughput across densities follows directly from this definition and similar PDR, even when the background traffic and route costs differ. Throughput is not aggregate network capacity.

## Additional metrics and statistics

Fallback activation is reported as a count and fraction of 30 scheduled `MistDynamicFogFallback` runs per density. Fallback decision latency is the initial route decision scalar for the real runs with `fallback_triggered=true`, in milliseconds. Route changes count only applied congestion/cost reroutes. Route computation frequency counts periodic `evaluated` events. Control transmission and byte counts, EV route distance, corridor delay, and EV travel time remain secondary metrics.

PDR and fallback activation use Wilson score 95% confidence intervals. Traffic-light waiting and corridor delay use 10,000-resample percentile bootstrap intervals with fixed seed 42 because they are nonnegative and zero-inflated. Other continuous metrics use Student-t 95% intervals. Graphs show the intervals as `[95% CI]` without method names; the computation methods remain specified here. Response and decision metrics are conditional on EM delivery; NRL is undefined when no EM is delivered. Paired comparisons use matched seeds.
