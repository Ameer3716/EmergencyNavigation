# Installation and reproduction

The installed stack is opp_env WSL, SUMO 1.18.0, OMNeT++ 6.3.0, and Veins 5.3.1. Run from the project directory in PowerShell:

```powershell
wsl -d opp_env -- bash /mnt/d/Codex/EmergencyNavigation/scripts/build.sh
wsl -d opp_env -- bash /mnt/d/Codex/EmergencyNavigation/scripts/run_batch_env.sh --force --jobs 4
python analysis/process_results.py --batch --require-all
python analysis/extract_fallback_evidence.py
python scripts/verify_response_times.py
python scripts/generate_final_graph.py
python scripts/write_final_reports.py
python scripts/validate_timing_evidence.py
python scripts/generate_reviewed_submission.py
python scripts/audit_batch.py
python -m unittest discover -s tests
python scripts/package_reviewed_submission.py --refresh
```

The default runner creates 450 simulations: 360 primary comparisons and 90 waiting controls. To inspect a small isolated sample, add `--seeds 1 4 --artifact-root /mnt/d/Codex/EmergencyNavigation/scratch/sample` to the runner, then process with `--batch --no-graphs --artifact-root scratch/sample`. A fresh run must not be mixed with old parameter outputs. Raw files are in results/raw, event logs and binary provenance manifests are in artifacts/logs/batch, and processed results are in results/processed.

## Reproduce the isolated red signal validation

Use a fresh workspace so the main batch stays unchanged. Inside the configured WSL environment:

```bash
bash scripts/run_batch_env.sh --signal-validation --workspace /home/opp_env/signal_validation_new
python analysis/supplemental_validation.py --signal-root /home/opp_env/signal_validation_new
```

The runner uses the existing binary and matched seed trips. Retain the complete workspace and copy it to artifacts/signal_validation before packaging. Route byte throughput is not inferred from absent packet logs.

## Reproduce the controlled incident comparison

```bash
bash scripts/run_batch_env.sh --congestion-validation --workspace /home/opp_env/incident_new --jobs 4
python analysis/congestion_validation.py --incident-root /home/opp_env/incident_new
```

First screen seed 1 at all densities in a separate workspace with --seeds 1. Retain the complete final workspace and copy it to artifacts/congestion_validation before packaging. The 360-run final matrix uses all 30 seeds without selection based on outcomes.
