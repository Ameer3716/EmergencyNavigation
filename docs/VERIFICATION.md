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
| NRL (packets/delivery) | 22,039.42 [21,724.71, 22,354.12] (n=24) | 22,045.67 [21,727.27, 22,364.07] (n=24) | 22,037.79 [21,722.22, 22,353.36] (n=24) | 22,033.04 [21,717.28, 22,348.81] (n=24) |
| EM throughput (bit/s) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) |
| EM end-to-end delay (ms) | 44.36 [40.33, 48.40] (n=24) | 44.36 [40.33, 48.40] (n=24) | 44.36 [40.33, 48.40] (n=24) | 44.36 [40.33, 48.40] (n=24) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=24) | 588.50 [412.05, 764.95] (n=24) | 588.50 [412.05, 764.95] (n=24) | 471.99 [373.86, 570.13] (n=24) |
| EV response time (s) | 153.29 [152.73, 153.86] (n=24) | 153.06 [152.30, 153.82] (n=24) | 152.52 [151.59, 153.46] (n=24) | 152.54 [151.60, 153.49] (n=24) |
| EV traffic-light waiting time (s) | 1.54 [1.10, 1.98] (n=24) | 1.58 [1.10, 2.06] (n=24) | 1.96 [1.50, 2.40] (n=24) | 2.02 [1.54, 2.46] (n=24) |

No-preemption waiting control: 26.29 s [24.17, 28.15], n=24.

### Routing and fallback

- MistDynamicAStar: 657 reviews; 4 applied route changes.
- MistDynamicFogFallback: 660 reviews; 4 applied route changes.
- Fallback: 7/30 (23.3%); triggered seeds 4, 5, 9, 10, 13, 17, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.54 ms |

Live candidate costs: 554 evaluations, 5 distinct positive costs, 20.85 to 103.10 s. Example actual route changes: seed 11 at 116.357 s, seed 19 at 116.360 s, seed 27 at 142.859 s.

## Medium traffic

Generated background vehicles: 144. SUMO actually inserted 142 to 144 background vehicles across seeds. Peak simultaneous background count: 60 to 78. Dynamic Mist alert deliveries: 29/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) |
| NRL (packets/delivery) | 39,771.48 [39,367.91, 40,175.05] (n=29) | 39,738.93 [39,340.38, 40,137.48] (n=29) | 39,766.07 [39,377.37, 40,154.77] (n=29) | 39,738.28 [39,353.78, 40,122.77] (n=29) |
| EM throughput (bit/s) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) |
| EM end-to-end delay (ms) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) |
| Route decision latency (ms) | 626.54 [626.54, 626.55] (n=29) | 574.28 [418.56, 729.99] (n=29) | 574.28 [418.56, 729.99] (n=29) | 464.10 [377.48, 550.71] (n=29) |
| EV response time (s) | 154.60 [153.40, 155.81] (n=29) | 155.48 [152.63, 158.34] (n=29) | 154.40 [151.38, 157.41] (n=29) | 154.14 [151.04, 157.23] (n=29) |
| EV traffic-light waiting time (s) | 0.95 [0.53, 1.40] (n=29) | 1.62 [0.34, 3.83] (n=29) | 1.71 [0.41, 3.93] (n=29) | 1.74 [0.45, 3.97] (n=29) |

No-preemption waiting control: 27.34 s [21.34, 35.55], n=29.

### Routing and fallback

- MistDynamicAStar: 820 reviews; 7 applied route changes.
- MistDynamicFogFallback: 815 reviews; 8 applied route changes.
- Fallback: 8/30 (26.7%); triggered seeds 4, 5, 9, 10, 13, 17, 18, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.60 ms |

Live candidate costs: 689 evaluations, 10 distinct positive costs, 20.85 to 103.10 s. Example actual route changes: seed 2 at 117.854 s, seed 20 at 115.870 s, seed 23 at 141.355 s.

## High traffic

Generated background vehicles: 200. SUMO actually inserted 200 to 200 background vehicles across seeds. Peak simultaneous background count: 86 to 102. Dynamic Mist alert deliveries: 30/30.

| Main metric | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) |
| NRL (packets/delivery) | 54,379.17 [53,910.26, 54,848.07] (n=30) | 54,257.13 [53,783.06, 54,731.20] (n=30) | 54,210.63 [53,730.08, 54,691.19] (n=30) | 54,257.27 [53,754.44, 54,760.09] (n=30) |
| EM throughput (bit/s) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) |
| EM end-to-end delay (ms) | 32.17 [29.22, 35.11] (n=30) | 32.17 [29.22, 35.11] (n=30) | 32.17 [29.22, 35.11] (n=30) | 32.17 [29.22, 35.11] (n=30) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=30) | 566.00 [414.85, 717.15] (n=30) | 566.00 [414.85, 717.15] (n=30) | 459.50 [375.42, 543.58] (n=30) |
| EV response time (s) | 156.32 [154.39, 158.25] (n=30) | 156.98 [154.80, 159.17] (n=30) | 154.38 [152.10, 156.67] (n=30) | 154.35 [152.05, 156.65] (n=30) |
| EV traffic-light waiting time (s) | 0.67 [0.33, 1.03] (n=30) | 0.62 [0.30, 0.98] (n=30) | 0.65 [0.33, 1.00] (n=30) | 0.60 [0.30, 0.95] (n=30) |

No-preemption waiting control: 22.72 s [18.27, 28.27], n=30.

### Routing and fallback

- MistDynamicAStar: 853 reviews; 10 applied route changes.
- MistDynamicFogFallback: 855 reviews; 10 applied route changes.
- Fallback: 8/30 (26.7%); triggered seeds 4, 5, 9, 10, 13, 17, 18, 29. These are controlled stall tests.

### Normal and controlled-stall decision latency

| Condition | Fog/Cloud | Mist | Dynamic Mist | Mist + Fog |
| --- | ---: | ---: | ---: | ---: |
| normal | 626.54 ms | 326.00 ms | 326.00 ms | 326.00 ms |
| controlled_stall | 626.54 ms | 1226.00 ms | 1226.00 ms | 826.63 ms |

Live candidate costs: 721 evaluations, 26 distinct positive costs, 20.85 to 114.22 s. Example actual route changes: seed 11 at 116.363 s, seed 14 at 136.370 s, seed 20 at 146.358 s.

## Interpreting density and approach differences

The alert reaches the EV before route computation starts. PDR and EM end-to-end delay describe that shared radio event; EM throughput uses the same delivery count and fixed 256-byte payload. These metrics can match across routing approaches without indicating that the routing code is inactive.

| Density | Generated background trips | Mean peak live vehicles | PDR | EM throughput (bit/s) | Mist A* response (s) | Dynamic Mist response (s) | Dynamic Mist route changes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| low | 72 | 33.2 | 0.800 | 1.820 | 153.06 | 152.52 | 4 |
| medium | 144 | 66.4 | 0.967 | 2.200 | 155.48 | 154.40 | 7 |
| high | 200 | 93.1 | 1.000 | 2.276 | 156.98 | 154.38 | 10 |

Density changes are present: PDR, throughput, and live vehicle counts rise with demand. Dynamic Mist is also active: it reviews live costs and applies route changes. PDR and throughput are expected to remain equal between route tiers when their common alert-delivery stage produces the same deliveries. Response means can differ after routing, but overlapping confidence intervals limit claims about small differences.

## Interpretation

The confidence intervals determine whether measured response differences are convincing. Controlled stalls demonstrate recovery from a defined fault; they do not establish the fault rate in real deployment.
