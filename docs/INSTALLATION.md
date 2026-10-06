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
