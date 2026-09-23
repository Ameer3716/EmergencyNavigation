# Emergency Vehicle Navigation Project Specification

## 1. Overview & Objectives
This project investigates intelligent emergency vehicle (EV) navigation in a Connected and Automated Vehicle (VANET) environment using hierarchical edge computing (Mist, Fog, and Cloud). The primary objective is to minimize EV response time while mitigating the impact on normal traffic through:
1. Low-latency mist-based local route planning.
2. Dynamic congestion-aware rerouting based on real-time V2V and V2I sensor feedback.
3. Fault-tolerant failover via a watchdog mechanism delegating to fog/cloud computation upon mist timeout.
4. Active V2I traffic-light preemption creating green waves along the EV corridor.

---

## 2. Experimental Configurations

The simulation framework evaluates five matched configurations sharing identical road geometry, traffic demand, accident placement, radio propagation, and pseudo-random seeds:

| Configuration | Route Computation Tier | Algorithm | Dynamic Updates | Fallback Watchdog | Traffic Light Preemption |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`FogCloudAStar`** | Edge/Cloud (Fog RSU / Cloud Server) | Static A* | None (fixed departure route) | N/A | Enabled (V2I) |
| **`MistAStar`** | Mist (On-Board Unit of EV) | Static A* | None (fixed departure route) | N/A | Enabled (V2I) |
| **`MistDynamicAStar`** | Mist (On-Board Unit of EV) | Dynamic A* | Periodic (5.0 s cycle) | N/A | Enabled (V2I) |
| **`MistDynamicFogFallback`** | Mist with Fog Failover | Dynamic A* | Periodic (5.0 s cycle) | Active (800 ms threshold) | Enabled (V2I) |
| **`NoPreemptionBaseline`** | Edge/Cloud (Fog RSU / Cloud Server) | Static A* | None (identical to `FogCloudAStar`) | N/A | **Disabled** (normal signal cycles) |

In addition, two diagnostic configurations validate targeted safety mechanics:
* **`ForcedMistFailure`**: Deliberately injects an immediate mist computation exception to verify instant fallback to the nearest Fog RSU.
* **`ForcedMistTimeout`**: Deliberately delays mist computation (1200 ms) beyond the 800 ms watchdog threshold to verify genuine timeout-driven Fog takeover.
* **`CongestionReroute`**: Injects localized downstream corridor blockage to confirm dynamic route diversion around slow road links.

---

## 3. Network & Simulation Environment

### 3.1 Road Network (`grid.net.xml`)
* **Topology**: 4 × 4 bidirectional arterial grid network with 16 signalized junctions (labeled A0 through D3).
* **Link Spacing**: 300 m between junction centers.
* **Road Geometry**: Dual-lane directional edges with dedicated turning lanes and explicitly defined turn connections (preventing illegal turning movements).
* **Speed Limits**: 13.89 m/s (50 km/h) for normal arterial road edges.

### 3.2 Vehicle Demand & Traffic Densities
* **Normal Traffic**: Flows continuously from $t=0\text{ s}$ to $t=360\text{ s}$ across peripheral grid entries.
  * **Low Density**: Headway 5.0 s (72 total background vehicles).
  * **Medium Density**: Headway 2.5 s (144 total background vehicles).
  * **High Density**: Headway 1.8 s (200 total background vehicles).
* **Accident Vehicle**: Spawns on edge approaching junction D3 and halts at $t=60\text{ s}$, creating a disabled vehicle incident.
* **Emergency Vehicle (Ambulance)**: Departs from peripheral edge A0A1 destined for the accident location at junction D3 (corridor distance ~1776.42 m). Ambulance is held via TraCI speed-hold at $t=0.1\text{ s}$ until initial route computation and application are complete, ensuring route computation and communication latencies are accurately reflected in response time.

### 3.3 Roadside Units (RSUs) & Infrastructure
* Three RSUs deployed at strategic arterial junctions:
  * **RSU 0**: Monitoring junction B1.
  * **RSU 1**: Monitoring junction C2.
  * **RSU 2**: Monitoring accident junction D3.
* RSUs collect periodic 1.0 s V2X beacons from normal traffic, compute rolling edge speed averages, and broadcast aggregated traffic status reports.

---

## 4. Communication & Message Dissemination

* **Wireless Protocol**: Native Veins IEEE 802.11p WAVE / DSRC at 5.89 GHz (no auxiliary uncalibrated wireless delays).
* **Emergency Message (EM)**:
  * Triggered when the stationary accident vehicle is detected by RSU 2 or nearby traffic. Detection occurs between $t=65.5\text{ s}$ and $t=68.0\text{ s}$ depending on background vehicle traffic positions. EM generation time matches the exact logged detection time (`emGenerationTime`).
  * **Explicit EM Schema**:
    * `eventId`: Unique string tracking the incident event (e.g. `accident-1`).
    * `messageId`: Unique message tracking identifier (e.g. `em-accident-1`).
    * `generationTimestamp`: Precise simulation timestamp when the EM was generated ($t_{\text{gen}} \in [65.5, 68.0]\text{ s}$).
    * `incidentLocation`: Approaching road edge ID (`D3C3`) and incident coordinates $(x=870, y=900)$.
    * `senderId`: Identifier of the transmitting node (starts as `EmergencyGridScenario.rsu[2]`, updated to forwarding node on relay).
    * `remainingHops`: TTL countdown counter initialized to `maxHops` (default: 10), decremented by 1 at each forwarding hop.
    * `hopCount`: Cumulative number of network forwarding hops traversed (starts at 0).
    * `packetBytes`: Useful message length (256 bytes useful payload + 10 bytes header = 266 bytes).
  * **Hop Limit (`maxHops`)**: Configurable via NED (`EmergencyRelayApp.ned`) and `omnetpp.ini` (default: **10 hops**). Rebroadcast delay is uniformly distributed between 5 ms and 20 ms with duplicate message suppression (60 s cache window).
  * Multi-hop relay supported across both intermediate normal vehicles (V2V) and RSUs (V2I/I2V).

---

## 5. Routing Algorithms & Computation Model

### 5.1 Mist OBU Input Data Schema
The On-Board Unit (OBU) executing the Mist routing module ingests:
1. **EV Current State**: Current road link ID (`mobility->getRoadId()`), vehicle coordinates $(x,y)$, and forward velocity ($v$) queried via TraCI.
2. **V2V Beacon Telemetry**: Periodic 1.0 s IEEE 802.11p beacon samples from surrounding normal vehicles (`vehicleId`, `edgeId`, instantaneous `speed`, `timestamp`).
3. **V2I Infrastructure Reports**: Periodic 1.0 s `TrafficStatus` broadcast tables emitted by RSUs containing rolling edge mean speed and vehicle count.
4. **Permitted Road Topology**: Directed graph parsed from `grid.net.xml` containing edge lengths, free-flow speed limits, and explicit junction turn connectivity matrices (preventing illegal turning movements).

### 5.2 Static & Dynamic A*
* **Static Cost**: $C_e = \text{length}_e / \text{speedLimit}_e$.
* **Heuristic**: $h(u) = \text{EuclideanDistance}(u, \text{dest}) / \max(v_{\text{net}})$.
* **Dynamic Congestion Cost Formula**:
  $$C_e = \left(\frac{\text{length}_e}{\max(v_{\text{mean}}, 1.0\text{ m/s})}\right) \times \left(1 + \lambda \cdot \min\left(1.0, \frac{K_e}{C_{\text{capacity}}}\right)\right)$$
  where $\lambda = 0.5$, $C_{\text{capacity}} = \text{length}_e / 7.5\text{ m}$, and $K_e$ is observed vehicle count on edge $e$.
* **Single-Vehicle Deceleration Guard (`minVehicles = 3`)**: Dynamic edge cost adjustment requires at least 3 observed vehicles on the edge. This prevents transient isolated decelerations (such as normal vehicles braking for amber signals) from triggering erroneous macro detours.
* **Reroute Thresholds**: Alternate routes are selected if estimated remaining corridor cost improves by at least 10% (or 5% if future edge has stayed below 30% speed limit for 2 consecutive samples). Minimum reroute gap is 30.0 s to prevent route oscillation.

### 5.3 Tiered Computation Delays
* **Mist Computing (OBU)**: $T_{\text{comp}} = 300\text{ ms} + 2\text{ ms} \times \text{expandedNodes}$. Zero backhaul latency.
* **Fog Computing (RSU)**: $T_{\text{comp}} = 300\text{ ms} + 2\text{ ms} \times \text{expandedNodes}$. Local V2I wireless transmission delay. Fog coverage radius is 500 m.
* **Cloud Computing**: Same computation formula + 150 ms one-way WAN backhaul latency (300 ms round-trip) added to wireless transmission.
* **Watchdog Failover**: 800 ms timer. If mist computation exceeds 800 ms, the OBU cancels mist calculation and applies the route returned by the fog RSU.

---

## 6. Traffic Light Preemption Protocol

* **Trigger**: EV evaluates next signal along planned route every 500 ms. Preemption is requested when distance to next signal $\le 250\text{ m}$ or estimated time of arrival (ETA) $\le 15.0\text{ s}$.
* **V2I Preemption Command**: Received by junction OMNeT++ controller.
* **Transition Phasing**:
  1. 150 ms controller processing delay.
  2. Conflicting green movements switch to **Yellow for 2.0 s**.
  3. **All-Red clearance for 1.0 s**.
  4. EV entry movement activates **Solid Green** (held for up to 25.0 s until EV crosses stop line).
  5. Controller restores original SUMO signal plan.
* **Green-Wave Margin**: Because requests occur ~18 s prior to EV arrival and phase change takes 3.15 s, green is established 14.8–16.2 s before EV arrival, creating an uninterrupted green wave.

---

## 7. Metrics & Statistical Design

1. **Packet Delivery Ratio (PDR)**: Ratio of unique EM messages delivered to and processed by the EV to total EMs generated. Evaluated across all generated runs ($N=30$ per density) using the bounded binomial **Wilson score 95% confidence interval**.
2. **End-to-End Delivery Latency (s)**: Timestamp of EV EM processing minus that run's logged EM generation timestamp ($t_{\text{ev\_processed}} - t_{\text{gen}}$).
3. **Emergency Vehicle Response Time (s)**: Elapsed duration from that run's logged Emergency Message generation timestamp ($t_{\text{gen}} \in [65.5, 68.0]\text{ s}$) to EV arrival at the destination stop line in SUMO:
   $$\text{EV Response Time} = t_{\text{arrival}} - t_{\text{gen}}$$
   *(Temporal breakdown: Incident trigger at $t=60.0\text{ s} \rightarrow$ deceleration $\rightarrow$ confirmed standstill $\rightarrow$ detection / EM generation at $t_{\text{gen}} \in [65.5, 68.0]\text{ s} \rightarrow$ EV receipt at $t_{\text{receive}} \in [65.51, 68.02]\text{ s} \rightarrow$ EV departure at $t_{\text{departure}} \in [66.5, 69.5]\text{ s} \rightarrow$ on-scene arrival at $t_{\text{arrival}} \in [204.0, 254.0]\text{ s}$ for active preemption, $[250.0, 349.5]\text{ s}$ for no-preemption baseline, and $[204.0, 349.5]\text{ s}$ across all 425 delivered runs)*.
4. **Route Decision Latency (s)**: Final applied route timestamp minus route request initiation timestamp.
5. **Traffic Light Waiting Time (`traffic_light_wait_s`)**: Total cumulative duration where EV speed $< 0.1\text{ m/s}$ within $\le 20.0\text{ m}$ of a traffic light. Evaluated using a reproducible non-parametric bootstrap percentile 95% confidence interval (10,000 resamples, fixed seed 42) to respect physical non-negativity without artificial clamping.
6. **Corridor Delay vs Free-Flow (`ev_delay_vs_freeflow_s`)**: $\max(0.0, \text{ev\_travel\_s} - 140.0\text{ s})$, measuring total corridor travel delay relative to the 140.0 s unimpeded green-wave travel time. Evaluated using a reproducible non-parametric bootstrap percentile 95% confidence interval (10,000 resamples, fixed seed 42).
7. **Network Routing Load (NRL)**: Total transmitted routing packets divided by delivered EMs. Conditional on successful EM delivery ($n=28$ low/high, $n=29$ medium) because zero deliveries leave the ratio undefined.
8. **Control Overhead (Bytes)**: Cumulative byte volume of control packets transmitted across the network.

### Experimental Sample Size & Reporting
* **Sample Size**: 30 independent, matched pseudo-random seeds per traffic density per configuration (90 runs per config; exactly **450 total runs** across the 5 configurations).
* **Sample Reporting**: Evaluated with $N=30$ for network transmission/PDR metrics, and conditionally reported on destination arrival ($n=28$ low, $n=29$ medium, $n=28$ high) for mobility and travel metrics due to genuine IEEE 802.11p network partitions in sparse topologies (seeds 12 & 28 low, 21 medium, 13 & 21 high). Response times are verified for all 425 delivered runs (`artifacts/response_time_verification.csv`), with the 25 partition runs classified as not applicable.
* **Statistical Rigor**: Continuous metrics reported as **Mean ± StdDev** with **Student-t 95% Confidence Intervals** calculated as $\bar{x} \pm t_{n-1, 0.975} \cdot \frac{s}{\sqrt{n}}$. PDR reported using bounded binomial **Wilson score intervals**. Nonnegative waiting times and corridor delay reported using bootstrap percentile intervals (10,000 resamples, fixed seed 42). Paired differences reported with exact Student-t two-sided p-values and Cohen's $d_z$ effect sizes. Raw simulation outputs (`.sca`, `.vec`, `.vci`, CSV logs) preserved without manual modification.

