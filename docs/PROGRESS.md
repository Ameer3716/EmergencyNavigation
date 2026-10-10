# Progress

Completed 360 primary matched runs and 90 no-preemption waiting-time controls, plus 360 separate controlled-obstruction runs and 18 separate red-signal checks. See VERIFICATION.md for measured counts and intervals, METHODOLOGY.md for model assumptions, and CLIENT_BASELINE_COMPARISON.md for direct comparisons with FogCloudAStar. The selected 20 percent response target is exceeded under obstruction at every density; ordinary traffic improves by a smaller margin. The ordinary and obstruction experiments are reported separately. Previous submission evidence is preserved in archive_20261010_before_advance_priority/. Historical comparison CSVs include only versions whose source data are available locally.

## Supplementary route communication and signal validation

The seven headline metrics and the 450-run main matrix are unchanged. Separate route-transaction metrics are derived from original raw scalars, and 18 isolated short-notice red-signal runs validate positive waiting and safe priority transitions. Definitions, confidence intervals, measured tables, and limitations are in [SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).

## Controlled incident and matched recovery evidence

A separate 360-run matrix uses a physical C1C2 stopped queue after initial route selection, with the same incident input and original trips for every algorithm. FCD evidence verifies the incident; all delivered-alert runs must reach the destination. Matched fault recovery is also reported from the original batch. Actual tables, confidence intervals and limits are in [REQUIREMENTS_EVIDENCE.md](REQUIREMENTS_EVIDENCE.md). Shared EM delivery metrics keep their definitions and cannot demonstrate routing superiority. Graph labels retain three decimals for response and waiting; SUMO motion remains sampled every 500 ms.

## Direct comparison with the Fog/Cloud baseline

[CLIENT_BASELINE_COMPARISON.md](CLIENT_BASELINE_COMPARISON.md) reports response, signal waiting, decision latency, excess travel delay above free flow, and actual Fog route request counts. The latter two are supporting metrics derived from recorded scalars, not substitutes for the seven headline metrics. Ordinary traffic and controlled obstruction have separate matched-seed estimates and 95% intervals. The framework comparison includes advance signal requests in dynamic Mist and reactive requests in Fog/static Mist; both use the same safety controller and bounded retry mechanism. It is not an isolated comparison of A* computation alone.
