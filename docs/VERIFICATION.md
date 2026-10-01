# Verification

## Batch and source checks

The current batch contains 360 runs: four configurations by three densities by 30 matched seeds. `scripts/audit_batch.py` checks the exact matrix, raw file triplets, parameter provenance, processed metrics, fallback logs, route event counts, and graph files. The 650 m historical batch is archived outside the current comparison.

The 400 m range screen used 23 selected MistDynamicAStar runs, including the five previously troublesome seed/density combinations and additional seeds in each density. Two of 23 partitioned at 400 m (low seeds 12 and 28), versus five of the same 23 at 650 m. This selected screen is not an estimate of the full-batch partition rate; the full result below uses all 360 current runs.

Across the full current batch, 28/360 runs (7.8%) did not deliver the EM. This is the batch-wide nondelivery/partition proxy; individual seed outcomes appear below.

SUMO route files contain 72, 144, and 200 background vehicles for low, medium, and high density, respectively, for every seed. The trip files show different seeded placements: normal0 starts on A2A3 and ends on D1C1 for seed 1, starts on D2D3 for seed 2, and starts on B0B1 for seed 4. Within one seed, the early trips intentionally match across densities; the trip counts and departure spacing then diverge.

## Seven primary metrics

Values below are mean [95% CI]. `n` is the metric-specific valid run count. Units remain in the metric label.

### Low density (72 background vehicles)

| Metric | FogCloudAStar | MistAStar | MistDynamicAStar | MistDynamicFogFallback |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) | 0.800 [0.627, 0.905] (n=30) |
| NRL (packets/delivery) | 22,035.1 [21,706.4, 22,363.9] (n=24) | 22,025.2 [21,700.7, 22,349.6] (n=24) | 22,051.2 [21,724.5, 22,378.0] (n=24) | 22,051.2 [21,724.5, 22,378.0] (n=24) |
| EM throughput (bit/s) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) | 1.820 [1.475, 2.166] (n=30) |
| EM end-to-end delay (ms) | 44.36 [40.33, 48.40] (n=24) | 44.36 [40.33, 48.40] (n=24) | 44.36 [40.33, 48.40] (n=24) | 44.36 [40.33, 48.40] (n=24) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=24) | 625.17 [579.21, 671.12] (n=24) | 625.17 [579.21, 671.12] (n=24) | 625.17 [579.21, 671.12] (n=24) |
| EV response time (s) | 141.67 [141.43, 141.91] (n=24) | 141.60 [141.35, 141.86] (n=24) | 141.67 [141.40, 141.93] (n=24) | 141.67 [141.40, 141.93] (n=24) |
| EV traffic-light waiting time (s) | 0.00 [0.00, 0.00] (n=24) | 0.00 [0.00, 0.00] (n=24) | 0.00 [0.00, 0.00] (n=24) | 0.00 [0.00, 0.00] (n=24) |

### Medium density (144 background vehicles)

| Metric | FogCloudAStar | MistAStar | MistDynamicAStar | MistDynamicFogFallback |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) | 0.967 [0.833, 0.994] (n=30) |
| NRL (packets/delivery) | 39,859.7 [39,449.2, 40,270.2] (n=29) | 39,897.7 [39,492.2, 40,303.2] (n=29) | 39,898.6 [39,492.0, 40,305.1] (n=29) | 39,918.2 [39,504.9, 40,331.5] (n=29) |
| EM throughput (bit/s) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) | 2.200 [2.045, 2.355] (n=30) |
| EM end-to-end delay (ms) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) | 37.12 [33.72, 40.52] (n=29) |
| Route decision latency (ms) | 626.54 [626.54, 626.55] (n=29) | 844.62 [773.43, 915.81] (n=29) | 844.62 [773.43, 915.81] (n=29) | 946.38 [855.22, 1037.53] (n=29) |
| EV response time (s) | 141.52 [141.48, 141.55] (n=29) | 141.66 [141.57, 141.74] (n=29) | 141.72 [141.45, 142.00] (n=29) | 141.88 [141.61, 142.15] (n=29) |
| EV traffic-light waiting time (s) | 0.00 [0.00, 0.00] (n=29) | 0.00 [0.00, 0.00] (n=29) | 0.00 [0.00, 0.00] (n=29) | 0.00 [0.00, 0.00] (n=29) |

### High density (200 background vehicles)

| Metric | FogCloudAStar | MistAStar | MistDynamicAStar | MistDynamicFogFallback |
| --- | ---: | ---: | ---: | ---: |
| PDR (ratio) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) | 1.000 [0.886, 1.000] (n=30) |
| NRL (packets/delivery) | 54,479.0 [53,976.4, 54,981.7] (n=30) | 54,432.5 [53,977.6, 54,887.4] (n=30) | 54,453.4 [53,986.1, 54,920.8] (n=30) | 54,462.6 [54,004.5, 54,920.8] (n=30) |
| EM throughput (bit/s) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) | 2.276 [2.276, 2.276] (n=30) |
| EM end-to-end delay (ms) | 32.17 [29.22, 35.11] (n=30) | 32.17 [29.22, 35.11] (n=30) | 32.17 [29.22, 35.11] (n=30) | 32.17 [29.22, 35.11] (n=30) |
| Route decision latency (ms) | 626.54 [626.54, 626.54] (n=30) | 1075.33 [995.17, 1155.50] (n=30) | 1075.33 [995.17, 1155.50] (n=30) | 1087.24 [1041.95, 1132.52] (n=30) |
| EV response time (s) | 142.52 [141.57, 143.46] (n=30) | 142.73 [141.83, 143.64] (n=30) | 142.70 [141.83, 143.57] (n=30) | 142.80 [141.94, 143.66] (n=30) |
| EV traffic-light waiting time (s) | 0.00 [0.00, 0.00] (n=30) | 0.00 [0.00, 0.00] (n=30) | 0.13 [0.00, 0.40] (n=30) | 0.13 [0.00, 0.40] (n=30) |

## Mechanism evidence

| Density | Fallback activations | Rate | MistDynamicAStar reroutes / reviews | MistDynamicFogFallback reroutes / reviews |
| --- | ---: | ---: | ---: | ---: |
| low | 0/30 | 0.000 | 3 / 625 | 3 / 625 |
| medium | 18/30 | 0.600 | 6 / 758 | 5 / 758 |
| high | 27/30 | 0.900 | 6 / 784 | 5 / 785 |

The reroute and review entries above are total events across 30 scheduled runs. Divide each by 30 for frequency per run; the exact per-run counts and their density means are in `individual_runs-batch.csv` and `summary-batch.csv`, respectively. Real fallback events and their full-precision decision latencies are in `results/processed/fallback_validation.csv`. The activation count excludes forced diagnostic configurations.

A real batch example is medium seed 1: the scheduled Mist work lasted 1066.00 ms, exceeded the 800 ms watchdog, and Fog applied the route after 1126.65 ms. The recorded reason is `watchdog_timeout`.

## Density and seed behavior

Distinct SUMO traffic counts and seeded trip origins demonstrate different injected demand. Routing log `evaluated` rows record live candidate costs and `applied` rows record actual reroutes; the count table above measures their density dependence.

- **Low**: 30 seeds; 6 EM nondeliveries (seeds 6, 12, 18, 23, 25, 28); 507 positive periodic cost evaluations with 5 distinct costs spanning 20.85–103.10 s; 3 applied reroutes. Examples: seed 8 at 106.803 s (cost_improvement), seed 11 at 111.757 s (cost_improvement), seed 27 at 113.179 s (cost_improvement).
- **Medium**: 30 seeds; 1 EM nondeliveries (seeds 25); 614 positive periodic cost evaluations with 9 distinct costs spanning 20.85–144.79 s; 6 applied reroutes. Examples: seed 5 at 111.256 s (cost_improvement), seed 8 at 111.658 s (cost_improvement), seed 18 at 136.786 s (cost_improvement).
- **High**: 30 seeds; 0 EM nondeliveries; 641 positive periodic cost evaluations with 21 distinct costs spanning 20.85–110.04 s; 6 applied reroutes. Examples: seed 5 at 101.78 s (cost_improvement), seed 8 at 131.465 s (cost_improvement), seed 22 at 112.811 s (cost_improvement).

Specific current high-density routing events include a cost-improvement reroute at 112.811 s in seed 22 and at 102.033 s in seed 27. High seed 4 performed 26 periodic evaluations and no applied reroute under the new parameters. These are actual routing-log outcomes; a route review does not necessarily change the route.

The throughput values remain close because the metric divides one fixed 256-byte EM payload by 900 s, with variation driven chiefly by delivery success. `results/processed/before_after_headline.csv` gives the measured 650 m to 400 m change for every primary metric and configuration without treating historical results as part of the current batch.
