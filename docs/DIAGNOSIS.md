# Diagnosis before model changes

Baseline: FogCloudAStar. Proposed: MistDynamicFogFallback. This diagnosis uses retained ordinary results before matched-policy changes. No model code was changed to create it.

## Where response time goes

Response = EM delivery + route decision + release/sampling residual + measured driving. Signal standstill is part of driving, not an additional term. Queues, acceleration, turning and junction travel are also within driving; the old metric cannot causally separate them.

| Configuration | Density | Arrivals | Response s | EM ms | Decision ms | Driving s | Signal standstill s | Release/sampling residual s | Below 1 m/s after departure s |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| FogCloudAStar | low | 24 | 153.312 | 44.366 | 626.539 | 152.312 | 1.562 | 0.329 | 2.938 |
| FogCloudAStar | medium | 29 | 154.517 | 37.123 | 626.543 | 153.517 | 0.845 | 0.336 | 2.293 |
| FogCloudAStar | high | 30 | 156.200 | 32.171 | 626.539 | 155.200 | 0.667 | 0.341 | 2.067 |
| MistDynamicFogFallback | low | 24 | 147.104 | 44.366 | 471.991 | 146.458 | 0.000 | 0.129 | 0.896 |
| MistDynamicFogFallback | medium | 29 | 147.362 | 37.123 | 464.096 | 146.724 | 0.000 | 0.137 | 0.948 |
| MistDynamicFogFallback | high | 30 | 146.733 | 32.171 | 459.501 | 146.100 | 0.000 | 0.142 | 0.867 |

The below-1 m/s estimate uses existing 100 ms mobility rows after first movement, which repeat 500 ms SUMO states. It excludes the initial navigation hold. It is not substituted into old raw results.

Missing-header logs encountered here (read using the declared original schema, without editing raw evidence): mobility-FogCloudAStar-medium-seed24.csv. Two further missing headers exist in Dynamic Mist high seed 3 and low seed 5.

## Zero waiting: what is and is not established

The collector only queries next TLS for speed below 0.1 m/s, then requires next-TLS distance at most 20 m. It can miss slow crawling (0.1 to 1 m/s) and stopped queues farther than 20 m. Advance requests can genuinely prepare green before arrival. The old trace has no next-TLS distance or approach phase column, so zero cannot prove every junction was reached on green. New instrumentation will log next TLS, distance, link state and controller phase on each new SUMO state, actual junction entries, and whole-route slow time. No synthetic minimum waiting will be added.

## Physical margin

External road travel alone takes at least 1721.6 / 13.9 = 123.856 s. This optimistic bound omits internal junctions, acceleration, route decision and EM delivery. Against the old baseline means, even a physically ideal proposal has at most 19.21%, 19.84%, and 20.71% response reduction in low, medium, and high density; real achievable margins are smaller. A 20% ordinary gain is impossible at low and medium with the unchanged trip and speed cap. An advance-policy baseline may be faster and reduce available margin. No 20% outcome is promised.

## Scheduled start-stop caveat

The shared special.rou.xml also defines a mandatory stop at lane position 30 m until time 65. Because the EV is held at position zero until routing completes, it reaches that stop later and SUMO still performs a stop. Initial instrumented held-out runs localize one full stop here, about 260 m before the next signal, even when signal waiting is zero. Whole-route slow time and full stops include this common scheduled stop; they must not all be attributed to traffic queues or red lights. The input is preserved for every configuration. This caveat was added after examining new instrumentation, without changing model parameters or selecting seeds.

## Plan fixed before new reported runs

The old dynamic frameworks use 250 m / 20 s requests; Fog/static Mist use 100 m / 8 s. Add explicit FogCloudAStarAdvance and MistAStarAdvance controls at 250 m / 20 s. Preserve the old results. Report original-policy and matched-policy comparisons separately. All signal controllers retain identical safety rules.

Tune proposed review interval and route replacement thresholds only on seeds 101–110, then freeze settings before all reported seeds 1–30. Use the same ordinary and existing obstruction inputs for every configuration, including the speed cap and SUMO driving seed behavior. Report full stops, green crossing share, whole-route below-1 m/s time and background time loss even when proposed loses. Signal-aware routing requires reliable signal observations; no unavailable global future phase information will be invented.
