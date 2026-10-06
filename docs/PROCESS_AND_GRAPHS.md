# Emergency vehicle navigation: project and graph guide

This project studies how an emergency vehicle receives an accident alert and chooses a route through traffic. The Word report contains the complete project explanation and the same 66 graphs.

## How the system works

1. Create a small road network with 16 junctions and traffic lights. Put three roadside units (RSUs) beside the roads. Each RSU can communicate within a 400 m radio neighborhood.

2. Add normal traffic to the roads. The low, medium, and high traffic scenarios contain 72, 144, and 200 background vehicles. Thirty random seeds give different trips for each scenario.

3. Start the emergency event. An accident vehicle stops, and the nearby RSU sends one 256-byte emergency message through the vehicle and roadside network to the emergency vehicle (EV).

4. When the EV receives the message, calculate a route to the accident using the selected routing configuration. Some configurations use a fixed A* route; the dynamic configurations review live road costs every five seconds.

5. While the EV drives under SUMO car-following and signal safety rules, it requests traffic-light priority within 100 m or eight seconds. The controller preserves a minimum ten-second green for traffic already being served, then clears the junction with yellow and all-red before changing priority.

6. Mist normally computes the route with no added telemetry validation delay. Eight independently selected seeds receive a controlled 900 ms Mist stall in all three Mist approaches. In Mist with Fog, unfinished work after 500 ms triggers a Fog request. These are labeled fault tests, not naturally occurring failures.

7. Record whether the message arrived, how long communication and route decisions took, how the EV traveled, and how many reviews, route changes, and fallback events occurred. Each run has a 900 second observation window.

8. Repeat the four primary configurations at three traffic levels and 30 matched seeds: 360 runs. Add 90 no-preemption control runs, displayed only for traffic-light waiting. Calculate averages and 95% confidence intervals, report normal and controlled-stall results separately, and draw the graphs.

## How to read the figures

Each bar is a density and configuration mean. Error bars show 95% confidence intervals; the exact methods are in [METHODOLOGY.md](METHODOLOGY.md). Metrics requiring EM delivery use only valid delivered runs. PDR, EM throughput, and fallback activation use all 30 scheduled runs where applicable. Fallback latency uses only runs where the watchdog actually activated.

## All 66 graphs

### Packet delivery ratio

The share of generated emergency messages that reached the EV. Higher is better.

![Packet delivery ratio for low traffic](../results/graphs/pdr-low.png)

Low traffic (72 background vehicles): Fog/Cloud 0.800; Mist 0.800; Mist Dynamic 0.800; Mist + Fog 0.800. Bars show means and 95% confidence intervals.

![Packet delivery ratio for medium traffic](../results/graphs/pdr-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 0.967; Mist 0.967; Mist Dynamic 0.967; Mist + Fog 0.967. Bars show means and 95% confidence intervals.

![Packet delivery ratio for high traffic](../results/graphs/pdr-high.png)

High traffic (200 background vehicles): Fog/Cloud 1.000; Mist 1.000; Mist Dynamic 1.000; Mist + Fog 1.000. Bars show means and 95% confidence intervals.

### Normalized routing load

Control and EM transmissions per delivered emergency message. Lower means less communication overhead.

![Normalized routing load for low traffic](../results/graphs/nrl-low.png)

Low traffic (72 background vehicles): Fog/Cloud 22,031; Mist 22,030; Mist Dynamic 22,020; Mist + Fog 22,027. Bars show means and 95% confidence intervals.

![Normalized routing load for medium traffic](../results/graphs/nrl-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 39,768; Mist 39,779; Mist Dynamic 39,806; Mist + Fog 39,788. Bars show means and 95% confidence intervals.

![Normalized routing load for high traffic](../results/graphs/nrl-high.png)

High traffic (200 background vehicles): Fog/Cloud 54,430; Mist 54,290; Mist Dynamic 54,333; Mist + Fog 54,276. Bars show means and 95% confidence intervals.

### EM throughput

Delivered EM payload bits divided by the fixed 900 second observation window. One delivery contributes 2.27556 bit/s.

![EM throughput for low traffic](../results/graphs/throughput_bps-low.png)

Low traffic (72 background vehicles): Fog/Cloud 1.820; Mist 1.820; Mist Dynamic 1.820; Mist + Fog 1.820. Bars show means and 95% confidence intervals.

![EM throughput for medium traffic](../results/graphs/throughput_bps-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 2.200; Mist 2.200; Mist Dynamic 2.200; Mist + Fog 2.200. Bars show means and 95% confidence intervals.

![EM throughput for high traffic](../results/graphs/throughput_bps-high.png)

High traffic (200 background vehicles): Fog/Cloud 2.276; Mist 2.276; Mist Dynamic 2.276; Mist + Fog 2.276. Bars show means and 95% confidence intervals.

### EM end-to-end delay

Time from RSU message generation to EV reception, in milliseconds. Lower is faster.

![EM end-to-end delay for low traffic](../results/graphs/e2e_delay_ms-low.png)

Low traffic (72 background vehicles): Fog/Cloud 44.4; Mist 44.4; Mist Dynamic 44.4; Mist + Fog 44.4. Bars show means and 95% confidence intervals.

![EM end-to-end delay for medium traffic](../results/graphs/e2e_delay_ms-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 37.1; Mist 37.1; Mist Dynamic 37.1; Mist + Fog 37.1. Bars show means and 95% confidence intervals.

![EM end-to-end delay for high traffic](../results/graphs/e2e_delay_ms-high.png)

High traffic (200 background vehicles): Fog/Cloud 32.2; Mist 32.2; Mist Dynamic 32.2; Mist + Fog 32.2. Bars show means and 95% confidence intervals.

### Route decision latency

Time from EV message reception to the initial route being applied, in milliseconds.

![Route decision latency for low traffic](../results/graphs/route_decision_ms-low.png)

Low traffic (72 background vehicles): Fog/Cloud 626.5; Mist 588.5; Mist Dynamic 588.5; Mist + Fog 472.0. Bars show means and 95% confidence intervals.

![Route decision latency for medium traffic](../results/graphs/route_decision_ms-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 626.5; Mist 574.3; Mist Dynamic 574.3; Mist + Fog 464.1. Bars show means and 95% confidence intervals.

![Route decision latency for high traffic](../results/graphs/route_decision_ms-high.png)

High traffic (200 background vehicles): Fog/Cloud 626.5; Mist 566.0; Mist Dynamic 566.0; Mist + Fog 459.5. Bars show means and 95% confidence intervals.

### EV response time

Time from emergency message generation until the EV reaches the accident, in seconds.

![EV response time for low traffic](../results/graphs/ev_response_s-low.png)

Low traffic (72 background vehicles): Fog/Cloud 153.3; Mist 153.5; Mist Dynamic 153.0; Mist + Fog 153.0. Bars show means and 95% confidence intervals.

![EV response time for medium traffic](../results/graphs/ev_response_s-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 154.5; Mist 154.7; Mist Dynamic 154.1; Mist + Fog 153.9. Bars show means and 95% confidence intervals.

![EV response time for high traffic](../results/graphs/ev_response_s-high.png)

High traffic (200 background vehicles): Fog/Cloud 156.2; Mist 156.9; Mist Dynamic 154.9; Mist + Fog 154.9. Bars show means and 95% confidence intervals.

### EV traffic-light waiting time

EV standstill near a signal stop line, in seconds. A value of zero means no measured wait.

![EV traffic-light waiting time for low traffic](../results/graphs/traffic_light_wait_s-low.png)

Low traffic (72 background vehicles): Fog/Cloud 1.6; Mist 1.8; Mist Dynamic 2.2; Mist + Fog 2.2; No preemption 26.3. Bars show means and 95% confidence intervals.

![EV traffic-light waiting time for medium traffic](../results/graphs/traffic_light_wait_s-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 0.8; Mist 0.9; Mist Dynamic 1.1; Mist + Fog 1.2; No preemption 27.3. Bars show means and 95% confidence intervals.

![EV traffic-light waiting time for high traffic](../results/graphs/traffic_light_wait_s-high.png)

High traffic (200 background vehicles): Fog/Cloud 0.7; Mist 0.7; Mist Dynamic 0.8; Mist + Fog 0.8; No preemption 22.7. Bars show means and 95% confidence intervals.

### Fallback activation rate

Share of Mist with Fog runs where the 500 ms watchdog requested Fog. Controlled stalls are explicitly injected in eight of the 30 seeds.

![Fallback activation rate for low traffic](../results/graphs/fallback_triggered-low.png)

Low traffic (72 background vehicles): Mist + Fog 0.233. Bars show means and 95% confidence intervals.

![Fallback activation rate for medium traffic](../results/graphs/fallback_triggered-medium.png)

Medium traffic (144 background vehicles): Mist + Fog 0.267. Bars show means and 95% confidence intervals.

![Fallback activation rate for high traffic](../results/graphs/fallback_triggered-high.png)

High traffic (200 background vehicles): Mist + Fog 0.267. Bars show means and 95% confidence intervals.

### Applied route changes

Mean number of actual congestion or cost reroutes per run. Reviews without a replacement are excluded.

![Applied route changes for low traffic](../results/graphs/route_changes-low.png)

Low traffic (72 background vehicles): Mist Dynamic 0.13; Mist + Fog 0.13. Bars show means and 95% confidence intervals.

![Applied route changes for medium traffic](../results/graphs/route_changes-medium.png)

Medium traffic (144 background vehicles): Mist Dynamic 0.27; Mist + Fog 0.30. Bars show means and 95% confidence intervals.

![Applied route changes for high traffic](../results/graphs/route_changes-high.png)

High traffic (200 background vehicles): Mist Dynamic 0.37; Mist + Fog 0.37. Bars show means and 95% confidence intervals.

### Route computation frequency

Mean number of periodic Dynamic A* route evaluations per run, normally scheduled every five seconds.

![Route computation frequency for low traffic](../results/graphs/route_reviews-low.png)

Low traffic (72 background vehicles): Mist Dynamic 22.03; Mist + Fog 22.03. Bars show means and 95% confidence intervals.

![Route computation frequency for medium traffic](../results/graphs/route_reviews-medium.png)

Medium traffic (144 background vehicles): Mist Dynamic 27.20; Mist + Fog 27.10. Bars show means and 95% confidence intervals.

![Route computation frequency for high traffic](../results/graphs/route_reviews-high.png)

High traffic (200 background vehicles): Mist Dynamic 28.67; Mist + Fog 28.67. Bars show means and 95% confidence intervals.

### Fallback decision latency

Time to apply the Fog route in runs where the watchdog actually triggered, in milliseconds.

![Fallback decision latency for low traffic](../results/graphs/fallback_decision_ms-low.png)

Low traffic (72 background vehicles): Mist + Fog 826.5. Bars show means and 95% confidence intervals.

![Fallback decision latency for medium traffic](../results/graphs/fallback_decision_ms-medium.png)

Medium traffic (144 background vehicles): Mist + Fog 826.6. Bars show means and 95% confidence intervals.

![Fallback decision latency for high traffic](../results/graphs/fallback_decision_ms-high.png)

High traffic (200 background vehicles): Mist + Fog 826.6. Bars show means and 95% confidence intervals.

### Control transmissions

Mean number of control-packet transmissions per run. This is supporting communication-load evidence.

![Control transmissions for low traffic](../results/graphs/control_transmissions-low.png)

Low traffic (72 background vehicles): Fog/Cloud 22,656; Mist 22,655; Mist Dynamic 22,647; Mist + Fog 22,653. Bars show means and 95% confidence intervals.

![Control transmissions for medium traffic](../results/graphs/control_transmissions-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 39,994; Mist 40,005; Mist Dynamic 40,031; Mist + Fog 40,013. Bars show means and 95% confidence intervals.

![Control transmissions for high traffic](../results/graphs/control_transmissions-high.png)

High traffic (200 background vehicles): Fog/Cloud 54,390; Mist 54,251; Mist Dynamic 54,294; Mist + Fog 54,237. Bars show means and 95% confidence intervals.

### Control bytes

Mean control traffic volume in bytes per run. This is supporting communication-load evidence.

![Control bytes for low traffic](../results/graphs/control_bytes-low.png)

Low traffic (72 background vehicles): Fog/Cloud 1,812,643; Mist 1,812,487; Mist Dynamic 1,811,834; Mist + Fog 1,812,378. Bars show means and 95% confidence intervals.

![Control bytes for medium traffic](../results/graphs/control_bytes-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 3,199,768; Mist 3,200,463; Mist Dynamic 3,202,549; Mist + Fog 3,201,222. Bars show means and 95% confidence intervals.

![Control bytes for high traffic](../results/graphs/control_bytes-high.png)

High traffic (200 background vehicles): Fog/Cloud 4,351,458; Mist 4,340,157; Mist Dynamic 4,343,608; Mist + Fog 4,339,125. Bars show means and 95% confidence intervals.

### EV corridor delay versus free flow

Extra travel time relative to the modeled free-flow corridor, in seconds.

![EV corridor delay versus free flow for low traffic](../results/graphs/ev_delay_vs_freeflow_s-low.png)

Low traffic (72 background vehicles): Fog/Cloud 24.3; Mist 24.7; Mist Dynamic 24.2; Mist + Fog 24.4. Bars show means and 95% confidence intervals.

![EV corridor delay versus free flow for medium traffic](../results/graphs/ev_delay_vs_freeflow_s-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 25.5; Mist 26.0; Mist Dynamic 25.3; Mist + Fog 25.2. Bars show means and 95% confidence intervals.

![EV corridor delay versus free flow for high traffic](../results/graphs/ev_delay_vs_freeflow_s-high.png)

High traffic (200 background vehicles): Fog/Cloud 27.3; Mist 28.2; Mist Dynamic 26.1; Mist + Fog 26.2. Bars show means and 95% confidence intervals.

### EV route distance

Distance traveled by the EV to reach the accident, in metres.

![EV route distance for low traffic](../results/graphs/ev_distance_m-low.png)

Low traffic (72 background vehicles): Fog/Cloud 1778.9; Mist 1778.9; Mist Dynamic 1779.0; Mist + Fog 1778.6. Bars show means and 95% confidence intervals.

![EV route distance for medium traffic](../results/graphs/ev_distance_m-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 1778.9; Mist 1779.0; Mist Dynamic 1779.4; Mist + Fog 1779.6. Bars show means and 95% confidence intervals.

![EV route distance for high traffic](../results/graphs/ev_distance_m-high.png)

High traffic (200 background vehicles): Fog/Cloud 1778.4; Mist 1778.7; Mist Dynamic 1780.3; Mist + Fog 1780.3. Bars show means and 95% confidence intervals.

### EV travel time

EV movement time from departure to accident arrival, in seconds.

![EV travel time for low traffic](../results/graphs/ev_travel_s-low.png)

Low traffic (72 background vehicles): Fog/Cloud 152.3; Mist 152.7; Mist Dynamic 152.2; Mist + Fog 152.3. Bars show means and 95% confidence intervals.

![EV travel time for medium traffic](../results/graphs/ev_travel_s-medium.png)

Medium traffic (144 background vehicles): Fog/Cloud 153.5; Mist 153.9; Mist Dynamic 153.3; Mist + Fog 153.3. Bars show means and 95% confidence intervals.

![EV travel time for high traffic](../results/graphs/ev_travel_s-high.png)

High traffic (200 background vehicles): Fog/Cloud 155.2; Mist 156.1; Mist Dynamic 154.2; Mist + Fog 154.3. Bars show means and 95% confidence intervals.

### Normal operation route decision latency

These figures separate seeds without a stall from seeds assigned the controlled 900 ms Mist stall. Fog/Cloud is unaffected by that local stall.

![Normal operation route decision latency for low traffic](../results/graphs/route_decision_ms-normal-low.png)

Low traffic, normal operation: Fog/Cloud 626.54 ms (n=17); Mist 326.00 ms (n=17); Mist Dynamic 326.00 ms (n=17); Mist + Fog 326.00 ms (n=17). Error bars show 95% confidence intervals.

![Normal operation route decision latency for medium traffic](../results/graphs/route_decision_ms-normal-medium.png)

Medium traffic, normal operation: Fog/Cloud 626.54 ms (n=21); Mist 326.00 ms (n=21); Mist Dynamic 326.00 ms (n=21); Mist + Fog 326.00 ms (n=21). Error bars show 95% confidence intervals.

![Normal operation route decision latency for high traffic](../results/graphs/route_decision_ms-normal-high.png)

High traffic, normal operation: Fog/Cloud 626.54 ms (n=22); Mist 326.00 ms (n=22); Mist Dynamic 326.00 ms (n=22); Mist + Fog 326.00 ms (n=22). Error bars show 95% confidence intervals.

### Normal operation ev response time

These figures separate seeds without a stall from seeds assigned the controlled 900 ms Mist stall. Fog/Cloud is unaffected by that local stall.

![Normal operation ev response time for low traffic](../results/graphs/ev_response_s-normal-low.png)

Low traffic, normal operation: Fog/Cloud 153.41 s (n=17); Mist 153.65 s (n=17); Mist Dynamic 152.97 s (n=17); Mist + Fog 152.97 s (n=17). Error bars show 95% confidence intervals.

![Normal operation ev response time for medium traffic](../results/graphs/ev_response_s-normal-medium.png)

Medium traffic, normal operation: Fog/Cloud 154.76 s (n=21); Mist 155.05 s (n=21); Mist Dynamic 154.81 s (n=21); Mist + Fog 154.81 s (n=21). Error bars show 95% confidence intervals.

![Normal operation ev response time for high traffic](../results/graphs/ev_response_s-normal-high.png)

High traffic, normal operation: Fog/Cloud 156.55 s (n=22); Mist 156.98 s (n=22); Mist Dynamic 155.02 s (n=22); Mist + Fog 155.02 s (n=22). Error bars show 95% confidence intervals.

### Controlled Mist stalls route decision latency

These figures separate seeds without a stall from seeds assigned the controlled 900 ms Mist stall. Fog/Cloud is unaffected by that local stall.

![Controlled Mist stalls route decision latency for low traffic](../results/graphs/route_decision_ms-controlled_stall-low.png)

Low traffic, controlled mist stalls: Fog/Cloud 626.54 ms (n=7); Mist 1226.00 ms (n=7); Mist Dynamic 1226.00 ms (n=7); Mist + Fog 826.54 ms (n=7). Error bars show 95% confidence intervals.

![Controlled Mist stalls route decision latency for medium traffic](../results/graphs/route_decision_ms-controlled_stall-medium.png)

Medium traffic, controlled mist stalls: Fog/Cloud 626.54 ms (n=8); Mist 1226.00 ms (n=8); Mist Dynamic 1226.00 ms (n=8); Mist + Fog 826.60 ms (n=8). Error bars show 95% confidence intervals.

![Controlled Mist stalls route decision latency for high traffic](../results/graphs/route_decision_ms-controlled_stall-high.png)

High traffic, controlled mist stalls: Fog/Cloud 626.54 ms (n=8); Mist 1226.00 ms (n=8); Mist Dynamic 1226.00 ms (n=8); Mist + Fog 826.63 ms (n=8). Error bars show 95% confidence intervals.

### Controlled Mist stalls ev response time

These figures separate seeds without a stall from seeds assigned the controlled 900 ms Mist stall. Fog/Cloud is unaffected by that local stall.

![Controlled Mist stalls ev response time for low traffic](../results/graphs/ev_response_s-controlled_stall-low.png)

Low traffic, controlled mist stalls: Fog/Cloud 153.07 s (n=7); Mist 153.14 s (n=7); Mist Dynamic 153.14 s (n=7); Mist + Fog 153.00 s (n=7). Error bars show 95% confidence intervals.

![Controlled Mist stalls ev response time for medium traffic](../results/graphs/ev_response_s-controlled_stall-medium.png)

Medium traffic, controlled mist stalls: Fog/Cloud 153.88 s (n=8); Mist 153.88 s (n=8); Mist Dynamic 152.31 s (n=8); Mist + Fog 151.50 s (n=8). Error bars show 95% confidence intervals.

![Controlled Mist stalls ev response time for high traffic](../results/graphs/ev_response_s-controlled_stall-high.png)

High traffic, controlled mist stalls: Fog/Cloud 155.25 s (n=8); Mist 156.62 s (n=8); Mist Dynamic 154.69 s (n=8); Mist + Fog 154.62 s (n=8). Error bars show 95% confidence intervals.

### Matched seed differences in ev response time

Each bar subtracts configuration B from A for the same delivered seeds. Below zero means A is faster. An interval crossing zero does not establish a difference; these comparisons are exploratory and not adjusted for multiple testing.

![Matched seed differences in ev response time for low traffic](../results/graphs/paired_ev_response_s-low.png)

Low traffic: Mist minus Fog/Cloud 0.19 s, 95% CI [-0.36, 0.73], n=24; Mist Dynamic minus Mist -0.48 s, 95% CI [-1.45, 0.49], n=24; Mist + Fog minus Mist Dynamic -0.04 s, 95% CI [-0.10, 0.02], n=24.

![Matched seed differences in ev response time for medium traffic](../results/graphs/paired_ev_response_s-medium.png)

Medium traffic: Mist minus Fog/Cloud 0.21 s, 95% CI [-0.68, 1.09], n=29; Mist Dynamic minus Mist -0.60 s, 95% CI [-1.98, 0.77], n=29; Mist + Fog minus Mist Dynamic -0.22 s, 95% CI [-0.89, 0.44], n=29.

![Matched seed differences in ev response time for high traffic](../results/graphs/paired_ev_response_s-high.png)

High traffic: Mist minus Fog/Cloud 0.68 s, 95% CI [-0.26, 1.63], n=30; Mist Dynamic minus Mist -1.95 s, 95% CI [-3.47, -0.43], n=30; Mist + Fog minus Mist Dynamic -0.02 s, 95% CI [-0.05, 0.02], n=30.

### Matched seed differences in route decision latency

Each bar subtracts configuration B from A for the same delivered seeds. Below zero means A is faster. An interval crossing zero does not establish a difference; these comparisons are exploratory and not adjusted for multiple testing.

![Matched seed differences in route decision latency for low traffic](../results/graphs/paired_route_decision_ms-low.png)

Low traffic: Mist minus Fog/Cloud -38.04 ms, 95% CI [-214.49, 138.41], n=24; Mist + Fog minus Mist Dynamic -116.51 ms, 95% CI [-194.83, -38.19], n=24.

![Matched seed differences in route decision latency for medium traffic](../results/graphs/paired_route_decision_ms-medium.png)

Medium traffic: Mist minus Fog/Cloud -52.27 ms, 95% CI [-207.98, 103.45], n=29; Mist + Fog minus Mist Dynamic -110.18 ms, 95% CI [-179.28, -41.08], n=29.

![Matched seed differences in route decision latency for high traffic](../results/graphs/paired_route_decision_ms-high.png)

High traffic: Mist minus Fog/Cloud -60.54 ms, 95% CI [-211.69, 90.61], n=30; Mist + Fog minus Mist Dynamic -106.50 ms, 95% CI [-173.57, -39.42], n=30.

The complete numeric means, valid sample sizes, standard deviations, and intervals are in `../results/processed/summary-batch.csv`. The seven main measures are also tabulated in `VERIFICATION.md`.
