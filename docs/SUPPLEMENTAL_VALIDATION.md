# Supplementary route communication and red signal validation

The seven headline metrics and their matched batch are unchanged. These checks explain route-specific communication and demonstrate finite waiting under controlled red-signal conditions.

## Route transactions

A request is counted when the EV sends a Fog RouteRequest. An accepted reply is counted when the matching valid RouteReply is accepted and its route is applied. These counts come from original raw scalars; they are not radio reception counts at every relay. Completion is accepted replies divided by requests sent. Local Mist uses no wireless Fog transaction, so its completion and delay are N/A. EM PDR and EM throughput retain their original definitions.

Transaction turnaround starts when the EV sends the Fog request and ends when it applies the reply. It includes Fog or Cloud processing and Cloud backhaul. Network round trip subtracts processing and backhaul, and excludes the 500 ms watchdog wait. No exact route-packet byte counts were recorded, so no route throughput or route-packet PDR is invented.

| Density | Configuration | Requests | Accepted replies | Turnaround ms | Network ms |
| --- | --- | ---: | ---: | ---: | ---: |
| low | Fog/Cloud | 24 | 24 | 626.539 | 0.539 |
| low | Mist | 0 | 0 | N/A | N/A |
| low | Dynamic Mist | 0 | 0 | N/A | N/A |
| low | Mist + Fog | 7 | 7 | 326.539 | 0.539 |
| medium | Fog/Cloud | 29 | 29 | 626.543 | 0.543 |
| medium | Mist | 0 | 0 | N/A | N/A |
| medium | Dynamic Mist | 0 | 0 | N/A | N/A |
| medium | Mist + Fog | 8 | 8 | 326.598 | 0.598 |
| high | Fog/Cloud | 30 | 30 | 626.539 | 0.539 |
| high | Mist | 0 | 0 | N/A | N/A |
| high | Dynamic Mist | 0 | 0 | N/A | N/A |
| high | Mist + Fog | 8 | 8 | 326.630 | 0.630 |

Count and continuous delay intervals use Student-t 95% intervals. Completion-rate intervals use Wilson 95% intervals. Counts include all 30 scheduled runs; delays include completed transactions only. A conditional 100% completion rate does not imply every scheduled run received an EM.

## Controlled red signal scenarios

Eighteen isolated runs use densities low/medium/high, seeds 1 and 4, and Fog/Cloud, Mist with Fog, and the matched no-preemption control. The existing binary and trip files are reused. Junction A1 starts with a protected conflicting phase rrGGrr for 150 seconds. The original permissive A0A1 green is removed in this validation input so both EV movements from A0A1 are red, including a possible dynamically selected turn. Priority is requested within 10 metres or half a second to test deliberately late notice. The horizon is 400 seconds. All controller safety rules stay in force. These scenarios are supplementary stress tests, not additional samples in the headline batch. Late notice is a controlled boundary case; it is not the default priority algorithm or an estimated real-world frequency.

| Density | Configuration | Runs | Mean waiting seconds |
| --- | --- | ---: | ---: |
| low | Fog/Cloud | 2 | 10.500 |
| medium | Fog/Cloud | 2 | 12.000 |
| high | Fog/Cloud | 2 | 5.000 |
| low | Mist + Fog | 2 | 11.500 |
| medium | Mist + Fog | 2 | 12.750 |
| high | Mist + Fog | 2 | 6.250 |
| low | No preemption | 2 | 111.750 |
| medium | No preemption | 2 | 110.500 |
| high | No preemption | 2 | 97.250 |

Each priority case must record the conflicting initial phase, a red-priority transition at A1, observed standstill waiting on the approach, confirmed arrival, and less total waiting than its matched no-preemption control. Signal clearance and minimum-green timings are checked from raw event logs.

Two seeds per density provide mechanism validation, not a population performance claim. Wide Student-t intervals are retained and can extend below zero; all observed waiting times are positive. Some ordinary green-arrival runs can still correctly have zero waiting, and routing approaches can still share the same initial alert delivery outcomes.

Raw validation results, generated network and configurations, scenario provenance, and logs are retained in artifacts/signal_validation/. The reproducible runner is scripts/run_signal_validation.py; the processor is analysis/supplemental_validation.py.
