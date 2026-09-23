# Methodology

## 1. Network Topology & Simulation Framework

The simulation environment integrates microscopic vehicular mobility (SUMO 1.18.0) and wireless network protocol simulation (OMNeT++ 6.3.0 / Veins 5.3.1) coupled bidirectionally over TraCI. 

The road network (`grid.net.xml`) is a 4 × 4 bidirectional arterial grid featuring:
* 16 signalized junctions (labeled A0 through D3) spaced 300 m apart.
* 48 directed road links with dedicated turning lanes and explicitly defined turn connection matrices.
* Uniform 13.89 m/s (50 km/h) speed limits.
* Three Roadside Units (RSUs) positioned at junctions B1 (`RSU 0`), C2 (`RSU 1`), and D3 (`RSU 2`).

Traffic demand is continuously injected between $t=0\text{ s}$ and $t=360\text{ s}$ across peripheral arterial boundaries:
* **Low Traffic Density**: Headway 5.0 s (~72 total background vehicles).
* **Medium Traffic Density**: Headway 2.5 s (~144 total background vehicles).
* **High Traffic Density**: Headway 1.8 s (~200 total background vehicles).
The accident incident is triggered approaching junction D3 at $t=60.0\text{ s}$. The vehicle decelerates and halts ($v < 0.1\text{ m/s}$); upon confirming standstill for stationary verification, `RSU 2` detects the incident and broadcasts an Emergency Message (EM) at $t_{\text{gen}} \in [65.5, 68.0]\text{ s}$ depending on vehicle deceleration dynamics and background traffic density. The ambulance departs from peripheral link A0A1 destined for D2D3 (free-flow corridor length 1776.42 m).

---

## 2. Experimental Configurations

Five matched configurations share identical road geometry, background vehicle demand, accident placement, radio propagation, and pseudo-random seed sets:

| Configuration | Route Computation Tier | Algorithm | Dynamic Updates | Fallback Watchdog | Traffic Light Preemption |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`FogCloudAStar`** | Edge / Cloud (RSU / Central Server) | Static A* | None (fixed departure route) | N/A | Enabled (V2I) |
| **`MistAStar`** | Mist (Ambulance OBU) | Static A* | None (fixed departure route) | N/A | Enabled (V2I) |
| **`MistDynamicAStar`** | Mist (Ambulance OBU) | Dynamic A* | Periodic (5.0 s cycle) | N/A | Enabled (V2I) |
| **`MistDynamicFogFallback`** | Mist with Fog Failover | Dynamic A* | Periodic (5.0 s cycle) | Active (800 ms threshold) | Enabled (V2I) |
| **`NoPreemptionBaseline`** | Edge / Cloud (RSU / Central Server) | Static A* | None (identical to `FogCloudAStar`) | N/A | **Disabled** (normal cycles) |

Diagnostic configurations include:
* **`ForcedMistFailure`**: Deliberately injects an immediate mist computation exception to verify instant fallback to the nearest Fog RSU.
* **`ForcedMistTimeout`**: Deliberately delays mist computation (1200 ms) beyond the 800 ms watchdog threshold to verify genuine timeout-driven Fog takeover.
* **`CongestionReroute`**: Verifies turn-valid dynamic detour around injected link blockage.

---

## 3. Communication Architecture & Telemetry Schemas

### 3.1 Wireless Protocol
Vehicles and infrastructure communicate using native Veins IEEE 802.11p WAVE / DSRC at 5.89 GHz on the Control Channel (CCH). Propagation incorporates free-space path loss and thermal noise floor (-98 dBm) with transmission power 20 mW (1 W for RSUs).

### 3.2 Emergency Message (EM) Schema
* `eventId`: Unique incident string (e.g. `accident-1`).
* `messageId`: Unique message tracking identifier (e.g. `em-accident-1`).
* `generationTimestamp`: Precise simulation timestamp when the EM was emitted ($t_{\text{gen}} \in [65.5, 68.0]\text{ s}$).
* `incidentLocation`: Approaching road edge ID (`D3C3`) and incident coordinates $(x=870, y=900)$.
* `senderId`: Transmitting node identifier.
* `remainingHops`: Initialized to `maxHops = 10`, decremented by 1 at each forwarding hop.
* `hopCount`: Forwarding counter incremented at each hop (starts at 0).
* `packetBytes`: 256 bytes payload + 10 bytes header (266 bytes).

Relay nodes cache message IDs for 60.0 s, suppress duplicate receptions, and forward with a uniform random delay between 5 ms and 20 ms if `remainingHops > 1`.

### 3.3 Mist Input Data Schema
The ambulance On-Board Unit (OBU) executes route computation utilizing:
1. **EV State**: Link ID (`mobility->getRoadId()`), position coordinates $(x,y)$, and speed ($v$).
2. **V2V Beacons**: 1.0 s periodic broadcast samples from adjacent vehicles containing vehicle ID, link ID, instantaneous speed, and timestamp.
3. **V2I Status Reports**: 1.0 s aggregated traffic reports from RSUs containing rolling mean link speeds and vehicle counts.
4. **Network Topology Graph**: Complete turn connectivity matrix and link lengths from `grid.net.xml`.

---

## 4. Routing Algorithms & Computation Model

### 4.1 Static & Dynamic A* Formulations
* **Static Cost**: $C_e = \text{length}_e / \text{speedLimit}_e$.
* **Heuristic**: $h(u) = \text{EuclideanDistance}(u, \text{dest}) / \max(v_{\text{net}})$.
* **Dynamic Congestion Cost Formula**:
  $$C_e = \left(\frac{\text{length}_e}{\max(v_{\text{mean}}, 1.0\text{ m/s})}\right) \times \left(1 + \lambda \cdot \min\left(1.0, \frac{K_e}{C_{\text{capacity}}}\right)\right)$$
  where $\lambda = 0.5$, $C_{\text{capacity}} = \text{length}_e / 7.5\text{ m}$, and $K_e$ is observed vehicle count on link $e$.
* **Single-Vehicle Deceleration Guard (`minVehicles = 3`)**: Dynamic edge cost adjustment requires at least 3 observed vehicles on the edge. This prevents transient isolated decelerations (such as normal vehicles braking for amber signals) from triggering erroneous macro detours.
* **Reroute Thresholds**: Evaluated every 5.0 s. An alternate route is applied if:
  1. Estimated remaining corridor cost improves by $\ge 10\%$, OR
  2. A downstream link has remained below 30% speed limit for 2 consecutive samples and alternate route improves remaining cost by $\ge 5\%$.
  3. Minimum interval between consecutive reroutes is 30.0 s to prevent route oscillation.

### 4.2 Tiered Computation Latency
* **Mist Computing (OBU)**: $T_{\text{comp}} = 300\text{ ms} + 2\text{ ms} \times \text{expandedNodes}$. Zero backhaul latency.
* **Fog Computing (RSU)**: $T_{\text{comp}} = 300\text{ ms} + 2\text{ ms} \times \text{expandedNodes}$. V2I wireless transmission delay. Fog service radius: 500 m.
* **Cloud Computing**: Same computation formula + 150 ms one-way WAN backhaul latency (300 ms round-trip) added to wireless transmission.
* **Watchdog Failover**: 800 ms watchdog timer. If mist computation exceeds 800 ms, the OBU cancels mist calculation and applies the route returned by the fog RSU. In standard runs, mist computation consistently finishes in ~0.326 s, canceling the watchdog before expiration. Two diagnostic cases validate failover: `ForcedMistFailure` (immediate exception-driven failover in 0.3248 s) and `ForcedMistTimeout` (watchdog expiration after 800 ms with Fog takeover in 1.1267 s).

---

## 5. Traffic Light Preemption Protocol

* **Trigger**: EV evaluates the next signal along its route every 500 ms. Preemption is requested when distance to next signal $\le 250\text{ m}$ or estimated time of arrival (ETA) $\le 15.0\text{ s}$.
* **V2I Preemption Command**: Received by the nearest RSU and delegated to the target junction controller.
* **Transition Phasing**:
  1. 150 ms controller processing delay.
  2. Conflicting green movements switch to **Yellow for 2.0 s**.
  3. **All-Red clearance for 1.0 s**.
  4. EV entry movement activates **Solid Green** (held for up to 25.0 s until EV crosses stop line).
  5. Controller restores original SUMO signal plan.
* **Green-Wave Margin**: Because requests occur ~18 s prior to EV arrival and phase change takes 3.15 s, green is established 14.8–16.2 s before EV arrival, creating an uninterrupted green wave.

---

## 6. Empirical Findings & Anomaly Disclosures

### 6.1 FogCloud Medium-Density Seed 14: Wireless Preemption Loss
In `FogCloudAStar-medium-seed14`, the ambulance experienced a 17.0 s traffic light waiting time at Junction C2. Detailed packet and scalar auditing reveals:
* The EV successfully transmitted the preemption request for C2 at $t \approx 144.6\text{ s}$ via IEEE 802.11p broadcast.
* RSU 1 experienced heavy channel contention, recording 17,944 lost packets (including 2,479 RX/TX collisions and 15,465 SNIR losses).
* The single-shot preemption broadcast was dropped at the physical/MAC layer without application-level acknowledgment.
* Consequently, Junction C2 never received the preemption command and operated on its fixed SUMO cycle, presenting a red phase when the EV arrived at $t=164.5\text{ s}$.
* The EV waited 16.5 s at the C2 stop line until the normal signal turned green at $t=181.0\text{ s}$.
* This empirical case illustrates a critical VANET engineering reality: without application-layer acknowledgment or periodic retransmissions, wireless contention can prevent preemption. Across the 30 medium-density seeds, `FogCloudAStar` achieved a mean waiting time of 0.59 s (a **98.04% reduction** relative to `NoPreemptionBaseline`'s 29.97 s).

### 6.2 Dynamic A* High-Density Seed 22: Queue-Avoidance Detour
In `MistDynamicAStar-high-seed22`, the EV traversed 2376.45 m (+600 m extra) with a response time of 187.5 s:
* At $t=101.8\text{ s}$, Dynamic A* adjusted the path from A1B1 north to B1B2 due to cost improvement.
* At $t=131.8\text{ s}$, approaching B1B2, the dynamic router observed 3 queued background vehicles on edge B2C2 stopped at Junction C2's pre-timed red light ($v < 0.3 \times 13.89\text{ m/s}$ for 2 consecutive samples).
* The dynamic formula inflated the cost of B2C2 to >300 s, prompting the router to execute a macro-detour via `B2B3 -> B3C3 -> C3C2 -> C2D2 -> D2D3`.
* While the detour bypassed the queue, the 600 m additional travel distance cost ~45 s.
* This is a **legitimate congestion-driven reroute** under the model specification: preemption-oblivious dynamic routers perceive signal queues as persistent road congestion before reaching the 250 m preemption trigger. Consequently, Dynamic A* exhibits **higher variance in high-density traffic** (stddev 9.06 s vs. 2.78 s for static MistAStar), and does not achieve the lowest mean response time in high traffic (142.86 s vs. 142.18 s).

---

## 7. Metrics & Statistical Design

1. **Packet Delivery Ratio (PDR)**: Evaluated across all generated runs ($N=30$ per density) using the bounded binomial **Wilson score 95% confidence interval**:
   $$\text{Wilson CI} = \frac{\hat{p} + \frac{z^2}{2N} \pm z\sqrt{\frac{\hat{p}(1-\hat{p})}{N} + \frac{z^2}{4N^2}}}{1 + \frac{z^2}{N}}$$
   Yielding $[0.787, 0.982]$ for 28/30 deliveries (low and high density) and $[0.833, 0.994]$ for 29/30 deliveries (medium density).
2. **Emergency Vehicle Response Time (s)**: Elapsed duration from that run's logged Emergency Message generation timestamp ($t_{\text{gen}} \in [65.5, 68.0]\text{ s}$) to EV arrival at the destination stop line in SUMO:
   $$\text{EV Response Time} = t_{\text{arrival}} - t_{\text{gen}}$$
   *(Temporal breakdown: Incident trigger at $t=60.0\text{ s} \rightarrow$ kinematic deceleration and confirmed standstill $\rightarrow$ accident detection / EM generation at $t_{\text{gen}} \in [65.5, 68.0]\text{ s} \rightarrow$ EV receipt at $t_{\text{receive}} \in [65.51, 68.02]\text{ s} \rightarrow$ EV departure at $t_{\text{departure}} \in [66.5, 69.5]\text{ s} \rightarrow$ on-scene arrival at $t_{\text{arrival}} \in [204.0, 254.0]\text{ s}$ for active preemption, $[250.0, 349.5]\text{ s}$ for no-preemption baseline, and $[204.0, 349.5]\text{ s}$ across all 425 delivered runs)*.
3. **Dual Delay Metrics**:
   * `traffic_light_wait_s`: Standstill ($v < 0.1\text{ m/s}$) within $\le 20.0\text{ m}$ of a traffic light.
   * `ev_delay_vs_freeflow_s`: Total corridor travel delay relative to 140.0 s unimpeded green-wave travel time (`max(0.0, ev_travel_s - 140.0)`).
   * Both `traffic_light_wait_s` and `ev_delay_vs_freeflow_s` are non-negative, bounded, zero-inflated distributions. Both report reproducible **non-parametric bootstrap percentile 95% confidence intervals** (10,000 resamples, fixed random seed 42) rather than clipped Student-$t$ intervals.
4. **Trajectory Delay Decomposition**: Trajectory analysis across representative matched seeds indicates that the difference between total corridor travel-time savings and stop-line waiting comprises upstream queue creep ($0.1 \le v < 5.0\text{ m/s}$) and kinematic acceleration/deceleration recovery.
5. **Sample Reporting**: Evaluated with $N=30$ for network transmission/PDR metrics, and conditionally reported on destination arrival ($n=28$ low, $n=29$ medium, $n=28$ high) due to genuine IEEE 802.11p network partitions in sparse topologies (seeds 12 & 28 low, 21 medium, 13 & 21 high). Response times are verified for all 425 delivered runs (`artifacts/response_time_verification.csv`), with the 25 partition runs classified as not applicable. NRL is conditionally reported ($n=28/29$) because zero deliveries leave the packet ratio undefined. Continuous unbounded metrics report exact Student-t 95% confidence intervals and exact paired two-sided p-values with Cohen's $d_z$ effect sizes.

---

## 8. Source Code Traceability

All algorithmic and networking behaviors map to verified C++ and OMNeT++ NED implementations:
* **Ambulance OBU & Navigation**: `src/apps/EmergencyVehicleApp.cc`, `src/apps/MistRoutingModule.cc`
* **Static & Dynamic A* Router**: `src/routing/AStarRouter.cc`, `src/routing/RoadGraph.cc`
* **Traffic Light Controller**: `src/apps/TrafficLightController.cc`
* **Edge & Cloud Services**: `src/apps/FogService.cc`, `src/apps/CloudService.cc`
* **Vehicle & RSU Dissemination**: `src/apps/NormalVehicleApp.cc`, `src/apps/RsuApp.cc`, `src/apps/EmergencyRelayApp.cc`
* **Simulation Metrics Collection**: `src/metrics/MetricsCollector.cc`

