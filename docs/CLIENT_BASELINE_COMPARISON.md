# Client baseline comparisons

FogCloudAStar is the baseline. The proposed framework is MistDynamicFogFallback. All three Mist approaches are retained in the comparison CSV. Ordinary traffic and controlled obstruction are separate experiments.

Positive reduction percentages mean a lower proposed value. Confidence intervals use matched seeds, including zero differences. Missing arrivals are excluded from time metrics. Fog request counts include all 30 scheduled runs, including runs without alert delivery.

| Scenario | Density | Metric | Paired runs | Fog baseline | Proposed | Reduction % | Proposed minus baseline 95% interval |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Ordinary traffic | low | Route decision latency (ms) | 24 | 626.539 | 471.991 | 24.67 | -252.683 to -56.413 |
| Ordinary traffic | low | EV response time (s) | 24 | 153.312 | 147.104 | 4.05 | -6.815 to -5.602 |
| Ordinary traffic | low | EV traffic-light waiting time (s) | 24 | 1.562 | 0.000 | 100.00 | -2.013 to -1.112 |
| Ordinary traffic | low | Excess travel delay above free flow (s) | 24 | 24.332 | 18.508 | 23.94 | -6.387 to -5.262 |
| Ordinary traffic | low | Fog route requests per scheduled run (requests/run) | 30 | 0.800 | 0.233 | 70.83 | -0.755 to -0.378 |
| Ordinary traffic | medium | Route decision latency (ms) | 29 | 626.543 | 464.096 | 25.93 | -249.060 to -75.833 |
| Ordinary traffic | medium | EV response time (s) | 29 | 154.517 | 147.362 | 4.63 | -8.562 to -5.748 |
| Ordinary traffic | medium | EV traffic-light waiting time (s) | 29 | 0.845 | 0.000 | 100.00 | -1.270 to -0.419 |
| Ordinary traffic | medium | Excess travel delay above free flow (s) | 29 | 25.537 | 18.675 | 26.87 | -8.273 to -5.451 |
| Ordinary traffic | medium | Fog route requests per scheduled run (requests/run) | 30 | 0.967 | 0.267 | 72.41 | -0.874 to -0.526 |
| Ordinary traffic | high | Route decision latency (ms) | 30 | 626.539 | 459.501 | 26.66 | -251.118 to -82.958 |
| Ordinary traffic | high | EV response time (s) | 30 | 156.200 | 146.733 | 6.06 | -11.425 to -7.508 |
| Ordinary traffic | high | EV traffic-light waiting time (s) | 30 | 0.667 | 0.000 | 100.00 | -1.060 to -0.273 |
| Ordinary traffic | high | Excess travel delay above free flow (s) | 30 | 27.255 | 18.099 | 33.59 | -11.103 to -7.209 |
| Ordinary traffic | high | Fog route requests per scheduled run (requests/run) | 30 | 1.000 | 0.267 | 73.33 | -0.901 to -0.565 |
| Controlled obstruction | low | Route decision latency (ms) | 24 | 626.539 | 471.991 | 24.67 | -252.683 to -56.413 |
| Controlled obstruction | low | EV response time (s) | 24 | 266.292 | 144.417 | 45.77 | -123.458 to -120.292 |
| Controlled obstruction | low | EV traffic-light waiting time (s) | 24 | 4.417 | 0.000 | 100.00 | -13.553 to 4.720 |
| Controlled obstruction | low | Excess travel delay above free flow (s) | 24 | 137.367 | 15.447 | 88.76 | -123.526 to -120.315 |
| Controlled obstruction | low | Fog route requests per scheduled run (requests/run) | 30 | 0.800 | 0.233 | 70.83 | -0.755 to -0.378 |
| Controlled obstruction | medium | Route decision latency (ms) | 29 | 626.543 | 464.096 | 25.93 | -249.060 to -75.833 |
| Controlled obstruction | medium | EV response time (s) | 29 | 272.259 | 158.224 | 41.88 | -129.772 to -98.297 |
| Controlled obstruction | medium | EV traffic-light waiting time (s) | 29 | 11.707 | 4.448 | 62.00 | -18.082 to 3.565 |
| Controlled obstruction | medium | Excess travel delay above free flow (s) | 29 | 143.292 | 21.856 | 84.75 | -130.019 to -112.854 |
| Controlled obstruction | medium | Fog route requests per scheduled run (requests/run) | 30 | 0.967 | 0.267 | 72.41 | -0.874 to -0.526 |
| Controlled obstruction | high | Route decision latency (ms) | 30 | 626.539 | 459.501 | 26.66 | -251.118 to -82.958 |
| Controlled obstruction | high | EV response time (s) | 30 | 278.417 | 160.083 | 42.50 | -138.200 to -98.466 |
| Controlled obstruction | high | EV traffic-light waiting time (s) | 30 | 26.483 | 5.267 | 80.11 | -37.587 to -4.846 |
| Controlled obstruction | high | Excess travel delay above free flow (s) | 30 | 149.433 | 24.049 | 83.91 | -136.438 to -114.331 |
| Controlled obstruction | high | Fog route requests per scheduled run (requests/run) | 30 | 1.000 | 0.267 | 73.33 | -0.901 to -0.565 |

## Supporting metric definitions

Excess travel delay is max(0, actual EV travel time minus traveled distance / 13.9 m/s). This reuses collected travel-time and distance scalars. It measures delay relative to a reference speed and is correlated with response time. It does not isolate congestion from signals.

Fog route requests count actual initial RouteRequest send events recorded by the EV. Local Mist needs zero requests; fallback needs one only when it switches to Fog. These are requests at the sender, not total relay transmissions or EM packet delivery. A scheduled case without an EM has zero requests.

Bar intervals use Student-t, except signal waiting uses the existing bootstrap percentile method. Paired intervals use Student-t and are exploratory without multiple-comparison correction. All graph labels use generic 95% CI.

The framework comparison includes live routing and advance signal requests in dynamic Mist. Fog/Cloud and static Mist use reactive requests. All use the same safety controller and bounded retry mechanism. Journey differences therefore do not isolate A* computation alone.

## Measured assessment

A paired interval wholly below zero supports a lower proposed value in this experiment. An interval crossing zero is inconclusive. The client selected a 20 percent response-time target after these runs were measured. The obstruction experiment exceeds that target at every density; ordinary traffic does not. This is an exploratory assessment, not a prospectively registered success test. See CLIENT_20_PERCENT_FEASIBILITY.md for the physical limits of the ordinary grid.

Ordinary traffic, ev response time: lower proposed values supported in low, medium, high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.

Ordinary traffic, ev traffic-light waiting time: lower proposed values supported in low, medium, high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.

Ordinary traffic, excess travel delay above free flow: lower proposed values supported in low, medium, high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.

Ordinary traffic, fog route requests per scheduled run: lower proposed values supported in low, medium, high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.

Controlled obstruction, ev response time: lower proposed values supported in low, medium, high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.

Controlled obstruction, ev traffic-light waiting time: lower proposed values supported in high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.

Controlled obstruction, excess travel delay above free flow: lower proposed values supported in low, medium, high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.

Controlled obstruction, fog route requests per scheduled run: lower proposed values supported in low, medium, high. Read the percentage reductions and intervals above for the size and uncertainty of each effect.
