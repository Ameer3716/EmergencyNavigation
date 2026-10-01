# Installation and reproduction

Use the provided `opp_env` WSL distribution with OMNeT++ 6.3.0, Veins 5.3.1, and SUMO 1.18.0. Source code is in `src/`, SUMO geometry and OMNeT++ configuration are in `simulations/grid/`, and the runner is `scripts/run_batch_env.sh`.

1. Build `src/libsrc.so` in the `opp_env` environment using `scripts/build.sh` or the environment's OMNeT++ make workflow.
2. Run the four configurations on all densities and 30 matched seeds:

```bash
wsl -d opp_env /mnt/d/Codex/EmergencyNavigation/scripts/run_batch_env.sh --configs FogCloudAStar MistAStar MistDynamicAStar MistDynamicFogFallback --densities low medium high --seed-start 1 --seed-end 30 --force
```

3. Process and verify the full 360-run matrix:

```powershell
python analysis/process_results.py --batch --require-all
python analysis/extract_fallback_evidence.py
python scripts/generate_final_graph.py
python scripts/write_final_reports.py
python scripts/audit_batch.py
python scripts/generate_reviewed_submission.py
python scripts/package_reviewed_submission.py
```

The processor checks that all 360 expected run keys are present and every `.sca` file records the current 400 m and 20 ms parameters. Raw `.sca`, `.vec`, and `.vci` outputs are in `results/raw/`; run logs are in `artifacts/logs/batch/`; plots are in `results/graphs/`. Historical 650 m data is preserved separately in `archive_raw_20261001_650m/` and is excluded from the current processor and graphs.
