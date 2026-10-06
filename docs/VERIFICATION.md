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

Generated background vehicles: 72. SUMO actually inserted 70 to 72 background vehicles across seeds. Peak simultaneous background count: 29 to 40. Dynamic Mist alert deliveries: 24/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) |
| NRL (packets/delivery) | 22,030.62 [21,705.17, 22,356.08] (n=24) | 22,029.75 [21,711.59, 22,347.91] (n=24) | 22,019.54 [21,702.46, 22,336.62] (n=24) | 22,027.46 [21,708.16, 22,346.76] (n=24) |
| EM throughput (bit/s) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) |
| EM end-to-end delay (ms) | 44.37 [40.33, 48.40] (n=24) | 44.37 [40.33, 48.40] (n=24) | 44.37 [40.33, 48.40] (n=24) | 44.37 [40.33, 48.40] (n=24) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=24) | 588.50 [412.05, 764.95] (n=24) | 588.50 [412.05, 764.95] (n=24) | 471.99 [373.86, 570.13] (n=24) |
| EV response time (s) | 153.312 [152.778, 153.847] (n=24) | 153.500 [152.624, 154.376] (n=24) | 153.021 [152.596, 153.445] (n=24) | 152.979 [152.550, 153.408] (n=24) |
| EV traffic-light waiting time (s) | 1.562 [1.125, 1.979] (n=24) | 1.833 [1.375, 2.271] (n=24) | 2.208 [1.812, 2.562] (n=24) | 2.250 [1.812, 2.646] (n=24) |

No-preemption waiting control: 26.29 s [24.17, 28.15], n=24.

### Routing and fallback

- MistDynamicAStar: 661 reviews; 4 applied route changes.
- MistDynamicFogFallback: 661 reviews; 4 applied route changes.
- Fallback: 7/30 (23.3%); triggered seeds 4, 5, 9, 10, 13, 17, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.54 ms |

Live candidate costs: 558 evaluations, 5 distinct positive costs, 20.85 to 103.10 s. Example actual route changes: seed 11 at 111.357 s, seed 19 at 116.360 s, seed 27 at 142.859 s.

## Medium traffic

Generated background vehicles: 144. SUMO actually inserted 142 to 144 background vehicles across seeds. Peak simultaneous background count: 60 to 78. Dynamic Mist alert deliveries: 29/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) |
| NRL (packets/delivery) | 39,768.45 [39,371.00, 40,165.90] (n=29) | 39,779.00 [39,374.16, 40,183.84] (n=29) | 39,805.97 [39,412.52, 40,199.41] (n=29) | 39,788.10 [39,395.75, 40,180.46] (n=29) |
| EM throughput (bit/s) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) |
| EM end-to-end delay (ms) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) |
| Route decision latency (ms) | 626.54 [626.54, 626.55] (n=29) | 574.28 [418.56, 729.99] (n=29) | 574.28 [418.56, 729.99] (n=29) | 464.10 [377.48, 550.71] (n=29) |
| EV response time (s) | 154.517 [153.183, 155.852] (n=29) | 154.724 [153.515, 155.933] (n=29) | 154.121 [152.597, 155.644] (n=29) | 153.897 [152.278, 155.515] (n=29) |
| EV traffic-light waiting time (s) | 0.845 [0.465, 1.259] (n=29) | 0.914 [0.500, 1.345] (n=29) | 1.121 [0.690, 1.586] (n=29) | 1.155 [0.724, 1.621] (n=29) |

No-preemption waiting control: 27.34 s [21.34, 35.55], n=29.

### Routing and fallback

- MistDynamicAStar: 816 reviews; 8 applied route changes.
- MistDynamicFogFallback: 813 reviews; 9 applied route changes.
- Fallback: 8/30 (26.7%); triggered seeds 4, 5, 9, 10, 13, 17, 18, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.60 ms |

Live candidate costs: 687 evaluations, 10 distinct positive costs, 20.85 to 144.79 s. Example actual route changes: seed 11 at 116.358 s, seed 2 at 117.854 s, seed 20 at 115.870 s.

## High traffic

Generated background vehicles: 200. SUMO actually inserted 200 to 200 background vehicles across seeds. Peak simultaneous background count: 86 to 100. Dynamic Mist alert deliveries: 30/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) |
| NRL (packets/delivery) | 54,429.80 [53,983.57, 54,876.03] (n=30) | 54,290.10 [53,902.28, 54,677.92] (n=30) | 54,333.23 [53,896.22, 54,770.25] (n=30) | 54,276.47 [53,895.42, 54,657.51] (n=30) |
| EM throughput (bit/s) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) |
| EM end-to-end delay (ms) | 32.17 [29.23, 35.12] (n=30) | 32.17 [29.23, 35.12] (n=30) | 32.17 [29.23, 35.12] (n=30) | 32.17 [29.23, 35.12] (n=30) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=30) | 566.00 [414.85, 717.15] (n=30) | 566.00 [414.85, 717.15] (n=30) | 459.50 [375.42, 543.58] (n=30) |
| EV response time (s) | 156.200 [154.259, 158.141] (n=30) | 156.883 [154.710, 159.057] (n=30) | 154.933 [152.505, 157.362] (n=30) | 154.917 [152.486, 157.348] (n=30) |
| EV traffic-light waiting time (s) | 0.667 [0.317, 1.050] (n=30) | 0.717 [0.350, 1.133] (n=30) | 0.817 [0.450, 1.217] (n=30) | 0.767 [0.416, 1.150] (n=30) |

No-preemption waiting control: 22.72 s [18.27, 28.27], n=30.

### Routing and fallback

- MistDynamicAStar: 860 reviews; 11 applied route changes.
- MistDynamicFogFallback: 860 reviews; 11 applied route changes.
- Fallback: 8/30 (26.7%); triggered seeds 4, 5, 9, 10, 13, 17, 18, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.63 ms |

Live candidate costs: 722 evaluations, 31 distinct positive costs, 20.85 to 114.22 s. Example actual route changes: seed 11 at 116.363 s, seed 14 at 136.370 s, seed 16 at 106.356 s.

## Interpreting density and approach differences

The alert reaches the EV before route computation starts. PDR and EM end-to-end delay describe that shared radio event; EM throughput uses the same delivery count and fixed 256-byte payload. These metrics can match across routing approaches without indicating that the routing code is inactive.

| Density | Generated background trips | Mean peak live vehicles | PDR | EM throughput (bit/s) | Mist A* response (s) | Dynamic Mist response (s) | Dynamic Mist route changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 72 | 33.2 | 0.800 | 1.820 | 153.50 | 153.02 | 4 |
| medium | 144 | 66.2 | 0.967 | 2.200 | 154.72 | 154.12 | 8 |
| high | 200 | 93.7 | 1.000 | 2.276 | 156.88 | 154.93 | 11 |

Density changes are present: PDR, throughput, and live vehicle counts rise with demand. Dynamic Mist is also active: it reviews live costs and applies route changes. PDR and throughput are expected to remain equal between route tiers when their common alert-delivery stage produces the same deliveries. Response means can differ after routing. Paired difference intervals, rather than overlap between independent mean intervals, determine whether matching seeds establish a difference.

## Interpretation

The confidence intervals determine whether measured response differences are convincing. Controlled stalls demonstrate recovery from a defined fault; they do not establish the fault rate in real deployment.

## Observed computation and watchdog margin

Initial A* expansions range from 13 to 13 nodes; the maximum across initial calculations and periodic reviews is 17. At 300 ms plus 2 ms per node, the latter represents 334 ms of modeled processing, leaving 166 ms before the 500 ms watchdog. The selected 900 ms stalls are controlled fault tests, not organic overload evidence.

Similar initial expansion counts can produce identical normal decision times across densities. Pooled latency means also depend on the delivered normal and controlled-stall samples; they should not be read as evidence that heavier traffic makes the processor faster.

## Matched seed differences

A minus B is computed within each delivered matching seed. Negative values favour A. An interval including zero does not establish a difference. These are exploratory comparisons without multiple-testing adjustment.

| Density | A minus B | Metric | Pairs | Mean difference | 95% CI | p value |
| --- | --- | --- | ---: | ---: | --- | ---: |
| low | MistAStar minus FogCloudAStar | ev_response_s (s) | 24 | 0.188 | [-0.358, 0.733] | 0.4843321320994577 |
| low | MistAStar minus FogCloudAStar | route_decision_ms (ms) | 24 | -38.039 | [-214.492, 138.415] | 0.6598053138966457 |
| low | MistDynamicAStar minus MistAStar | ev_response_s (s) | 24 | -0.479 | [-1.447, 0.488] | 0.3162333361856316 |
| low | MistDynamicFogFallback minus MistDynamicAStar | ev_response_s (s) | 24 | -0.042 | [-0.101, 0.018] | 0.16166805648925678 |
| low | MistDynamicFogFallback minus MistDynamicAStar | route_decision_ms (ms) | 24 | -116.509 | [-194.827, -38.191] | 0.0053245715882288035 |
| medium | MistAStar minus FogCloudAStar | ev_response_s (s) | 29 | 0.207 | [-0.679, 1.092] | 0.6359534218874056 |
| medium | MistAStar minus FogCloudAStar | route_decision_ms (ms) | 29 | -52.267 | [-207.985, 103.451] | 0.4973923895215849 |
| medium | MistDynamicAStar minus MistAStar | ev_response_s (s) | 29 | -0.603 | [-1.982, 0.775] | 0.3774916381060249 |
| medium | MistDynamicFogFallback minus MistDynamicAStar | ev_response_s (s) | 29 | -0.224 | [-0.890, 0.442] | 0.49615126928608094 |
| medium | MistDynamicFogFallback minus MistDynamicAStar | route_decision_ms (ms) | 29 | -110.180 | [-179.284, -41.076] | 0.0028798547062911725 |
| high | MistAStar minus FogCloudAStar | ev_response_s (s) | 30 | 0.683 | [-0.260, 1.627] | 0.14941986723298062 |
| high | MistAStar minus FogCloudAStar | route_decision_ms (ms) | 30 | -60.539 | [-211.694, 90.615] | 0.4193852825650407 |
| high | MistDynamicAStar minus MistAStar | ev_response_s (s) | 30 | -1.950 | [-3.468, -0.432] | 0.013602534996809698 |
| high | MistDynamicFogFallback minus MistDynamicAStar | ev_response_s (s) | 30 | -0.017 | [-0.051, 0.017] | 0.32558198801619365 |
| high | MistDynamicFogFallback minus MistDynamicAStar | route_decision_ms (ms) | 30 | -106.499 | [-173.573, -39.425] | 0.002939291312809749 |

The normal and controlled-stall plots and matched-seed difference plots accompany the pooled figures. Faster modeled route decisions do not automatically produce an equally large change in SUMO vehicle arrival time.

## Supplementary route communication and signal validation

The seven headline metrics and the 450-run main matrix are unchanged. Separate route-transaction metrics are derived from original raw scalars, and 18 isolated short-notice red-signal runs validate positive waiting and safe priority transitions. Definitions, confidence intervals, measured tables, and limitations are in [SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).

## Controlled incident and matched recovery evidence

A separate 360-run matrix uses a physical C1C2 stopped queue after initial route selection, with the same incident input and original trips for every algorithm. FCD evidence verifies the incident; all delivered-alert runs must reach the destination. Matched fault recovery is also reported from the original batch. Actual tables, confidence intervals and limits are in [REQUIREMENTS_EVIDENCE.md](REQUIREMENTS_EVIDENCE.md). Shared EM delivery metrics keep their definitions and cannot demonstrate routing superiority. Graph labels retain three decimals for response and waiting; SUMO motion remains sampled every 500 ms.
