> Retained original-policy experiment. See [POLICY_VALIDATION.md](POLICY_VALIDATION.md) for the new matched-policy results and unmet requirements.

# Audit of the 20 percent EV response target

The acceptance target is at least 20 percent lower mean EV response time in each density. Ordinary traffic and controlled obstruction remain separate experiments.

| Experiment | Density | Baseline s | Proposed s | Reduction percent | Target s | Target met |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| Ordinary traffic | low | 153.312 | 147.104 | 4.05 | 122.650 | No |
| Ordinary traffic | medium | 154.517 | 147.362 | 4.63 | 123.614 | No |
| Ordinary traffic | high | 156.200 | 146.733 | 6.06 | 124.960 | No |
| Controlled obstruction | low | 266.292 | 144.417 | 45.77 | 213.033 | Yes |
| Controlled obstruction | medium | 272.259 | 158.224 | 41.88 | 217.807 | Yes |
| Controlled obstruction | high | 278.417 | 160.083 | 42.50 | 222.733 | Yes |

## Physical feasibility in the current ordinary grid

The shortest legal path contains at least 1721.600 m of external road lanes. All 83 delivered proposed runs start route computation at lane position zero. At the current 13.900 m/s EV speed cap, external road travel alone takes at least 123.856 s.

This is an optimistic lower bound. It omits junction connector travel, acceleration, message delivery, route computation and every traffic delay. Those factors can only increase response time.

Ordinary densities whose targets fall below this optimistic bound: low, medium. A target below this bound cannot be met by routing and signal timing changes while preserving the current trip, speed cap and measured baseline. A target above this bound is not guaranteed achievable because the bound omits unavoidable delays.

A different demand scenario or vehicle policy would be a new experiment. Apply common input changes to every compared configuration, justify them before running, retain every scheduled seed, and keep the current ordinary results. Do not slow the baseline or select seeds to manufacture the target.

Final verdict: 3 of 6 experiment and density combinations meet the target.

## Matched-policy extension (2026-10-10)

The new isolated experiment contains 630 ordinary and 540 obstruction runs, plus 180 held-out candidate runs on seeds 101–110. Previous tables in this file describe the retained original-policy experiment. New matched-policy estimates and explicit unmet requirements are in [POLICY_VALIDATION.md](POLICY_VALIDATION.md). The fixed design is in [POLICY_EXPERIMENT_PLAN.md](POLICY_EXPERIMENT_PLAN.md); the prior timing and zero-wait diagnosis is in [DIAGNOSIS.md](DIAGNOSIS.md). The selected settings are frozen in results/policy_validation/selection.json. No artificial waiting or outcome gate is used.

### Updated bound against the matched advance-policy baseline

| Context | Density | Matched baseline s | Optimistic bound s | Maximum theoretically possible reduction % | 20% target below bound |
| --- | --- | ---: | ---: | ---: | --- |
| ordinary | low | 147.542 | 123.856 | 16.05 | Yes |
| ordinary | medium | 148.000 | 123.856 | 16.31 | Yes |
| ordinary | high | 147.717 | 123.856 | 16.15 | Yes |
| obstruction | low | 264.792 | 123.856 | 53.23 | No |
| obstruction | medium | 263.466 | 123.856 | 52.99 | No |
| obstruction | high | 266.617 | 123.856 | 53.55 | No |

This bound remains optimistic and excludes the common scheduled start stop, junctions, acceleration and communication. It is not an achievable performance prediction.
