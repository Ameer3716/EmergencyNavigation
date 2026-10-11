# Completed pilot results after cancellation

The experiment was cancelled on 11 October 2026. This update includes 109 fully completed held-out pilot runs only. Eleven unfinished or unstarted runs are excluded from every table, CSV and graph. The reported seeds 1 to 30 were never launched. These pilot observations do not replace the preserved matched ordinary and fixed-obstruction results.

The first pilot used a 360 second departure window. All 60 runs completed. The stronger-demand pilot used a 120 second window; 49 of 60 runs completed. Partial cells can have biased completion patterns, so comparisons are descriptive pilot evidence and cannot establish general performance.

## Coverage

| Window s | Trips | Configuration | Complete | Scheduled |
| ---: | --- | --- | ---: | ---: |
| 360 | heavy400 | FogCloudAStarAdvance | 10 | 10 |
| 360 | heavy600 | FogCloudAStarAdvance | 10 | 10 |
| 360 | heavy400 | MistDynamicFogFallback | 10 | 10 |
| 360 | heavy600 | MistDynamicFogFallback | 10 | 10 |
| 360 | heavy400 | FogCloudDynamicAdvance | 10 | 10 |
| 360 | heavy600 | FogCloudDynamicAdvance | 10 | 10 |
| 120 | heavy400 | FogCloudAStarAdvance | 10 | 10 |
| 120 | heavy600 | FogCloudAStarAdvance | 10 | 10 |
| 120 | heavy400 | MistDynamicFogFallback | 10 | 10 |
| 120 | heavy600 | MistDynamicFogFallback | 9 | 10 |
| 120 | heavy400 | FogCloudDynamicAdvance | 10 | 10 |
| 120 | heavy600 | FogCloudDynamicAdvance | 0 | 10 |

## Completed matched pilot measurements

Baseline is FogCloudAStarAdvance; proposed is MistDynamicFogFallback. Both use the same advance signal requests. Intervals are paired proposed minus baseline bootstrap 95% intervals. Counts disclose available completed pairs; no partial run is assigned a result.

| Window s | Trips | Requirement and metric | Baseline | Proposed | Change % | Paired difference 95% CI | Pairs |
| ---: | --- | --- | ---: | ---: | ---: | --- | ---: |
| 360 | heavy400 | B response s | 148.250 | 175.350 | 18.280 | [-1.000, 81.650] | 10 |
| 360 | heavy400 | A decision ms | 626.541 | 325.800 | -48.000 | [-301.142, -300.539] | 10 |
| 360 | heavy400 | D signal waiting s | 0.000 | 1.050 | undefined | [0.000, 3.150] | 10 |
| 360 | heavy400 | C full stops | 1.000 | 1.300 | 30.000 | [0.000, 0.900] | 10 |
| 360 | heavy400 | C green approach share | 1.000 | 0.993 | -0.667 | [-0.020, 0.000] | 10 |
| 360 | heavy400 | C background loss s | 114.243 | 110.901 | -2.926 | [-6.115, -0.434] | 10 |
| 360 | heavy600 | B response s | 150.000 | 190.950 | 27.300 | [12.899, 84.350] | 10 |
| 360 | heavy600 | A decision ms | 626.540 | 325.600 | -48.032 | [-301.539, -300.538] | 10 |
| 360 | heavy600 | D signal waiting s | 0.000 | 1.850 | undefined | [0.000, 3.900] | 10 |
| 360 | heavy600 | C full stops | 1.000 | 1.700 | 70.000 | [0.200, 1.200] | 10 |
| 360 | heavy600 | C green approach share | 0.980 | 1.000 | 2.041 | [0.000, 0.060] | 10 |
| 360 | heavy600 | C background loss s | 194.287 | 192.906 | -0.711 | [-4.477, 1.872] | 10 |
| 120 | heavy400 | B response s | 209.300 | 235.000 | 12.279 | [-5.450, 56.151] | 10 |
| 120 | heavy400 | A decision ms | 626.541 | 323.600 | -48.351 | [-304.741, -301.740] | 10 |
| 120 | heavy400 | D signal waiting s | 13.150 | 5.750 | -56.274 | [-17.150, 1.050] | 10 |
| 120 | heavy400 | C full stops | 2.700 | 2.600 | -3.704 | [-1.200, 0.900] | 10 |
| 120 | heavy400 | C green approach share | 0.960 | 0.989 | 3.009 | [-0.022, 0.089] | 10 |
| 120 | heavy400 | C background loss s | 177.740 | 176.110 | -0.917 | [-4.794, 1.229] | 10 |
| 120 | heavy600 | B response s | 285.214 | 375.143 | 31.530 | [-35.143, 234.071] | 7 |
| 120 | heavy600 | A decision ms | 626.539 | 316.857 | -49.427 | [-313.109, -305.970] | 7 |
| 120 | heavy600 | D signal waiting s | 4.500 | 11.714 | 160.317 | [-3.000, 23.786] | 7 |
| 120 | heavy600 | C full stops | 4.429 | 3.286 | -25.806 | [-2.714, 0.714] | 7 |
| 120 | heavy600 | C green approach share | 0.886 | 0.983 | 10.979 | [0.000, 0.206] | 7 |
| 120 | heavy600 | C background loss s | 285.934 | 274.870 | -3.869 | [-22.305, -2.175] | 9 |

## Interpretation

The completed first pilot produced queues, but the baseline response rose only from 148.25 s at 400 trips to 150.00 s at 600 trips. The paired increase was 1.75 s, below the predeclared 5 s congestion qualification. Stronger demand was therefore piloted, but that matrix was cancelled before completion. No final congestion qualification or reported-sample A to D verdict is claimed.

Dynamic Fog uses real network requests. Existing Mist periodic reviews compute synchronously without scheduling another initial processing delay; the ablation is not a hardware CPU benchmark. The 900 ms stalls remain labelled controlled fault injection. Zero waiting is retained when measured. Mean speed is correlated with journey time; background loss is not a pure causal measure of preemption harm.

Primary metrics are PDR, NRL, EM throughput, EM end-to-end delay, route decision latency, EV response and signal waiting. Completed-run secondary metrics and ablations are retained in summary.csv and paired_comparisons.csv. No existing historical result was replaced.

## Graphs

### pilot_120 background_time_loss_s-heavy400

![background_time_loss_s-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/background_time_loss_s-heavy400.png)

### pilot_120 background_time_loss_s-heavy600

![background_time_loss_s-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/background_time_loss_s-heavy600.png)

### pilot_120 control_bytes-heavy400

![control_bytes-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/control_bytes-heavy400.png)

### pilot_120 control_bytes-heavy600

![control_bytes-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/control_bytes-heavy600.png)

### pilot_120 control_transmissions-heavy400

![control_transmissions-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/control_transmissions-heavy400.png)

### pilot_120 control_transmissions-heavy600

![control_transmissions-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/control_transmissions-heavy600.png)

### pilot_120 e2e_delay_ms-heavy400

![e2e_delay_ms-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/e2e_delay_ms-heavy400.png)

### pilot_120 e2e_delay_ms-heavy600

![e2e_delay_ms-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/e2e_delay_ms-heavy600.png)

### pilot_120 ev_below_1_s-heavy400

![ev_below_1_s-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_below_1_s-heavy400.png)

### pilot_120 ev_below_1_s-heavy600

![ev_below_1_s-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_below_1_s-heavy600.png)

### pilot_120 ev_delay_vs_freeflow_s-heavy400

![ev_delay_vs_freeflow_s-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_delay_vs_freeflow_s-heavy400.png)

### pilot_120 ev_delay_vs_freeflow_s-heavy600

![ev_delay_vs_freeflow_s-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_delay_vs_freeflow_s-heavy600.png)

### pilot_120 ev_distance_m-heavy400

![ev_distance_m-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_distance_m-heavy400.png)

### pilot_120 ev_distance_m-heavy600

![ev_distance_m-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_distance_m-heavy600.png)

### pilot_120 ev_full_stops-heavy400

![ev_full_stops-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_full_stops-heavy400.png)

### pilot_120 ev_full_stops-heavy600

![ev_full_stops-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_full_stops-heavy600.png)

### pilot_120 ev_green_approach_fraction-heavy400

![ev_green_approach_fraction-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_green_approach_fraction-heavy400.png)

### pilot_120 ev_green_approach_fraction-heavy600

![ev_green_approach_fraction-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_green_approach_fraction-heavy600.png)

### pilot_120 ev_green_count-heavy400

![ev_green_count-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_green_count-heavy400.png)

### pilot_120 ev_green_count-heavy600

![ev_green_count-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_green_count-heavy600.png)

### pilot_120 ev_green_fraction-heavy400

![ev_green_fraction-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_green_fraction-heavy400.png)

### pilot_120 ev_green_fraction-heavy600

![ev_green_fraction-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_green_fraction-heavy600.png)

### pilot_120 ev_mean_speed_mps-heavy400

![ev_mean_speed_mps-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_mean_speed_mps-heavy400.png)

### pilot_120 ev_mean_speed_mps-heavy600

![ev_mean_speed_mps-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_mean_speed_mps-heavy600.png)

### pilot_120 ev_response_s-heavy400

![ev_response_s-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_response_s-heavy400.png)

### pilot_120 ev_response_s-heavy600

![ev_response_s-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_response_s-heavy600.png)

### pilot_120 ev_travel_s-heavy400

![ev_travel_s-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_travel_s-heavy400.png)

### pilot_120 ev_travel_s-heavy600

![ev_travel_s-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_travel_s-heavy600.png)

### pilot_120 ev_whole_stopped_s-heavy400

![ev_whole_stopped_s-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/ev_whole_stopped_s-heavy400.png)

### pilot_120 ev_whole_stopped_s-heavy600

![ev_whole_stopped_s-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/ev_whole_stopped_s-heavy600.png)

### pilot_120 fallback_triggered-heavy400

![fallback_triggered-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/fallback_triggered-heavy400.png)

### pilot_120 fallback_triggered-heavy600

![fallback_triggered-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/fallback_triggered-heavy600.png)

### pilot_120 fog_completed_reviews-heavy400

![fog_completed_reviews-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/fog_completed_reviews-heavy400.png)

### pilot_120 fog_requests-heavy400

![fog_requests-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/fog_requests-heavy400.png)

### pilot_120 fog_requests-heavy600

![fog_requests-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/fog_requests-heavy600.png)

### pilot_120 fog_unanswered_reviews-heavy400

![fog_unanswered_reviews-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/fog_unanswered_reviews-heavy400.png)

### pilot_120 nrl-heavy400

![nrl-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/nrl-heavy400.png)

### pilot_120 nrl-heavy600

![nrl-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/nrl-heavy600.png)

### pilot_120 pdr-heavy400

![pdr-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/pdr-heavy400.png)

### pilot_120 pdr-heavy600

![pdr-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/pdr-heavy600.png)

### pilot_120 route_changes-heavy400

![route_changes-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/route_changes-heavy400.png)

### pilot_120 route_changes-heavy600

![route_changes-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/route_changes-heavy600.png)

### pilot_120 route_decision_ms-heavy400

![route_decision_ms-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/route_decision_ms-heavy400.png)

### pilot_120 route_decision_ms-heavy600

![route_decision_ms-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/route_decision_ms-heavy600.png)

### pilot_120 route_reviews-heavy400

![route_reviews-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/route_reviews-heavy400.png)

### pilot_120 route_reviews-heavy600

![route_reviews-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/route_reviews-heavy600.png)

### pilot_120 throughput_bps-heavy400

![throughput_bps-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/throughput_bps-heavy400.png)

### pilot_120 throughput_bps-heavy600

![throughput_bps-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/throughput_bps-heavy600.png)

### pilot_120 traffic_light_wait_s-heavy400

![traffic_light_wait_s-heavy400](../results/next_validation/completed_pilots/pilot_120/graphs/traffic_light_wait_s-heavy400.png)

### pilot_120 traffic_light_wait_s-heavy600

![traffic_light_wait_s-heavy600](../results/next_validation/completed_pilots/pilot_120/graphs/traffic_light_wait_s-heavy600.png)

### pilot_360 background_time_loss_s-heavy400

![background_time_loss_s-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/background_time_loss_s-heavy400.png)

### pilot_360 background_time_loss_s-heavy600

![background_time_loss_s-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/background_time_loss_s-heavy600.png)

### pilot_360 control_bytes-heavy400

![control_bytes-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/control_bytes-heavy400.png)

### pilot_360 control_bytes-heavy600

![control_bytes-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/control_bytes-heavy600.png)

### pilot_360 control_transmissions-heavy400

![control_transmissions-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/control_transmissions-heavy400.png)

### pilot_360 control_transmissions-heavy600

![control_transmissions-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/control_transmissions-heavy600.png)

### pilot_360 e2e_delay_ms-heavy400

![e2e_delay_ms-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/e2e_delay_ms-heavy400.png)

### pilot_360 e2e_delay_ms-heavy600

![e2e_delay_ms-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/e2e_delay_ms-heavy600.png)

### pilot_360 ev_below_1_s-heavy400

![ev_below_1_s-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_below_1_s-heavy400.png)

### pilot_360 ev_below_1_s-heavy600

![ev_below_1_s-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_below_1_s-heavy600.png)

### pilot_360 ev_delay_vs_freeflow_s-heavy400

![ev_delay_vs_freeflow_s-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_delay_vs_freeflow_s-heavy400.png)

### pilot_360 ev_delay_vs_freeflow_s-heavy600

![ev_delay_vs_freeflow_s-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_delay_vs_freeflow_s-heavy600.png)

### pilot_360 ev_distance_m-heavy400

![ev_distance_m-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_distance_m-heavy400.png)

### pilot_360 ev_distance_m-heavy600

![ev_distance_m-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_distance_m-heavy600.png)

### pilot_360 ev_full_stops-heavy400

![ev_full_stops-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_full_stops-heavy400.png)

### pilot_360 ev_full_stops-heavy600

![ev_full_stops-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_full_stops-heavy600.png)

### pilot_360 ev_green_approach_fraction-heavy400

![ev_green_approach_fraction-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_green_approach_fraction-heavy400.png)

### pilot_360 ev_green_approach_fraction-heavy600

![ev_green_approach_fraction-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_green_approach_fraction-heavy600.png)

### pilot_360 ev_green_count-heavy400

![ev_green_count-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_green_count-heavy400.png)

### pilot_360 ev_green_count-heavy600

![ev_green_count-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_green_count-heavy600.png)

### pilot_360 ev_green_fraction-heavy400

![ev_green_fraction-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_green_fraction-heavy400.png)

### pilot_360 ev_green_fraction-heavy600

![ev_green_fraction-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_green_fraction-heavy600.png)

### pilot_360 ev_mean_speed_mps-heavy400

![ev_mean_speed_mps-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_mean_speed_mps-heavy400.png)

### pilot_360 ev_mean_speed_mps-heavy600

![ev_mean_speed_mps-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_mean_speed_mps-heavy600.png)

### pilot_360 ev_response_s-heavy400

![ev_response_s-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_response_s-heavy400.png)

### pilot_360 ev_response_s-heavy600

![ev_response_s-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_response_s-heavy600.png)

### pilot_360 ev_travel_s-heavy400

![ev_travel_s-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_travel_s-heavy400.png)

### pilot_360 ev_travel_s-heavy600

![ev_travel_s-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_travel_s-heavy600.png)

### pilot_360 ev_whole_stopped_s-heavy400

![ev_whole_stopped_s-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/ev_whole_stopped_s-heavy400.png)

### pilot_360 ev_whole_stopped_s-heavy600

![ev_whole_stopped_s-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/ev_whole_stopped_s-heavy600.png)

### pilot_360 fallback_triggered-heavy400

![fallback_triggered-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/fallback_triggered-heavy400.png)

### pilot_360 fallback_triggered-heavy600

![fallback_triggered-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/fallback_triggered-heavy600.png)

### pilot_360 fog_completed_reviews-heavy400

![fog_completed_reviews-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/fog_completed_reviews-heavy400.png)

### pilot_360 fog_completed_reviews-heavy600

![fog_completed_reviews-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/fog_completed_reviews-heavy600.png)

### pilot_360 fog_requests-heavy400

![fog_requests-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/fog_requests-heavy400.png)

### pilot_360 fog_requests-heavy600

![fog_requests-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/fog_requests-heavy600.png)

### pilot_360 fog_unanswered_reviews-heavy400

![fog_unanswered_reviews-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/fog_unanswered_reviews-heavy400.png)

### pilot_360 fog_unanswered_reviews-heavy600

![fog_unanswered_reviews-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/fog_unanswered_reviews-heavy600.png)

### pilot_360 nrl-heavy400

![nrl-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/nrl-heavy400.png)

### pilot_360 nrl-heavy600

![nrl-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/nrl-heavy600.png)

### pilot_360 pdr-heavy400

![pdr-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/pdr-heavy400.png)

### pilot_360 pdr-heavy600

![pdr-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/pdr-heavy600.png)

### pilot_360 route_changes-heavy400

![route_changes-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/route_changes-heavy400.png)

### pilot_360 route_changes-heavy600

![route_changes-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/route_changes-heavy600.png)

### pilot_360 route_decision_ms-heavy400

![route_decision_ms-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/route_decision_ms-heavy400.png)

### pilot_360 route_decision_ms-heavy600

![route_decision_ms-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/route_decision_ms-heavy600.png)

### pilot_360 route_reviews-heavy400

![route_reviews-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/route_reviews-heavy400.png)

### pilot_360 route_reviews-heavy600

![route_reviews-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/route_reviews-heavy600.png)

### pilot_360 throughput_bps-heavy400

![throughput_bps-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/throughput_bps-heavy400.png)

### pilot_360 throughput_bps-heavy600

![throughput_bps-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/throughput_bps-heavy600.png)

### pilot_360 traffic_light_wait_s-heavy400

![traffic_light_wait_s-heavy400](../results/next_validation/completed_pilots/pilot_360/graphs/traffic_light_wait_s-heavy400.png)

### pilot_360 traffic_light_wait_s-heavy600

![traffic_light_wait_s-heavy600](../results/next_validation/completed_pilots/pilot_360/graphs/traffic_light_wait_s-heavy600.png)
