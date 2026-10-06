# Progress

Completed 360 primary matched runs and 90 no-preemption waiting-time controls. See VERIFICATION.md for measured counts and intervals, and METHODOLOGY.md for controlled fault labels and signal safety timing. Pre-fix outputs are preserved in archive_20261005_before_audit_fixes/. Separate named comparisons retain the 400m telemetry20 and archived 650m versions; they change multiple model settings and do not isolate a telemetry effect.

## Supplementary route communication and signal validation

The seven headline metrics and the 450-run main matrix are unchanged. Separate route-transaction metrics are derived from original raw scalars, and 18 isolated short-notice red-signal runs validate positive waiting and safe priority transitions. Definitions, confidence intervals, measured tables, and limitations are in [SUPPLEMENTAL_VALIDATION.md](SUPPLEMENTAL_VALIDATION.md).

## Controlled incident and matched recovery evidence

A separate 360-run matrix uses a physical C1C2 stopped queue after initial route selection, with the same incident input and original trips for every algorithm. FCD evidence verifies the incident; all delivered-alert runs must reach the destination. Matched fault recovery is also reported from the original batch. Actual tables, confidence intervals and limits are in [REQUIREMENTS_EVIDENCE.md](REQUIREMENTS_EVIDENCE.md). Shared EM delivery metrics keep their definitions and cannot demonstrate routing superiority. Graph labels retain three decimals for response and waiting; SUMO motion remains sampled every 500 ms.
