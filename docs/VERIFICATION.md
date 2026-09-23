# Verification report

Verified on 2026-09-21 using OMNeT++ 6.3.0, Veins 5.3.1, SUMO 1.18.0, and 30 matched seeds across all five comparison configurations (`FogCloudAStar`, `MistAStar`, `MistDynamicAStar`, `MistDynamicFogFallback`, and `NoPreemptionBaseline`), totaling 450 simulation runs. All 23 functional verification checks pass with complete evidence in `artifacts/logs/batch/`, `results/raw/`, and `results/processed/`.

## 1. Functional Verification Matrix (23 Checks)

| # | Test | Result and evidence |
| --- | --- | --- |
| 1 | SUMO network loads | Passed: SUMO-only validation for all three seed-1 densities, `sumo-validation.json`. |
| 2 | Veins connects with SUMO | Passed: stock example and custom launcher logs on port 9998 (`grid-launchd.log`). |
| 3 | Vehicles appear and move | Passed: SUMO FCD and OMNeT++ TraCI mobility logs (`mobility-*.csv`). |
| 4 | Direct RSU → EV EM | Passed: `emergency-DirectDelivery.csv`, hop count 0, direct V2I transmission. |
| 5 | Vehicle multihop EM | Passed: `emergency-VehicleRelay.csv`, hop count 2, intermediate vehicle relay. |
| 6 | RSU multihop EM | Passed: `emergency-RsuRelay.csv`, hop count 1, intermediate infrastructure relay. |
| 7 | Duplicate suppression | Passed: 283 duplicate discarded rows logged with 60 s cache window. |
| 8 | TTL termination | Passed: TTL=1 run has one source transmission, seven expiration rows, zero EV delivery. |
| 9 | Static A* connected route | Passed: independent C++ routing test and applied turn-valid SUMO route. |
| 10 | Dynamic A* route change | Passed: `CongestionReroute` and high-density seed 4 alternate routes applied successfully. |
| 11 | Mist meets watchdog | Passed: normal mist decision completes in ~0.326 s, well below 800 ms watchdog. |
| 12 | Forced mist failure | Passed: `fallback-forced-verified.csv` records immediate exception failover (`fallbackReason = forced_failure`). |
| 13 | Forced mist timeout | Passed: `fallback-timeout-verified.csv` records genuine 800 ms watchdog timeout (`fallbackReason = watchdog_timeout`) and fog takeover applied at t=68.15 s. |
| 14 | Correct TL phase changes | Passed: `traffic-light-*.csv` records requested incoming edge and green state across all corridor junctions. |
| 15 | Safe transition phases | Passed: actual SUMO phase transitions confirm yellow (2.0 s) followed by all-red (1.0 s) before green. |
| 16 | Original program restored | Passed: all preemption events log `program_restored` after EV departure or 25 s maximum hold. |
| 17 | EV reaches accident | Passed: all delivering runs record `accidentArrivalConfirmed = 1` in `.sca` scalars. |
| 18 | Result/log files generated | Passed: 450 nonempty `.sca`, `.vec`, `.vci` files and CSV event logs generated. |
| 19 | Metric formulas | Passed: `validate_integrated.py` and `audit_batch.py` recompute PDR, E2E delay, NRL, throughput, and response time from raw rows/scalars. All 425 delivered response times verified against raw `.sca` files (0 mismatches), and 25 network-partition runs correctly classified as not applicable (`artifacts/response_time_verification.csv`). |
| 20 | TraCI TLS wiring & preemption | Passed: `MetricsCollector` wired to TraCI `VAR_NEXT_TLS (0x70)`. Preemption requests at 250 m turn signals green ~15 s prior to arrival (+15.208 s margin at B1 for FogCloud high seed 1). |
| 21 | Network partition analysis | Passed: Genuine IEEE 802.11p network partitions verified from raw logs: low traffic (seeds 12, 28; PDR = 93.33%, Wilson [0.787, 0.982]), medium traffic (seed 21; PDR = 96.67%, Wilson [0.833, 0.994]), high traffic (seeds 13, 21; PDR = 93.33%, Wilson [0.787, 0.982]). |
| 22 | Balanced batch matrix | Passed: exactly 450 runs across five configurations (30 low, 30 medium, 30 high seeds each). Programmatically verified by `scripts/audit_batch.py`. |
| 23 | No-preemption baseline control | Passed: `NoPreemptionBaseline` (FogCloud routing without preemption) evaluated across all 30 seeds per density (150 total baseline runs). Without preemption, EV halts at red lights, logging 27.5–31.3 s waiting time. |

---

## 2. Multi-Density Batch Experiment Results (450 Runs across 5 Configurations)

Evaluated across 30 matched random seeds (seeds 1–30) per density per configuration. PDR incorporates all $N=30$ generated runs using bounded binomial Wilson 95% confidence intervals. Downstream mobility metrics are reported conditionally on successful delivery ($n=28$ low, $n=29$ medium, $n=28$ high). Waiting time and corridor delay vs. free-flow use non-parametric bootstrap percentile 95% confidence intervals (10,000 resamples, fixed seed 42) to respect their non-negative zero-inflated distributions:

| Traffic Density | Configuration | Total Runs | PDR (Mean ± SD) | Wilson 95% CI | Response Runs ($n$) | Mean Response Time (s) | StdDev (s) | 95% Confidence Interval | TL Wait $\le$20m (s) | Corridor Delay vs Free-Flow (s) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **High** | FogCloudAStar | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 142.59 | 2.61 | [141.62, 143.56] | 0.00 ± 0.00 | 1.09 ± 2.61 |
| **High** | MistAStar | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 142.18 | 2.78 | [141.15, 143.21] | 0.00 ± 0.00 | 1.18 ± 2.78 |
| **High** | MistDynamicAStar | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 142.86 | 9.06 | [139.50, 146.21] | 0.00 ± 0.00 | 2.39 ± 8.85 |
| **High** | MistDynamicFogFallback | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 142.86 | 9.06 | [139.50, 146.21] | 0.00 ± 0.00 | 2.39 ± 8.85 |
| **High** | **NoPreemptionBaseline** | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | **197.07** | **24.68** | **[187.93, 206.21]** | **27.48 ± 14.92** | **55.57 ± 24.68** |
| **Medium** | FogCloudAStar | 30 | 0.967 ± 0.183 | [0.833, 0.994] | 29 | 142.29 | 4.18 | [140.77, 143.81] | 0.59 ± 3.16 | 0.79 ± 4.18 |
| **Medium** | MistAStar | 30 | 0.967 ± 0.183 | [0.833, 0.994] | 29 | 141.03 | 0.13 | [140.99, 141.08] | 0.00 ± 0.00 | 0.03 ± 0.13 |
| **Medium** | MistDynamicAStar | 30 | 0.967 ± 0.183 | [0.833, 0.994] | 29 | 140.90 | 0.69 | [140.65, 141.15] | 0.00 ± 0.00 | 0.07 ± 0.18 |
| **Medium** | MistDynamicFogFallback | 30 | 0.967 ± 0.183 | [0.833, 0.994] | 29 | 140.90 | 0.69 | [140.65, 141.15] | 0.00 ± 0.00 | 0.07 ± 0.18 |
| **Medium** | **NoPreemptionBaseline** | 30 | 0.967 ± 0.183 | [0.833, 0.994] | 29 | **192.74** | **17.25** | **[186.46, 199.02]** | **29.97 ± 14.99** | **51.24 ± 17.25** |
| **Low** | FogCloudAStar | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 141.64 | 0.53 | [141.45, 141.84] | 0.00 ± 0.00 | 0.14 ± 0.53 |
| **Low** | MistAStar | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 141.18 | 0.66 | [140.94, 141.42] | 0.00 ± 0.00 | 0.18 ± 0.66 |
| **Low** | MistDynamicAStar | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 141.23 | 0.66 | [140.99, 141.48] | 0.00 ± 0.00 | 0.23 ± 0.66 |
| **Low** | MistDynamicFogFallback | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | 141.23 | 0.66 | [140.99, 141.48] | 0.00 ± 0.00 | 0.23 ± 0.66 |
| **Low** | **NoPreemptionBaseline** | 30 | 0.933 ± 0.254 | [0.787, 0.982] | 28 | **186.63** | **2.70** | **[185.62, 187.63]** | **31.30 ± 6.21** | **45.13 ± 2.70** |

### Event Timeline & Kinematic Range Provenance
Analysis of raw OMNeT++ scalars across all 425 delivered simulation runs establishes the complete empirical event timeline:
* **Incident Trigger**: Injected at $t = 60.0\text{ s}$ on link D3C3.
* **Kinematic Deceleration & Standstill**: The disabled vehicle halts; RSU 2 monitors speed until standstill ($v < 0.1\text{ m/s}$) is confirmed.
* **Accident Detection & EM Generation**: $t_{\text{gen}} \in [65.5, 68.0]\text{ s}$ across all 450 runs (including partitioned runs).
* **EV Receipt**: $t_{\text{receive}} \in [65.5138, 68.0193]\text{ s}$.
* **EV Departure**: $t_{\text{departure}} \in [66.5, 69.5]\text{ s}$ (recorded in raw `.sca` `evDepartureTime` after initial route application).
* **EV Arrival**:
  * Active preemption configurations (340 delivered runs): $t_{\text{arrival}} \in [204.0, 254.0]\text{ s}$ (response time 138.5–187.5 s).
  * No-preemption baseline (85 delivered runs): $t_{\text{arrival}} \in [250.0, 349.5]\text{ s}$ (response time 182.5–284.0 s).
  * All delivered runs combined: $t_{\text{arrival}} \in [204.0, 349.5]\text{ s}$ (response time 138.5–284.0 s).
Complete per-run timeline records are verified in [`artifacts/event_timeline_verification.csv`](file:///d:/Codex/EmergencyNavigation/artifacts/event_timeline_verification.csv).

---

## 3. Key Findings & Empirical Analysis

1. **Mist Routing Latency Advantage**: On static shortest paths, `MistAStar` consistently reduces EV response time by 0.41–1.26 s compared to `FogCloudAStar` (low-density paired difference: $-0.3005\text{ s}$ decision latency, $t = -525596, df = 27, p = 1.1 \times 10^{-136}$, Cohen's $d_z = -99328$), reflecting elimination of wireless transmission and WAN backhaul delays (0.326 s vs 0.627 s). Note that the large $t$ and $d_z$ arise from almost deterministic configured computation delays with very low run-to-run variance ($s_D \approx 3.0 \times 10^{-6}\text{ s}$); the primary finding is the verified 0.3005 s latency savings.
2. **Dynamic A* Performance and Variance**: In medium traffic, `MistDynamicAStar` delivers an average response time of **140.90 s**, outperforming static MistAStar (141.03 s) and FogCloud (142.29 s). In high traffic, Dynamic A* exhibits higher variance (stddev 9.06 s, mean 142.86 s). Detailed auditing of high-density seed 22 shows that Dynamic A* detected 3 queued vehicles at red signal link B2C2, triggering an alternate detour that added 600 m of distance and 45 s of travel time. This demonstrates that preemption-oblivious dynamic routing can suffer from queue detours in heavy traffic.
3. **Traffic Light Preemption Waiting Time Reduction**:
   * **Low Traffic**: Preemption achieves a **100.0% reduction** in waiting time (0.00 s vs. 31.30 s, paired diff $-31.30\text{ s}, t = -26.67, df = 27, p = 6.2 \times 10^{-21}$, Cohen's $d_z = -5.04$) and saves **44.98 s** in total response time ($t = -91.74, df = 27, p = 3.1 \times 10^{-35}$, $d_z = -17.34$).
   * **Medium Traffic**: Preemption achieves a **98.04% reduction** in waiting time (0.59 s vs. 29.97 s, paired diff $-29.38\text{ s}, t = -10.26, df = 28, p = 5.4 \times 10^{-11}$, Cohen's $d_z = -1.91$) and saves **50.45 s** in total response time ($t = -15.07, df = 28, p = 5.8 \times 10^{-15}$, $d_z = -2.80$). Detailed investigation reveals that in seed 14, an IEEE 802.11p wireless packet loss prevented the C2 preemption request from reaching RSU 1, causing an isolated 17.0 s wait that explains the non-zero medium-density average.
   * **High Traffic**: Preemption achieves a **100.0% reduction** in waiting time (0.00 s vs. 27.48 s, paired diff $-27.48\text{ s}, t = -9.75, df = 27, p = 2.5 \times 10^{-10}$, Cohen's $d_z = -1.84$) and saves **54.48 s** in total response time ($t = -11.49, df = 27, p = 6.7 \times 10^{-12}$, $d_z = -2.17$).
4. **Visual Evidence Deliverables**:
   * `artifacts/screenshots/software-versions-terminal.png`: OMNeT++ 6.3.0, SUMO 1.18.0, Veins 5.3.1 toolchain audit.
   * `artifacts/screenshots/stock-veins-run-terminal.png`: Stock Veins simulation run to t=200 s with exit code 0.
   * `artifacts/screenshots/direct-em-delivery-event.png`: Direct RSU-to-EV (V2I) emergency message delivery event trace.
   * `artifacts/screenshots/multihop-em-delivery-events.png`: Multi-hop vehicle and RSU relay forwarding event chain showing both receive and transmit events chronologically.
   * `artifacts/screenshots/dynamic-rerouting-trace.png`: Log-derived route schematic of autonomous dynamic A* congestion avoidance (High Seed 4).
   * `artifacts/screenshots/traffic-light-preemption-phase.png`: Preemption phase transition sequence at Intersection B1 (+15.208 s arrival margin, verified against `traffic-light-FogCloudAStar-high-seed1.csv`).
   * `artifacts/screenshots/forced-mist-fallback-trace.png`: Two-panel log-derived event transcript demonstrating Panel A (Immediate Failure-Triggered Fallback, `ForcedMistFailure`) and Panel B (800 ms Watchdog Timeout Fallback, `ForcedMistTimeout`).
   * `artifacts/screenshots/final-ev-response-graph.png`: 3-panel comparison chart displaying all 5 configurations across Low, Medium, and High densities with 95% confidence intervals.
