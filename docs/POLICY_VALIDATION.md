# Matched signal-policy results

This study compares Fog and Cloud route planning with local Mist route planning and a Fog fallback. SUMO moves the vehicles and controls safe driving. OMNeT++ and Veins carry the emergency message through roadside units and vehicles. After the EV receives the message, the selected framework plans a route and requests safe signal priority. Dynamic Mist reviews received road information as the EV travels. A 500 ms watchdog requests Fog when initial Mist work is unfinished. The 900 ms worker stalls are controlled injected faults, not naturally observed failures.

Low, medium and high demand use 72, 144 and 200 scheduled background trips. Every configuration shares the same trips and EV speed cap for each matched seed. All 30 reported seeds are retained. Ordinary traffic and the existing physical obstruction are separate experiments.

Preserved original-policy comparisons and fair advance-policy controls. Negative changes favor proposed for latency, response, stops and delay; positive changes favor proposed for green share and speed. Difference intervals are proposed minus baseline. Time metrics use available delivered pairs.

## Supervisor requirements A–D, matched advance policy

FogCloudAStarAdvance uses exactly the same 250 m / 20 s request policy as proposed. The two-step policy ablations are retained in paired_comparisons.csv.

| Context | Density | Requirement / metric | Baseline | Proposed | Change % | Paired difference 95% CI | Pairs |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| ordinary | low | A: decision ms | 626.539 | 471.991 | -24.67 | [-252.683, -56.413] | 24 |
| ordinary | low | B: response s | 147.542 | 147.104 | -0.30 | [-0.637, -0.238] | 24 |
| ordinary | low | D: signal waiting s | 0.000 | 0.000 | undefined (baseline zero) | [0.000, 0.000] | 24 |
| ordinary | low | C: full stops | 1.000 | 1.000 | 0.00 | [0.000, 0.000] | 24 |
| ordinary | low | C: green approach share | 1.000 | 1.000 | 0.00 | [0.000, 0.000] | 24 |
| ordinary | low | C: background time loss s | 65.138 | 65.161 | 0.03 | [-0.261, 0.306] | 30 |
| ordinary | medium | A: decision ms | 626.543 | 464.096 | -25.93 | [-249.060, -75.833] | 29 |
| ordinary | medium | B: response s | 148.000 | 147.362 | -0.43 | [-1.047, -0.228] | 29 |
| ordinary | medium | D: signal waiting s | 0.000 | 0.000 | undefined (baseline zero) | [0.000, 0.000] | 29 |
| ordinary | medium | C: full stops | 1.000 | 1.000 | 0.00 | [0.000, 0.000] | 29 |
| ordinary | medium | C: green approach share | 1.000 | 1.000 | 0.00 | [0.000, 0.000] | 29 |
| ordinary | medium | C: background time loss s | 63.869 | 64.071 | 0.32 | [-0.131, 0.536] | 30 |
| ordinary | high | A: decision ms | 626.539 | 459.501 | -26.66 | [-251.118, -82.958] | 30 |
| ordinary | high | B: response s | 147.717 | 146.733 | -0.67 | [-1.548, -0.419] | 30 |
| ordinary | high | D: signal waiting s | 0.000 | 0.000 | undefined (baseline zero) | [0.000, 0.000] | 30 |
| ordinary | high | C: full stops | 1.000 | 1.000 | 0.00 | [0.000, 0.000] | 30 |
| ordinary | high | C: green approach share | 1.000 | 1.000 | 0.00 | [0.000, 0.000] | 30 |
| ordinary | high | C: background time loss s | 69.127 | 69.215 | 0.13 | [-0.527, 0.704] | 30 |
| obstruction | low | A: decision ms | 626.539 | 471.991 | -24.67 | [-252.683, -56.413] | 24 |
| obstruction | low | B: response s | 264.792 | 144.417 | -45.46 | [-121.456, -119.294] | 24 |
| obstruction | low | D: signal waiting s | 4.542 | 0.000 | -100.00 | [-13.937, 4.853] | 24 |
| obstruction | low | C: full stops | 2.083 | 1.000 | -52.00 | [-1.256, -0.911] | 24 |
| obstruction | low | C: green approach share | 1.000 | 1.000 | 0.00 | [0.000, 0.000] | 24 |
| obstruction | low | C: background time loss s | 71.281 | 68.899 | -3.34 | [-3.526, -1.238] | 30 |
| obstruction | medium | A: decision ms | 626.543 | 464.096 | -25.93 | [-249.060, -75.833] | 29 |
| obstruction | medium | B: response s | 263.466 | 158.224 | -39.95 | [-120.227, -90.256] | 29 |
| obstruction | medium | D: signal waiting s | 4.017 | 4.448 | 10.73 | [-0.452, 1.314] | 29 |
| obstruction | medium | C: full stops | 2.034 | 1.103 | -45.76 | [-1.029, -0.833] | 29 |
| obstruction | medium | C: green approach share | 0.972 | 0.997 | 2.51 | [-0.003, 0.052] | 29 |
| obstruction | medium | C: background time loss s | 71.614 | 69.137 | -3.46 | [-3.924, -1.030] | 30 |
| obstruction | high | A: decision ms | 626.539 | 459.501 | -26.66 | [-251.118, -82.958] | 30 |
| obstruction | high | B: response s | 266.617 | 160.083 | -39.96 | [-126.012, -87.054] | 30 |
| obstruction | high | D: signal waiting s | 12.067 | 5.267 | -56.35 | [-17.749, 4.149] | 30 |
| obstruction | high | C: full stops | 2.233 | 1.233 | -44.78 | [-1.340, -0.660] | 30 |
| obstruction | high | C: green approach share | 0.987 | 0.995 | 0.87 | [-0.013, 0.030] | 30 |
| obstruction | high | C: background time loss s | 80.025 | 76.234 | -4.74 | [-5.829, -1.752] | 30 |

## Separate the signal policy and framework effects

The original comparison changes both the framework and signal request timing. The matched comparison holds request timing equal. Fog advance versus Fog reactive isolates the signal policy within Fog routing; Mist advance versus Mist reactive does the same within static Mist. Framework differences also include initial computation and controlled fallback, so matched results are not claimed as routing alone. All other measured contrasts are in paired_comparisons.csv.

| Context | Density | Comparison | Baseline response s | Comparison response s | Change % | Paired difference 95% CI s | Pairs |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| ordinary | low | Proposed versus Fog reactive | 153.312 | 147.104 | -4.05 | [-6.815, -5.602] | 24 |
| ordinary | medium | Proposed versus Fog reactive | 154.517 | 147.362 | -4.63 | [-8.562, -5.748] | 29 |
| ordinary | high | Proposed versus Fog reactive | 156.200 | 146.733 | -6.06 | [-11.425, -7.508] | 30 |
| ordinary | low | Proposed versus Fog advance | 147.542 | 147.104 | -0.30 | [-0.637, -0.238] | 24 |
| ordinary | medium | Proposed versus Fog advance | 148.000 | 147.362 | -0.43 | [-1.047, -0.228] | 29 |
| ordinary | high | Proposed versus Fog advance | 147.717 | 146.733 | -0.67 | [-1.548, -0.419] | 30 |
| ordinary | low | Fog advance versus Fog reactive | 153.312 | 147.542 | -3.76 | [-6.331, -5.211] | 24 |
| ordinary | medium | Fog advance versus Fog reactive | 154.517 | 148.000 | -4.22 | [-7.849, -5.185] | 29 |
| ordinary | high | Fog advance versus Fog reactive | 156.200 | 147.717 | -5.43 | [-10.193, -6.774] | 30 |
| ordinary | low | Mist advance versus Mist reactive | 153.500 | 147.146 | -4.14 | [-7.340, -5.369] | 24 |
| ordinary | medium | Mist advance versus Mist reactive | 154.724 | 147.397 | -4.74 | [-8.712, -5.944] | 29 |
| ordinary | high | Mist advance versus Mist reactive | 156.883 | 147.500 | -5.98 | [-11.327, -7.440] | 30 |
| ordinary | low | Proposed versus Mist advance | 147.146 | 147.104 | -0.03 | [-0.128, 0.045] | 24 |
| ordinary | medium | Proposed versus Mist advance | 147.397 | 147.362 | -0.02 | [-0.800, 0.731] | 29 |
| ordinary | high | Proposed versus Mist advance | 147.500 | 146.733 | -0.52 | [-1.361, -0.173] | 30 |
| obstruction | low | Proposed versus Fog reactive | 266.292 | 144.417 | -45.77 | [-123.458, -120.292] | 24 |
| obstruction | medium | Proposed versus Fog reactive | 272.259 | 158.224 | -41.88 | [-129.772, -98.297] | 29 |
| obstruction | high | Proposed versus Fog reactive | 278.417 | 160.083 | -42.50 | [-138.200, -98.466] | 30 |
| obstruction | low | Proposed versus Fog advance | 264.792 | 144.417 | -45.46 | [-121.456, -119.294] | 24 |
| obstruction | medium | Proposed versus Fog advance | 263.466 | 158.224 | -39.95 | [-120.227, -90.256] | 29 |
| obstruction | high | Proposed versus Fog advance | 266.617 | 160.083 | -39.96 | [-126.012, -87.054] | 30 |
| obstruction | low | Fog advance versus Fog reactive | 266.292 | 264.792 | -0.56 | [-2.821, -0.179] | 24 |
| obstruction | medium | Fog advance versus Fog reactive | 272.259 | 263.466 | -3.23 | [-12.095, -5.491] | 29 |
| obstruction | high | Fog advance versus Fog reactive | 278.417 | 266.617 | -4.24 | [-15.254, -8.346] | 30 |
| obstruction | low | Mist advance versus Mist reactive | 266.500 | 265.021 | -0.56 | [-2.960, 0.001] | 24 |
| obstruction | medium | Mist advance versus Mist reactive | 272.586 | 263.517 | -3.33 | [-12.328, -5.810] | 29 |
| obstruction | high | Mist advance versus Mist reactive | 278.750 | 266.417 | -4.42 | [-16.012, -8.654] | 30 |
| obstruction | low | Proposed versus Mist advance | 265.021 | 144.417 | -45.51 | [-121.798, -119.410] | 24 |
| obstruction | medium | Proposed versus Mist advance | 263.517 | 158.224 | -39.96 | [-120.282, -90.304] | 29 |
| obstruction | high | Proposed versus Mist advance | 266.417 | 160.083 | -39.91 | [-125.811, -86.855] | 30 |

## Seven primary metrics

Cells show the measured mean and sample count. Their 95% intervals are in summary.csv and every graph. PDR and EM throughput describe the shared alert service, which acts before routing. One delivered 256 byte EM contributes 2048 / 900 = 2.27556 bit/s; equal throughput among delivered runs is expected under this definition. No-preemption is displayed only on the signal waiting graph.

### ordinary low

| Configuration | PDR | NRL | EM throughput bit/s | EM E2E ms | Decision ms | Response s | Signal wait s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FogCloudAStar | 0.800 (n=30) | 22038.208 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 626.539 (n=24) | 153.312 (n=24) | 1.562 (n=24) |
| MistAStar | 0.800 (n=30) | 22038.250 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 588.500 (n=24) | 153.500 (n=24) | 1.833 (n=24) |
| MistDynamicAStar | 0.800 (n=30) | 22059.375 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 588.500 (n=24) | 147.167 (n=24) | 0.000 (n=24) |
| MistDynamicFogFallback | 0.800 (n=30) | 22062.042 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 471.991 (n=24) | 147.104 (n=24) | 0.000 (n=24) |
| FogCloudAStarAdvance | 0.800 (n=30) | 22057.417 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 626.539 (n=24) | 147.542 (n=24) | 0.000 (n=24) |
| MistAStarAdvance | 0.800 (n=30) | 22053.417 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 588.500 (n=24) | 147.146 (n=24) | 0.000 (n=24) |

### ordinary medium

| Configuration | PDR | NRL | EM throughput bit/s | EM E2E ms | Decision ms | Response s | Signal wait s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FogCloudAStar | 0.967 (n=30) | 39778.655 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 626.543 (n=29) | 154.517 (n=29) | 0.845 (n=29) |
| MistAStar | 0.967 (n=30) | 39778.172 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 574.276 (n=29) | 154.724 (n=29) | 0.914 (n=29) |
| MistDynamicAStar | 0.967 (n=30) | 39892.759 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 574.276 (n=29) | 147.362 (n=29) | 0.000 (n=29) |
| MistDynamicFogFallback | 0.967 (n=30) | 39899.931 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 464.096 (n=29) | 147.362 (n=29) | 0.000 (n=29) |
| FogCloudAStarAdvance | 0.967 (n=30) | 39884.483 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 626.543 (n=29) | 148.000 (n=29) | 0.000 (n=29) |
| MistAStarAdvance | 0.967 (n=30) | 39855.897 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 574.276 (n=29) | 147.397 (n=29) | 0.000 (n=29) |

### ordinary high

| Configuration | PDR | NRL | EM throughput bit/s | EM E2E ms | Decision ms | Response s | Signal wait s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FogCloudAStar | 1.000 (n=30) | 54436.100 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 626.539 (n=30) | 156.200 (n=30) | 0.667 (n=30) |
| MistAStar | 1.000 (n=30) | 54300.267 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 566.000 (n=30) | 156.883 (n=30) | 0.717 (n=30) |
| MistDynamicAStar | 1.000 (n=30) | 54515.433 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 566.000 (n=30) | 147.517 (n=30) | 0.400 (n=30) |
| MistDynamicFogFallback | 1.000 (n=30) | 54511.800 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 459.501 (n=30) | 146.733 (n=30) | 0.000 (n=30) |
| FogCloudAStarAdvance | 1.000 (n=30) | 54531.633 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 626.539 (n=30) | 147.717 (n=30) | 0.000 (n=30) |
| MistAStarAdvance | 1.000 (n=30) | 54535.033 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 566.000 (n=30) | 147.500 (n=30) | 0.000 (n=30) |

### obstruction low

| Configuration | PDR | NRL | EM throughput bit/s | EM E2E ms | Decision ms | Response s | Signal wait s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FogCloudAStar | 0.800 (n=30) | 23037.833 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 626.539 (n=24) | 266.292 (n=24) | 4.417 (n=24) |
| MistAStar | 0.800 (n=30) | 23012.417 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 588.500 (n=24) | 266.500 (n=24) | 4.479 (n=24) |
| MistDynamicAStar | 0.800 (n=30) | 23021.125 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 588.500 (n=24) | 144.521 (n=24) | 0.000 (n=24) |
| MistDynamicFogFallback | 0.800 (n=30) | 23023.750 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 471.991 (n=24) | 144.417 (n=24) | 0.000 (n=24) |
| FogCloudAStarAdvance | 0.800 (n=30) | 23387.792 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 626.539 (n=24) | 264.792 (n=24) | 4.542 (n=24) |
| MistAStarAdvance | 0.800 (n=30) | 23371.583 (n=24) | 1.820 (n=30) | 44.366 (n=24) | 588.500 (n=24) | 265.021 (n=24) | 4.583 (n=24) |

### obstruction medium

| Configuration | PDR | NRL | EM throughput bit/s | EM E2E ms | Decision ms | Response s | Signal wait s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FogCloudAStar | 0.967 (n=30) | 41605.241 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 626.543 (n=29) | 272.259 (n=29) | 11.707 (n=29) |
| MistAStar | 0.967 (n=30) | 41567.966 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 574.276 (n=29) | 272.586 (n=29) | 11.793 (n=29) |
| MistDynamicAStar | 0.967 (n=30) | 41345.552 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 574.276 (n=29) | 158.310 (n=29) | 4.448 (n=29) |
| MistDynamicFogFallback | 0.967 (n=30) | 41349.448 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 464.096 (n=29) | 158.224 (n=29) | 4.448 (n=29) |
| FogCloudAStarAdvance | 0.967 (n=30) | 41763.103 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 626.543 (n=29) | 263.466 (n=29) | 4.017 (n=29) |
| MistAStarAdvance | 0.967 (n=30) | 41730.103 (n=29) | 2.200 (n=30) | 37.123 (n=29) | 574.276 (n=29) | 263.517 (n=29) | 4.017 (n=29) |

### obstruction high

| Configuration | PDR | NRL | EM throughput bit/s | EM E2E ms | Decision ms | Response s | Signal wait s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FogCloudAStar | 1.000 (n=30) | 56833.500 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 626.539 (n=30) | 278.417 (n=30) | 26.483 (n=30) |
| MistAStar | 1.000 (n=30) | 56859.667 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 566.000 (n=30) | 278.750 (n=30) | 23.183 (n=30) |
| MistDynamicAStar | 1.000 (n=30) | 56674.100 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 566.000 (n=30) | 160.050 (n=30) | 5.267 (n=30) |
| MistDynamicFogFallback | 1.000 (n=30) | 56666.133 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 459.501 (n=30) | 160.083 (n=30) | 5.267 (n=30) |
| FogCloudAStarAdvance | 1.000 (n=30) | 57511.733 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 626.539 (n=30) | 266.617 (n=30) | 12.067 (n=30) |
| MistAStarAdvance | 1.000 (n=30) | 57394.433 (n=30) | 2.276 (n=30) | 32.171 (n=30) | 566.000 (n=30) | 266.417 (n=30) | 11.983 (n=30) |


## Interpretation and limits

A: only an interval below zero supports faster decisions. B: compare the measured size with the requested substantial margin; ordinary physical limits remain. C: full stops, green passage and background time loss are distinct operational measures, but none is guaranteed to improve. D: zero waiting is retained when observed; no artificial stop is inserted. Whole-route slow time detects crawling hidden by the 20 m / 0.1 m/s waiting definition. Green classification is sampled within 500 ms and cannot prove the exact continuous crossing instant. Controlled 900 ms stalls remain injected faults. Ordinary and obstruction results are not pooled.

Full new graphs and CSVs are in results/policy_validation/. Earlier main results and the previous Word submission are retained as historical results, not overwritten or presented as the new policy experiment.

## Held-out tuning outcome

The fixed rule selected MistTuningReference. Only seeds 101–110 were used. Each candidate has 60 scheduled density/context/seed cells; response means use the same delivered cells. No reported seed was used for selection. The selected settings and model-source/binary hashes were frozen before reported runs.

| Candidate | Scheduled | Arrivals | Mean response s | Mean applied route changes |
| --- | ---: | ---: | ---: | ---: |
| MistTuningReference | 60 | 54 | 148.870 | 0.722 |
| MistTuningFast | 60 | 54 | 151.639 | 0.944 |
| MistTuningBalanced | 60 | 54 | 156.519 | 0.889 |

The tested tuning alternatives did not improve held-out response. The reference was retained; this experiment does not claim a new routing improvement from those alternatives.

## Signal waiting and whole-route motion

Means below use delivered runs. Near-signal slow time uses speed below 1 m/s within the same 20 m signal zone. The scheduled-start stop count localizes stop onsets on A0A1 within 0.2 m of the shared 30 m stop. Other stops are not automatically attributed to signals. All durations retain the 500 ms SUMO state resolution.

| Context | Density | Configuration | Arrivals | Zero signal waits | Signal wait s | Whole-route below 1 m/s s | Near-signal below 1 m/s s | Full stops | Stops at scheduled start | Green on approach share |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ordinary | low | FogCloudAStarAdvance | 24 | 24 | 0.000 | 1.217 | 0.000 | 1.000 | 1.000 | 1.000 |
| ordinary | low | MistDynamicFogFallback | 24 | 24 | 0.000 | 0.996 | 0.000 | 1.000 | 1.000 | 1.000 |
| ordinary | medium | FogCloudAStarAdvance | 29 | 29 | 0.000 | 1.145 | 0.000 | 1.000 | 1.000 | 1.000 |
| ordinary | medium | MistDynamicFogFallback | 29 | 29 | 0.000 | 1.048 | 0.000 | 1.000 | 1.000 | 1.000 |
| ordinary | high | FogCloudAStarAdvance | 30 | 30 | 0.000 | 1.183 | 0.000 | 1.000 | 1.000 | 1.000 |
| ordinary | high | MistDynamicFogFallback | 30 | 30 | 0.000 | 0.967 | 0.000 | 1.000 | 1.000 | 1.000 |
| obstruction | low | FogCloudAStarAdvance | 24 | 23 | 4.542 | 105.467 | 4.583 | 2.083 | 1.000 | 1.000 |
| obstruction | low | MistDynamicFogFallback | 24 | 24 | 0.000 | 0.996 | 0.000 | 1.000 | 1.000 | 1.000 |
| obstruction | medium | FogCloudAStarAdvance | 29 | 28 | 4.017 | 107.266 | 4.259 | 2.034 | 1.000 | 0.972 |
| obstruction | medium | MistDynamicFogFallback | 29 | 27 | 4.448 | 5.979 | 4.931 | 1.103 | 1.000 | 0.997 |
| obstruction | high | FogCloudAStarAdvance | 30 | 26 | 12.067 | 110.167 | 12.467 | 2.233 | 1.000 | 0.987 |
| obstruction | high | MistDynamicFogFallback | 30 | 26 | 5.267 | 6.767 | 5.767 | 1.233 | 1.000 | 0.995 |

## Physical obstruction realization

FCD records at least one physically stopped incident vehicle during 90–250 s in 540/540 assigned obstruction runs. No seed is dropped for weaker realized exposure. Per-run insertion and maximum queue counts are exported.

| Configuration | Density | Runs | Any stopped blocker | All three stopped together |
| --- | --- | ---: | ---: | ---: |
| FogCloudAStar | low | 30 | 30 | 30 |
| FogCloudAStar | medium | 30 | 30 | 30 |
| FogCloudAStar | high | 30 | 30 | 28 |
| MistAStar | low | 30 | 30 | 30 |
| MistAStar | medium | 30 | 30 | 30 |
| MistAStar | high | 30 | 30 | 28 |
| MistDynamicAStar | low | 30 | 30 | 30 |
| MistDynamicAStar | medium | 30 | 30 | 30 |
| MistDynamicAStar | high | 30 | 30 | 28 |
| MistDynamicFogFallback | low | 30 | 30 | 30 |
| MistDynamicFogFallback | medium | 30 | 30 | 30 |
| MistDynamicFogFallback | high | 30 | 30 | 28 |
| FogCloudAStarAdvance | low | 30 | 30 | 30 |
| FogCloudAStarAdvance | medium | 30 | 30 | 30 |
| FogCloudAStarAdvance | high | 30 | 30 | 28 |
| MistAStarAdvance | low | 30 | 30 | 30 |
| MistAStarAdvance | medium | 30 | 30 | 30 |
| MistAStarAdvance | high | 30 | 30 | 28 |

## Measured requirement verdicts

The previously requested 20% margin is shown as a reference for B, not a data-acceptance gate. C requires at least two supported improvements among full stops, green share and background time loss. D distinguishes lower waiting from the requested nonzero waiting.

| Context | Density | A: decision | B: at least 20% response reduction | C: two distinct supported metric wins | D: lower and positive signal waiting |
| --- | --- | --- | --- | --- | --- |
| ordinary | low | Met | Not met | Not met (0/3) | Zero retained; nonzero request not met |
| ordinary | medium | Met | Not met | Not met (0/3) | Zero retained; nonzero request not met |
| ordinary | high | Met | Not met | Not met (0/3) | Zero retained; nonzero request not met |
| obstruction | low | Met | Met | Met (2/3) | Zero retained; nonzero request not met |
| obstruction | medium | Met | Met | Met (2/3) | Improvement not established |
| obstruction | high | Met | Met | Met (2/3) | Improvement not established |

## All new comparison graphs

Each figure uses the same raw-to-summary pipeline. No-preemption appears only for traffic-light waiting. Original and matched policy labels are visible on the axes.

### ordinary: pdr-low

![pdr-low](../results/policy_validation/ordinary/graphs/pdr-low.png)

### ordinary: pdr-medium

![pdr-medium](../results/policy_validation/ordinary/graphs/pdr-medium.png)

### ordinary: pdr-high

![pdr-high](../results/policy_validation/ordinary/graphs/pdr-high.png)

### ordinary: nrl-low

![nrl-low](../results/policy_validation/ordinary/graphs/nrl-low.png)

### ordinary: nrl-medium

![nrl-medium](../results/policy_validation/ordinary/graphs/nrl-medium.png)

### ordinary: nrl-high

![nrl-high](../results/policy_validation/ordinary/graphs/nrl-high.png)

### ordinary: throughput_bps-low

![throughput_bps-low](../results/policy_validation/ordinary/graphs/throughput_bps-low.png)

### ordinary: throughput_bps-medium

![throughput_bps-medium](../results/policy_validation/ordinary/graphs/throughput_bps-medium.png)

### ordinary: throughput_bps-high

![throughput_bps-high](../results/policy_validation/ordinary/graphs/throughput_bps-high.png)

### ordinary: e2e_delay_ms-low

![e2e_delay_ms-low](../results/policy_validation/ordinary/graphs/e2e_delay_ms-low.png)

### ordinary: e2e_delay_ms-medium

![e2e_delay_ms-medium](../results/policy_validation/ordinary/graphs/e2e_delay_ms-medium.png)

### ordinary: e2e_delay_ms-high

![e2e_delay_ms-high](../results/policy_validation/ordinary/graphs/e2e_delay_ms-high.png)

### ordinary: route_decision_ms-low

![route_decision_ms-low](../results/policy_validation/ordinary/graphs/route_decision_ms-low.png)

### ordinary: route_decision_ms-medium

![route_decision_ms-medium](../results/policy_validation/ordinary/graphs/route_decision_ms-medium.png)

### ordinary: route_decision_ms-high

![route_decision_ms-high](../results/policy_validation/ordinary/graphs/route_decision_ms-high.png)

### ordinary: ev_response_s-low

![ev_response_s-low](../results/policy_validation/ordinary/graphs/ev_response_s-low.png)

### ordinary: ev_response_s-medium

![ev_response_s-medium](../results/policy_validation/ordinary/graphs/ev_response_s-medium.png)

### ordinary: ev_response_s-high

![ev_response_s-high](../results/policy_validation/ordinary/graphs/ev_response_s-high.png)

### ordinary: traffic_light_wait_s-low

![traffic_light_wait_s-low](../results/policy_validation/ordinary/graphs/traffic_light_wait_s-low.png)

### ordinary: traffic_light_wait_s-medium

![traffic_light_wait_s-medium](../results/policy_validation/ordinary/graphs/traffic_light_wait_s-medium.png)

### ordinary: traffic_light_wait_s-high

![traffic_light_wait_s-high](../results/policy_validation/ordinary/graphs/traffic_light_wait_s-high.png)

### ordinary: control_transmissions-low

![control_transmissions-low](../results/policy_validation/ordinary/graphs/control_transmissions-low.png)

### ordinary: control_transmissions-medium

![control_transmissions-medium](../results/policy_validation/ordinary/graphs/control_transmissions-medium.png)

### ordinary: control_transmissions-high

![control_transmissions-high](../results/policy_validation/ordinary/graphs/control_transmissions-high.png)

### ordinary: control_bytes-low

![control_bytes-low](../results/policy_validation/ordinary/graphs/control_bytes-low.png)

### ordinary: control_bytes-medium

![control_bytes-medium](../results/policy_validation/ordinary/graphs/control_bytes-medium.png)

### ordinary: control_bytes-high

![control_bytes-high](../results/policy_validation/ordinary/graphs/control_bytes-high.png)

### ordinary: route_changes-low

![route_changes-low](../results/policy_validation/ordinary/graphs/route_changes-low.png)

### ordinary: route_changes-medium

![route_changes-medium](../results/policy_validation/ordinary/graphs/route_changes-medium.png)

### ordinary: route_changes-high

![route_changes-high](../results/policy_validation/ordinary/graphs/route_changes-high.png)

### ordinary: route_reviews-low

![route_reviews-low](../results/policy_validation/ordinary/graphs/route_reviews-low.png)

### ordinary: route_reviews-medium

![route_reviews-medium](../results/policy_validation/ordinary/graphs/route_reviews-medium.png)

### ordinary: route_reviews-high

![route_reviews-high](../results/policy_validation/ordinary/graphs/route_reviews-high.png)

### ordinary: fallback_triggered-low

![fallback_triggered-low](../results/policy_validation/ordinary/graphs/fallback_triggered-low.png)

### ordinary: fallback_triggered-medium

![fallback_triggered-medium](../results/policy_validation/ordinary/graphs/fallback_triggered-medium.png)

### ordinary: fallback_triggered-high

![fallback_triggered-high](../results/policy_validation/ordinary/graphs/fallback_triggered-high.png)

### ordinary: fallback_decision_ms-low

![fallback_decision_ms-low](../results/policy_validation/ordinary/graphs/fallback_decision_ms-low.png)

### ordinary: fallback_decision_ms-medium

![fallback_decision_ms-medium](../results/policy_validation/ordinary/graphs/fallback_decision_ms-medium.png)

### ordinary: fallback_decision_ms-high

![fallback_decision_ms-high](../results/policy_validation/ordinary/graphs/fallback_decision_ms-high.png)

### ordinary: ev_delay_vs_freeflow_s-low

![ev_delay_vs_freeflow_s-low](../results/policy_validation/ordinary/graphs/ev_delay_vs_freeflow_s-low.png)

### ordinary: ev_delay_vs_freeflow_s-medium

![ev_delay_vs_freeflow_s-medium](../results/policy_validation/ordinary/graphs/ev_delay_vs_freeflow_s-medium.png)

### ordinary: ev_delay_vs_freeflow_s-high

![ev_delay_vs_freeflow_s-high](../results/policy_validation/ordinary/graphs/ev_delay_vs_freeflow_s-high.png)

### ordinary: ev_distance_m-low

![ev_distance_m-low](../results/policy_validation/ordinary/graphs/ev_distance_m-low.png)

### ordinary: ev_distance_m-medium

![ev_distance_m-medium](../results/policy_validation/ordinary/graphs/ev_distance_m-medium.png)

### ordinary: ev_distance_m-high

![ev_distance_m-high](../results/policy_validation/ordinary/graphs/ev_distance_m-high.png)

### ordinary: ev_travel_s-low

![ev_travel_s-low](../results/policy_validation/ordinary/graphs/ev_travel_s-low.png)

### ordinary: ev_travel_s-medium

![ev_travel_s-medium](../results/policy_validation/ordinary/graphs/ev_travel_s-medium.png)

### ordinary: ev_travel_s-high

![ev_travel_s-high](../results/policy_validation/ordinary/graphs/ev_travel_s-high.png)

### ordinary: ev_full_stops-low

![ev_full_stops-low](../results/policy_validation/ordinary/graphs/ev_full_stops-low.png)

### ordinary: ev_full_stops-medium

![ev_full_stops-medium](../results/policy_validation/ordinary/graphs/ev_full_stops-medium.png)

### ordinary: ev_full_stops-high

![ev_full_stops-high](../results/policy_validation/ordinary/graphs/ev_full_stops-high.png)

### ordinary: ev_below_1_s-low

![ev_below_1_s-low](../results/policy_validation/ordinary/graphs/ev_below_1_s-low.png)

### ordinary: ev_below_1_s-medium

![ev_below_1_s-medium](../results/policy_validation/ordinary/graphs/ev_below_1_s-medium.png)

### ordinary: ev_below_1_s-high

![ev_below_1_s-high](../results/policy_validation/ordinary/graphs/ev_below_1_s-high.png)

### ordinary: ev_whole_stopped_s-low

![ev_whole_stopped_s-low](../results/policy_validation/ordinary/graphs/ev_whole_stopped_s-low.png)

### ordinary: ev_whole_stopped_s-medium

![ev_whole_stopped_s-medium](../results/policy_validation/ordinary/graphs/ev_whole_stopped_s-medium.png)

### ordinary: ev_whole_stopped_s-high

![ev_whole_stopped_s-high](../results/policy_validation/ordinary/graphs/ev_whole_stopped_s-high.png)

### ordinary: ev_green_fraction-low

![ev_green_fraction-low](../results/policy_validation/ordinary/graphs/ev_green_fraction-low.png)

### ordinary: ev_green_fraction-medium

![ev_green_fraction-medium](../results/policy_validation/ordinary/graphs/ev_green_fraction-medium.png)

### ordinary: ev_green_fraction-high

![ev_green_fraction-high](../results/policy_validation/ordinary/graphs/ev_green_fraction-high.png)

### ordinary: ev_green_count-low

![ev_green_count-low](../results/policy_validation/ordinary/graphs/ev_green_count-low.png)

### ordinary: ev_green_count-medium

![ev_green_count-medium](../results/policy_validation/ordinary/graphs/ev_green_count-medium.png)

### ordinary: ev_green_count-high

![ev_green_count-high](../results/policy_validation/ordinary/graphs/ev_green_count-high.png)

### ordinary: ev_green_approach_fraction-low

![ev_green_approach_fraction-low](../results/policy_validation/ordinary/graphs/ev_green_approach_fraction-low.png)

### ordinary: ev_green_approach_fraction-medium

![ev_green_approach_fraction-medium](../results/policy_validation/ordinary/graphs/ev_green_approach_fraction-medium.png)

### ordinary: ev_green_approach_fraction-high

![ev_green_approach_fraction-high](../results/policy_validation/ordinary/graphs/ev_green_approach_fraction-high.png)

### ordinary: background_time_loss_s-low

![background_time_loss_s-low](../results/policy_validation/ordinary/graphs/background_time_loss_s-low.png)

### ordinary: background_time_loss_s-medium

![background_time_loss_s-medium](../results/policy_validation/ordinary/graphs/background_time_loss_s-medium.png)

### ordinary: background_time_loss_s-high

![background_time_loss_s-high](../results/policy_validation/ordinary/graphs/background_time_loss_s-high.png)

### ordinary: ev_mean_speed_mps-low

![ev_mean_speed_mps-low](../results/policy_validation/ordinary/graphs/ev_mean_speed_mps-low.png)

### ordinary: ev_mean_speed_mps-medium

![ev_mean_speed_mps-medium](../results/policy_validation/ordinary/graphs/ev_mean_speed_mps-medium.png)

### ordinary: ev_mean_speed_mps-high

![ev_mean_speed_mps-high](../results/policy_validation/ordinary/graphs/ev_mean_speed_mps-high.png)

### obstruction: pdr-low

![pdr-low](../results/policy_validation/obstruction/graphs/pdr-low.png)

### obstruction: pdr-medium

![pdr-medium](../results/policy_validation/obstruction/graphs/pdr-medium.png)

### obstruction: pdr-high

![pdr-high](../results/policy_validation/obstruction/graphs/pdr-high.png)

### obstruction: nrl-low

![nrl-low](../results/policy_validation/obstruction/graphs/nrl-low.png)

### obstruction: nrl-medium

![nrl-medium](../results/policy_validation/obstruction/graphs/nrl-medium.png)

### obstruction: nrl-high

![nrl-high](../results/policy_validation/obstruction/graphs/nrl-high.png)

### obstruction: throughput_bps-low

![throughput_bps-low](../results/policy_validation/obstruction/graphs/throughput_bps-low.png)

### obstruction: throughput_bps-medium

![throughput_bps-medium](../results/policy_validation/obstruction/graphs/throughput_bps-medium.png)

### obstruction: throughput_bps-high

![throughput_bps-high](../results/policy_validation/obstruction/graphs/throughput_bps-high.png)

### obstruction: e2e_delay_ms-low

![e2e_delay_ms-low](../results/policy_validation/obstruction/graphs/e2e_delay_ms-low.png)

### obstruction: e2e_delay_ms-medium

![e2e_delay_ms-medium](../results/policy_validation/obstruction/graphs/e2e_delay_ms-medium.png)

### obstruction: e2e_delay_ms-high

![e2e_delay_ms-high](../results/policy_validation/obstruction/graphs/e2e_delay_ms-high.png)

### obstruction: route_decision_ms-low

![route_decision_ms-low](../results/policy_validation/obstruction/graphs/route_decision_ms-low.png)

### obstruction: route_decision_ms-medium

![route_decision_ms-medium](../results/policy_validation/obstruction/graphs/route_decision_ms-medium.png)

### obstruction: route_decision_ms-high

![route_decision_ms-high](../results/policy_validation/obstruction/graphs/route_decision_ms-high.png)

### obstruction: ev_response_s-low

![ev_response_s-low](../results/policy_validation/obstruction/graphs/ev_response_s-low.png)

### obstruction: ev_response_s-medium

![ev_response_s-medium](../results/policy_validation/obstruction/graphs/ev_response_s-medium.png)

### obstruction: ev_response_s-high

![ev_response_s-high](../results/policy_validation/obstruction/graphs/ev_response_s-high.png)

### obstruction: traffic_light_wait_s-low

![traffic_light_wait_s-low](../results/policy_validation/obstruction/graphs/traffic_light_wait_s-low.png)

### obstruction: traffic_light_wait_s-medium

![traffic_light_wait_s-medium](../results/policy_validation/obstruction/graphs/traffic_light_wait_s-medium.png)

### obstruction: traffic_light_wait_s-high

![traffic_light_wait_s-high](../results/policy_validation/obstruction/graphs/traffic_light_wait_s-high.png)

### obstruction: control_transmissions-low

![control_transmissions-low](../results/policy_validation/obstruction/graphs/control_transmissions-low.png)

### obstruction: control_transmissions-medium

![control_transmissions-medium](../results/policy_validation/obstruction/graphs/control_transmissions-medium.png)

### obstruction: control_transmissions-high

![control_transmissions-high](../results/policy_validation/obstruction/graphs/control_transmissions-high.png)

### obstruction: control_bytes-low

![control_bytes-low](../results/policy_validation/obstruction/graphs/control_bytes-low.png)

### obstruction: control_bytes-medium

![control_bytes-medium](../results/policy_validation/obstruction/graphs/control_bytes-medium.png)

### obstruction: control_bytes-high

![control_bytes-high](../results/policy_validation/obstruction/graphs/control_bytes-high.png)

### obstruction: route_changes-low

![route_changes-low](../results/policy_validation/obstruction/graphs/route_changes-low.png)

### obstruction: route_changes-medium

![route_changes-medium](../results/policy_validation/obstruction/graphs/route_changes-medium.png)

### obstruction: route_changes-high

![route_changes-high](../results/policy_validation/obstruction/graphs/route_changes-high.png)

### obstruction: route_reviews-low

![route_reviews-low](../results/policy_validation/obstruction/graphs/route_reviews-low.png)

### obstruction: route_reviews-medium

![route_reviews-medium](../results/policy_validation/obstruction/graphs/route_reviews-medium.png)

### obstruction: route_reviews-high

![route_reviews-high](../results/policy_validation/obstruction/graphs/route_reviews-high.png)

### obstruction: fallback_triggered-low

![fallback_triggered-low](../results/policy_validation/obstruction/graphs/fallback_triggered-low.png)

### obstruction: fallback_triggered-medium

![fallback_triggered-medium](../results/policy_validation/obstruction/graphs/fallback_triggered-medium.png)

### obstruction: fallback_triggered-high

![fallback_triggered-high](../results/policy_validation/obstruction/graphs/fallback_triggered-high.png)

### obstruction: fallback_decision_ms-low

![fallback_decision_ms-low](../results/policy_validation/obstruction/graphs/fallback_decision_ms-low.png)

### obstruction: fallback_decision_ms-medium

![fallback_decision_ms-medium](../results/policy_validation/obstruction/graphs/fallback_decision_ms-medium.png)

### obstruction: fallback_decision_ms-high

![fallback_decision_ms-high](../results/policy_validation/obstruction/graphs/fallback_decision_ms-high.png)

### obstruction: ev_delay_vs_freeflow_s-low

![ev_delay_vs_freeflow_s-low](../results/policy_validation/obstruction/graphs/ev_delay_vs_freeflow_s-low.png)

### obstruction: ev_delay_vs_freeflow_s-medium

![ev_delay_vs_freeflow_s-medium](../results/policy_validation/obstruction/graphs/ev_delay_vs_freeflow_s-medium.png)

### obstruction: ev_delay_vs_freeflow_s-high

![ev_delay_vs_freeflow_s-high](../results/policy_validation/obstruction/graphs/ev_delay_vs_freeflow_s-high.png)

### obstruction: ev_distance_m-low

![ev_distance_m-low](../results/policy_validation/obstruction/graphs/ev_distance_m-low.png)

### obstruction: ev_distance_m-medium

![ev_distance_m-medium](../results/policy_validation/obstruction/graphs/ev_distance_m-medium.png)

### obstruction: ev_distance_m-high

![ev_distance_m-high](../results/policy_validation/obstruction/graphs/ev_distance_m-high.png)

### obstruction: ev_travel_s-low

![ev_travel_s-low](../results/policy_validation/obstruction/graphs/ev_travel_s-low.png)

### obstruction: ev_travel_s-medium

![ev_travel_s-medium](../results/policy_validation/obstruction/graphs/ev_travel_s-medium.png)

### obstruction: ev_travel_s-high

![ev_travel_s-high](../results/policy_validation/obstruction/graphs/ev_travel_s-high.png)

### obstruction: ev_full_stops-low

![ev_full_stops-low](../results/policy_validation/obstruction/graphs/ev_full_stops-low.png)

### obstruction: ev_full_stops-medium

![ev_full_stops-medium](../results/policy_validation/obstruction/graphs/ev_full_stops-medium.png)

### obstruction: ev_full_stops-high

![ev_full_stops-high](../results/policy_validation/obstruction/graphs/ev_full_stops-high.png)

### obstruction: ev_below_1_s-low

![ev_below_1_s-low](../results/policy_validation/obstruction/graphs/ev_below_1_s-low.png)

### obstruction: ev_below_1_s-medium

![ev_below_1_s-medium](../results/policy_validation/obstruction/graphs/ev_below_1_s-medium.png)

### obstruction: ev_below_1_s-high

![ev_below_1_s-high](../results/policy_validation/obstruction/graphs/ev_below_1_s-high.png)

### obstruction: ev_whole_stopped_s-low

![ev_whole_stopped_s-low](../results/policy_validation/obstruction/graphs/ev_whole_stopped_s-low.png)

### obstruction: ev_whole_stopped_s-medium

![ev_whole_stopped_s-medium](../results/policy_validation/obstruction/graphs/ev_whole_stopped_s-medium.png)

### obstruction: ev_whole_stopped_s-high

![ev_whole_stopped_s-high](../results/policy_validation/obstruction/graphs/ev_whole_stopped_s-high.png)

### obstruction: ev_green_fraction-low

![ev_green_fraction-low](../results/policy_validation/obstruction/graphs/ev_green_fraction-low.png)

### obstruction: ev_green_fraction-medium

![ev_green_fraction-medium](../results/policy_validation/obstruction/graphs/ev_green_fraction-medium.png)

### obstruction: ev_green_fraction-high

![ev_green_fraction-high](../results/policy_validation/obstruction/graphs/ev_green_fraction-high.png)

### obstruction: ev_green_count-low

![ev_green_count-low](../results/policy_validation/obstruction/graphs/ev_green_count-low.png)

### obstruction: ev_green_count-medium

![ev_green_count-medium](../results/policy_validation/obstruction/graphs/ev_green_count-medium.png)

### obstruction: ev_green_count-high

![ev_green_count-high](../results/policy_validation/obstruction/graphs/ev_green_count-high.png)

### obstruction: ev_green_approach_fraction-low

![ev_green_approach_fraction-low](../results/policy_validation/obstruction/graphs/ev_green_approach_fraction-low.png)

### obstruction: ev_green_approach_fraction-medium

![ev_green_approach_fraction-medium](../results/policy_validation/obstruction/graphs/ev_green_approach_fraction-medium.png)

### obstruction: ev_green_approach_fraction-high

![ev_green_approach_fraction-high](../results/policy_validation/obstruction/graphs/ev_green_approach_fraction-high.png)

### obstruction: background_time_loss_s-low

![background_time_loss_s-low](../results/policy_validation/obstruction/graphs/background_time_loss_s-low.png)

### obstruction: background_time_loss_s-medium

![background_time_loss_s-medium](../results/policy_validation/obstruction/graphs/background_time_loss_s-medium.png)

### obstruction: background_time_loss_s-high

![background_time_loss_s-high](../results/policy_validation/obstruction/graphs/background_time_loss_s-high.png)

### obstruction: ev_mean_speed_mps-low

![ev_mean_speed_mps-low](../results/policy_validation/obstruction/graphs/ev_mean_speed_mps-low.png)

### obstruction: ev_mean_speed_mps-medium

![ev_mean_speed_mps-medium](../results/policy_validation/obstruction/graphs/ev_mean_speed_mps-medium.png)

### obstruction: ev_mean_speed_mps-high

![ev_mean_speed_mps-high](../results/policy_validation/obstruction/graphs/ev_mean_speed_mps-high.png)

