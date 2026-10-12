> Retained original-policy experiment. See [POLICY_VALIDATION.md](POLICY_VALIDATION.md) for the new matched-policy results and unmet requirements.

# Progress

Completed 360 primary matched runs and 90 no-preemption waiting-time controls, plus 360 separate controlled-obstruction runs and 18 separate red-signal checks. See VERIFICATION.md for measured counts and intervals, METHODOLOGY.md for model assumptions, and CLIENT_BASELINE_COMPARISON.md for direct comparisons with FogCloudAStar. The selected 20 percent response target is exceeded under obstruction at every density; ordinary traffic improves by a smaller margin. The ordinary and obstruction experiments are reported separately. Previous submission evidence is preserved in archive_20261010_before_advance_priority/. Historical comparison CSVs include only versions whose source data are available locally.

## Supplementary route communication and signal validation

The seven headline metrics and the 450-run main matrix are unchanged. Separate route-transaction metrics are derived from original raw scalars, and 18 isolated short-notice red-signal runs validate positive waiting and safe priority transitions. Definitions, confidence intervals, measured tables, and limitations are in [SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).

## Controlled incident and matched recovery evidence

A separate 360-run matrix uses a physical C1C2 stopped queue after initial route selection, with the same incident input and original trips for every algorithm. FCD evidence verifies the incident; all delivered-alert runs must reach the destination. Matched fault recovery is also reported from the original batch. Actual tables, confidence intervals and limits are in [REQUIREMENTS_EVIDENCE.md](REQUIREMENTS_EVIDENCE.md). Shared EM delivery metrics keep their definitions and cannot demonstrate routing superiority. Graph labels retain three decimals for response and waiting; SUMO motion remains sampled every 500 ms.

## Direct comparison with the Fog/Cloud baseline

[CLIENT_BASELINE_COMPARISON.md](CLIENT_BASELINE_COMPARISON.md) reports response, signal waiting, decision latency, excess travel delay above free flow, and actual Fog route request counts. The latter two are supporting metrics derived from recorded scalars, not substitutes for the seven headline metrics. Ordinary traffic and controlled obstruction have separate matched-seed estimates and 95% intervals. The framework comparison includes advance signal requests in dynamic Mist and reactive requests in Fog/static Mist; both use the same safety controller and bounded retry mechanism. It is not an isolated comparison of A* computation alone.

## Matched-policy extension (2026-10-10)

The new isolated experiment contains 630 ordinary and 540 obstruction runs, plus 180 held-out candidate runs on seeds 101–110. Previous tables in this file describe the retained original-policy experiment. New matched-policy estimates and explicit unmet requirements are in [POLICY_VALIDATION.md](POLICY_VALIDATION.md). The fixed design is in [POLICY_EXPERIMENT_PLAN.md](POLICY_EXPERIMENT_PLAN.md); the prior timing and zero-wait diagnosis is in [DIAGNOSIS.md](DIAGNOSIS.md). The selected settings are frozen in results/policy_validation/selection.json. No artificial waiting or outcome gate is used.

## Cancelled experiment completed evidence

The new experiment was cancelled before reported seeds began. COMPLETED_PILOT_RESULTS.md and results/next_validation/completed_pilots contain only 109 completed held-out pilot runs, with 11 unfinished or unstarted cases excluded and coverage disclosed. The audit validates included evidence, not a complete scheduled matrix or performance success. Preserved reported results remain in POLICY_VALIDATION.md.

## Unified project submission

The Word submission now presents the project from the beginning: overview, system components, operating process, routing frameworks, signal and fallback mechanisms, experimental settings, metric definitions, complete matched results, completed pilot evidence, ablations and conclusions. The reproducible builder is scripts/generate_complete_project_report.py. Its graph gallery covers every available matched and completed-pilot metric, with the seven primary metrics first and a simple explanation for every panel. Earlier results remain in the historical submission. The experiment remains cancelled and no simulation was restarted for this document revision.
