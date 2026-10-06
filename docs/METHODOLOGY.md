# Methodology

## Experiment design

SUMO 1.18.0 moves vehicles on a 4 by 4 signalized grid with 48 directed road links. OMNeT++ 6.3.0 and Veins 5.3.1 simulate wireless communication through TraCI. Three RSUs use a 400 m radio neighborhood. Low, medium, and high demand generates 72, 144, and 200 background trips over 360 seconds. Trip generation count differs from the number simultaneously on the road. The collector records peak active background vehicles and unique background vehicles seen up to EV arrival.

The main comparison is FogCloudAStar, MistAStar, MistDynamicAStar, and MistDynamicFogFallback at three densities and 30 matched seeds (360 runs). A further 90 NoPreemptionBaseline runs use FogCloudAStar routing with signal priority disabled. This control is displayed only for traffic-light waiting time. Its other collected values remain in the individual-run CSV for transparency.

## Routing and controlled fallback tests

Mist initial processing is 300 ms plus 2 ms per expanded A* node. Telemetry validation adds 0 ms per received message. The fallback watchdog is 500 ms. Normal operation is reported separately from controlled stalls. A fixed independent random selection with Python seed 20261005 selects eight seeds: 4, 5, 9, 10, 13, 17, 18, and 29. These receive an additional 900 ms initial Mist worker stall in every Mist configuration and at every density. The other 22 seeds have no injected stall. This is an explicit fault-injection experiment; the delay is not measured OBU behavior and the fallback must not be described as organic. Fog/Cloud is unaffected by a local Mist stall. A selected seed that does not receive the EM cannot activate fallback.

Dynamic A* reads received vehicle beacons and RSU edge reports, requires at least three observed vehicles for a congestion adjustment, and reviews the route every five seconds. A replacement needs 10% lower remaining cost, or a confirmed slow edge with 5% improvement. Two slow observations and a 30-second gap help prevent route oscillation. Observed speeds are capped at the road speed limit in the cost estimate, keeping the A* free-flow heuristic admissible. Initial processing delays are modeled; periodic reviews are atomic simulation evaluations. Reviews and applied route changes are separate counts. Routing logs include candidate cost, current remaining cost, observed edge count, and the controlled stall parameter.

## Vehicle movement and signal priority

The EV is held until its first route is ready. Release uses SUMO automatic speed control, a 13.9 m/s maximum speed, and speed mode 31 so car following, acceleration, junction priority, and red-light safety checks apply. No blue-light device is used to ignore red signals.

The EV sends a priority request within 100 m or an estimated eight seconds of the next signal. If its approach already has a compatible green, that phase is extended. Otherwise the controller uses 150 ms processing and checks the active green again before clearance. If SUMO started a new green during processing, that phase receives its full ten-second minimum before two seconds of yellow and one second of all-red clearance. Priority green also lasts at least ten seconds. Priority is released after the EV passes the junction or a 25-second maximum hold, followed by yellow and all-red before restoring the normal program. These are scenario timing assumptions, not a claim of compliance with a local traffic standard. They allow some requests to finish before EV arrival and others to cause waiting; no artificial waiting is added to the measurements.

The collector accumulates and logs at 100 ms. SUMO and the Veins manager still update motion every 500 ms; intervening polls reuse the last SUMO state. The finer accumulator does not claim 100 ms underlying motion accuracy. Traffic-light waiting is EV speed below 0.1 m/s within 20 m of the next signal after alert reception; it includes queue waiting near that stop line.

## Metrics and confidence intervals

PDR is delivered unique EMs divided by generated unique EMs. NRL is control plus EM transmissions divided by delivered EMs. EM throughput is delivered useful payload bits divided by a fixed 900-second window. The payload is 256 bytes: a successful run contributes 2048/900 = 2.27556 bit/s, and a nondelivery contributes zero. This is EM delivery throughput, not total network capacity. PDR and EM delay occur before route computation, so equal values across routing approaches can be correct.

EM end-to-end delay is generation to reception. Initial route decision latency is reception to route application. Both, and fallback decision latency, are displayed in milliseconds using high-precision raw scalars. Event, mobility, fallback and signal logs use 15 significant digits. Fog communication delay starts at the Fog request; routeWaitBeforeFog records watchdog waiting separately. For routes supplied by Fog, total initial latency equals waiting before Fog plus Fog processing, cloud backhaul and communication. EV response time is generation to arrival; EV travel and signal waiting remain in seconds. Response and decision measures require EM delivery, and NRL is undefined without a delivery. Corridor delay is travel time minus route distance/13.9 m/s, bounded at zero; it includes acceleration, turning, queuing, and signal effects.

PDR and fallback activation use Wilson score 95% intervals. Waiting and corridor delay use percentile bootstrap intervals with 10,000 resamples and fixed seed 42. Other continuous metrics use Student-t 95% intervals. Graphs show a generic [95% CI] label. Full mixed-cohort means and separate normal/stall means are both exported and plotted. Configuration colours are constant across figures. Matched-seed difference graphs show paired intervals; comparisons are exploratory and unadjusted for multiple testing. Paired comparisons use matching seeds and preserve a constant nonzero difference even when its sample variance is zero.

## Supplementary route communication and signal validation

The seven headline metrics and the 450-run main matrix are unchanged. Separate route-transaction metrics are derived from original raw scalars, and 18 isolated short-notice red-signal runs validate positive waiting and safe priority transitions. Definitions, confidence intervals, measured tables, and limitations are in [SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).
