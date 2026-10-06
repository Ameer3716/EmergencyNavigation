# EmergencyNavigation development guide

The project uses SUMO 1.18.0, OMNeT++ 6.3.0, and Veins 5.3.1. The main comparison is four configurations times three densities times 30 seeds (360 runs), plus 90 NoPreemptionBaseline runs shown only for traffic-light waiting. The current parameters are 400 m radio range, 0 ms telemetry delay, 500 ms watchdog, and 100 ms metric accumulation with 500 ms underlying SUMO updates. Eight fixed independently sampled seeds receive 900 ms controlled initial Mist stalls in all Mist configurations. Never describe these as organic fallback or measured OBU performance.

Build with scripts/build.sh, run with scripts/run_batch_env.sh, process with analysis/process_results.py --batch --require-all, extract fallback evidence, then generate reports and audit. Previous evidence is in archive_20261005_before_audit_fixes/, archive_20261005_400m_telemetry20/ and archive_raw_20261001_650m/. Do not manually edit raw logs, result CSVs, or graphs. Regenerate them from the source pipeline. Keep the no-preemption control out of every summary and plot except traffic-light waiting.

Supplementary route transactions are derived from raw scalars by analysis/supplemental_validation.py. The separate 18-run red-signal stress suite uses scripts/run_signal_validation.py; its protected red phase and deliberately late priority requests must not be mixed into the main batch.

The separate incident matrix uses scripts/run_congestion_validation.py and analysis/congestion_validation.py. Keep incident and ordinary results separate; never gate data acceptance on effect size or significance. Incident FCD verifies physical queues.
