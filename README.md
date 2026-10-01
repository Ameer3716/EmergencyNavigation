# Emergency vehicle navigation simulation

This repository couples SUMO 1.18.0 and OMNeT++ 6.3.0 / Veins 5.3.1 to compare four emergency vehicle route architectures on a 4 by 4 signalized grid. The reviewed study uses a 400 m radio neighborhood and 360 matched runs (4 configurations × 3 traffic densities × 30 seeds). The historical 650 m data is in `archive_raw_20261001_650m/` and is excluded from current comparisons.

## Configurations

| Configuration | Route computation | Periodic review | Fallback |
| --- | --- | --- | --- |
| FogCloudAStar | Fog and cloud static A* | No | No |
| MistAStar | Local static A* | No | No |
| MistDynamicAStar | Local dynamic A* | Every 5 s | No |
| MistDynamicFogFallback | Local dynamic A* | Every 5 s | 800 ms Fog takeover |

All four use V2I signal preemption. Diagnostic forced-failure and forced-timeout configurations remain outside the comparison.

## Results and reproduction

The preferred outcomes are PDR, NRL, EM throughput, EM end-to-end delay (ms), route decision latency (ms), EV response time (s), and EV traffic-light waiting time (s). Supplemental routing and fallback measures are reported separately. `docs/VERIFICATION.md` has the current result tables, `docs/METHODOLOGY.md` has formulas and modeling assumptions, and `docs/INSTALLATION.md` has commands to rebuild, rerun, process, and audit. The source CSVs are in `results/processed/`, raw simulation evidence is in `results/raw/`, and graphs are in `results/graphs/`.

The [illustrated final report](docs/Emergency_Vehicle_Navigation_Final_Submission.docx) explains the project in plain English and includes all 47 graphs. The [graph guide](docs/PROCESS_AND_GRAPHS.md) shows the same figures directly on GitHub.

EM throughput uses one 256-byte useful payload divided by the fixed 900 s window, so similar delivery rates yield similar plotted throughput despite different vehicle counts and routing costs. All graphs retain 95% confidence intervals; the actual interval methods are documented in `docs/METHODOLOGY.md`.
