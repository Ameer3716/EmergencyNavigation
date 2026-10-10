# Verification

The experiment contains 360 primary runs plus 90 waiting-time control runs. Values below are calculated from unmodified simulation outputs.

## Seed variation in generated trips

Trip IDs are reused as labels across seeds; different origins and destinations establish different placements.

| High-density seed | First trip ID | Departure (s) | Origin edge | Destination edge |
| --- | --- | ---: | --- | --- |
| 1 | normal0 | 0.00 | A2A3 | D1C1 |
| 4 | normal0 | 0.00 | B0B1 | A1B1 |
| 22 | normal0 | 0.00 | D2D3 | A2A3 |

## Low traffic

Generated background vehicles: 72. SUMO actually inserted 70 to 72 background vehicles across seeds. Peak simultaneous background count: 28 to 40. Dynamic Mist alert deliveries: 24/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) |
| NRL (packets/delivery) | 22,038.21 [21,713.57, 22,362.84] (n=24) | 22,038.25 [21,718.47, 22,358.03] (n=24) | 22,059.38 [21,733.69, 22,385.06] (n=24) | 22,062.04 [21,737.57, 22,386.52] (n=24) |
| EM throughput (bit/s) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) |
| EM end-to-end delay (ms) | 44.37 [40.33, 48.40] (n=24) | 44.37 [40.33, 48.40] (n=24) | 44.37 [40.33, 48.40] (n=24) | 44.37 [40.33, 48.40] (n=24) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=24) | 588.50 [412.05, 764.95] (n=24) | 588.50 [412.05, 764.95] (n=24) | 471.99 [373.86, 570.13] (n=24) |
| EV response time (s) | 153.312 [152.778, 153.847] (n=24) | 153.500 [152.624, 154.376] (n=24) | 147.167 [146.857, 147.476] (n=24) | 147.104 [146.806, 147.403] (n=24) |
| EV traffic-light waiting time (s) | 1.562 [1.125, 1.979] (n=24) | 1.833 [1.375, 2.271] (n=24) | 0.000 [0.000, 0.000] (n=24) | 0.000 [0.000, 0.000] (n=24) |

No-preemption waiting control: 26.29 s [24.17, 28.15], n=24.

### Routing and fallback

- MistDynamicAStar: 643 reviews; 3 applied route changes.
- MistDynamicFogFallback: 645 reviews; 3 applied route changes.
- Fallback: 7/30 (23.3%); triggered seeds 4, 5, 9, 10, 13, 17, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.54 ms |

Live candidate costs: 524 evaluations, 5 distinct positive costs, 20.85 to 103.10 s. Example actual route changes: seed 11 at 116.357 s, seed 27 at 112.859 s, seed 8 at 106.383 s.

## Medium traffic

Generated background vehicles: 144. SUMO actually inserted 142 to 144 background vehicles across seeds. Peak simultaneous background count: 59 to 78. Dynamic Mist alert deliveries: 29/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) |
| NRL (packets/delivery) | 39,778.66 [39,381.52, 40,175.79] (n=29) | 39,778.17 [39,372.29, 40,184.05] (n=29) | 39,892.76 [39,508.97, 40,276.54] (n=29) | 39,899.93 [39,513.63, 40,286.23] (n=29) |
| EM throughput (bit/s) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) |
| EM end-to-end delay (ms) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) |
| Route decision latency (ms) | 626.54 [626.54, 626.55] (n=29) | 574.28 [418.56, 729.99] (n=29) | 574.28 [418.56, 729.99] (n=29) | 464.10 [377.48, 550.71] (n=29) |
| EV response time (s) | 154.517 [153.183, 155.852] (n=29) | 154.724 [153.515, 155.933] (n=29) | 147.362 [146.418, 148.306] (n=29) | 147.362 [146.442, 148.283] (n=29) |
| EV traffic-light waiting time (s) | 0.845 [0.465, 1.259] (n=29) | 0.914 [0.500, 1.345] (n=29) | 0.000 [0.000, 0.000] (n=29) | 0.000 [0.000, 0.000] (n=29) |

No-preemption waiting control: 27.34 s [21.34, 35.55], n=29.

### Routing and fallback

- MistDynamicAStar: 780 reviews; 8 applied route changes.
- MistDynamicFogFallback: 782 reviews; 8 applied route changes.
- Fallback: 8/30 (26.7%); triggered seeds 4, 5, 9, 10, 13, 17, 18, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.60 ms |

Live candidate costs: 641 evaluations, 9 distinct positive costs, 20.85 to 103.10 s. Example actual route changes: seed 11 at 116.358 s, seed 18 at 132.266 s, seed 20 at 115.870 s.

## High traffic

Generated background vehicles: 200. SUMO actually inserted 200 to 200 background vehicles across seeds. Peak simultaneous background count: 84 to 104. Dynamic Mist alert deliveries: 30/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) |
| NRL (packets/delivery) | 54,436.10 [53,992.50, 54,879.70] (n=30) | 54,300.27 [53,914.16, 54,686.37] (n=30) | 54,515.43 [53,975.62, 55,055.24] (n=30) | 54,511.80 [53,979.46, 55,044.14] (n=30) |
| EM throughput (bit/s) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) |
| EM end-to-end delay (ms) | 32.17 [29.23, 35.12] (n=30) | 32.17 [29.23, 35.12] (n=30) | 32.17 [29.23, 35.12] (n=30) | 32.17 [29.23, 35.12] (n=30) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=30) | 566.00 [414.85, 717.15] (n=30) | 566.00 [414.85, 717.15] (n=30) | 459.50 [375.42, 543.58] (n=30) |
| EV response time (s) | 156.200 [154.259, 158.141] (n=30) | 156.883 [154.710, 159.057] (n=30) | 147.517 [145.986, 149.047] (n=30) | 146.733 [146.210, 147.256] (n=30) |
| EV traffic-light waiting time (s) | 0.667 [0.317, 1.050] (n=30) | 0.717 [0.350, 1.133] (n=30) | 0.400 [0.000, 1.200] (n=30) | 0.000 [0.000, 0.000] (n=30) |

No-preemption waiting control: 22.72 s [18.27, 28.27], n=30.

### Routing and fallback

- MistDynamicAStar: 807 reviews; 6 applied route changes.
- MistDynamicFogFallback: 803 reviews; 6 applied route changes.
- Fallback: 8/30 (26.7%); triggered seeds 4, 5, 9, 10, 13, 17, 18, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.63 ms |

Live candidate costs: 667 evaluations, 19 distinct positive costs, 20.85 to 113.01 s. Example actual route changes: seed 22 at 111.851 s, seed 23 at 140.853 s, seed 27 at 106.353 s.

## Interpreting density and approach differences

The alert reaches the EV before route computation starts. PDR and EM end-to-end delay describe that shared radio event; EM throughput uses the same delivery count and fixed 256-byte payload. These metrics can match across routing approaches without indicating that the routing code is inactive.

| Density | Generated background trips | Mean peak live vehicles | PDR | EM throughput (bit/s) | Mist A* response (s) | Dynamic Mist response (s) | Dynamic Mist route changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 72 | 33.0 | 0.800 | 1.820 | 153.50 | 147.17 | 3 |
| medium | 144 | 65.8 | 0.967 | 2.200 | 154.72 | 147.36 | 8 |
| high | 200 | 92.4 | 1.000 | 2.276 | 156.88 | 147.52 | 6 |

Density changes are present: PDR, throughput, and live vehicle counts rise with demand. Dynamic Mist is also active: it reviews live costs and applies route changes. PDR and throughput are expected to remain equal between route tiers when their common alert-delivery stage produces the same deliveries. Response means can differ after routing. Paired difference intervals, rather than overlap between independent mean intervals, determine whether matching seeds establish a difference.

## Interpretation

The confidence intervals determine whether measured response differences are convincing. Controlled stalls demonstrate recovery from a defined fault; they do not establish the fault rate in real deployment.

## Observed computation and watchdog margin

Initial A* expansions range from 13 to 13 nodes; the maximum across initial calculations and periodic reviews is 16. At 300 ms plus 2 ms per node, the latter represents 332 ms of modeled processing, leaving 168 ms before the 500 ms watchdog. The selected 900 ms stalls are controlled fault tests, not organic overload evidence.

Similar initial expansion counts can produce identical normal decision times across densities. Pooled latency means also depend on the delivered normal and controlled-stall samples; they should not be read as evidence that heavier traffic makes the processor faster.

## Matched seed differences

A minus B is computed within each delivered matching seed. Negative values favour A. An interval including zero does not establish a difference. These are exploratory comparisons without multiple-testing adjustment.

| Density | A minus B | Metric | Pairs | Mean difference | 95% CI | p value |
| --- | --- | --- | ---: | ---: | --- | ---: |
| low | MistAStar minus FogCloudAStar | ev_response_s (s) | 24 | 0.188 | [-0.358, 0.733] | 0.4843321320994577 |
| low | MistAStar minus FogCloudAStar | route_decision_ms (ms) | 24 | -38.039 | [-214.492, 138.415] | 0.6598053138966457 |
| low | MistDynamicAStar minus MistAStar | ev_response_s (s) | 24 | -6.333 | [-7.313, -5.354] | 2.4757969327511394e-12 |
| low | MistDynamicFogFallback minus MistDynamicAStar | ev_response_s (s) | 24 | -0.062 | [-0.134, 0.009] | 0.08295987936478119 |
| low | MistDynamicFogFallback minus MistDynamicAStar | route_decision_ms (ms) | 24 | -116.509 | [-194.827, -38.191] | 0.0053245715882288035 |
| medium | MistAStar minus FogCloudAStar | ev_response_s (s) | 29 | 0.207 | [-0.679, 1.092] | 0.6359534218874056 |
| medium | MistAStar minus FogCloudAStar | route_decision_ms (ms) | 29 | -52.267 | [-207.985, 103.451] | 0.4973923895215849 |
| medium | MistDynamicAStar minus MistAStar | ev_response_s (s) | 29 | -7.362 | [-8.614, -6.110] | 1.3690447246835657e-12 |
| medium | MistDynamicFogFallback minus MistDynamicAStar | ev_response_s (s) | 29 | 0.000 | [-0.144, 0.144] | 1.0 |
| medium | MistDynamicFogFallback minus MistDynamicAStar | route_decision_ms (ms) | 29 | -110.180 | [-179.284, -41.076] | 0.0028798547062911725 |
| high | MistAStar minus FogCloudAStar | ev_response_s (s) | 30 | 0.683 | [-0.260, 1.627] | 0.14941986723298062 |
| high | MistAStar minus FogCloudAStar | route_decision_ms (ms) | 30 | -60.539 | [-211.694, 90.615] | 0.4193852825650407 |
| high | MistDynamicAStar minus MistAStar | ev_response_s (s) | 30 | -9.367 | [-11.401, -7.333] | 2.524139191831425e-10 |
| high | MistDynamicFogFallback minus MistDynamicAStar | ev_response_s (s) | 30 | -0.783 | [-2.213, 0.647] | 0.27177525277108106 |
| high | MistDynamicFogFallback minus MistDynamicAStar | route_decision_ms (ms) | 30 | -106.499 | [-173.573, -39.425] | 0.002939291312809749 |

The normal and controlled-stall plots and matched-seed difference plots accompany the pooled figures. Faster modeled route decisions do not automatically produce an equally large change in SUMO vehicle arrival time.

## Supplementary route communication and signal validation

The seven headline metrics and the 450-run main matrix are unchanged. Separate route-transaction metrics are derived from original raw scalars, and 18 isolated short-notice red-signal runs validate positive waiting and safe priority transitions. Definitions, confidence intervals, measured tables, and limitations are in [SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).

## Controlled incident and matched recovery evidence

A separate 360-run matrix uses a physical C1C2 stopped queue after initial route selection, with the same incident input and original trips for every algorithm. FCD evidence verifies the incident; all delivered-alert runs must reach the destination. Matched fault recovery is also reported from the original batch. Actual tables, confidence intervals and limits are in [REQUIREMENTS_EVIDENCE.md](REQUIREMENTS_EVIDENCE.md). Shared EM delivery metrics keep their definitions and cannot demonstrate routing superiority. Graph labels retain three decimals for response and waiting; SUMO motion remains sampled every 500 ms.

## Direct comparison with the Fog/Cloud baseline

[CLIENT_BASELINE_COMPARISON.md](CLIENT_BASELINE_COMPARISON.md) reports response, signal waiting, decision latency, excess travel delay above free flow, and actual Fog route request counts. The latter two are supporting metrics derived from recorded scalars, not substitutes for the seven headline metrics. Ordinary traffic and controlled obstruction have separate matched-seed estimates and 95% intervals. The framework comparison includes advance signal requests in dynamic Mist and reactive requests in Fog/static Mist; both use the same safety controller and bounded retry mechanism. It is not an isolated comparison of A* computation alone.
