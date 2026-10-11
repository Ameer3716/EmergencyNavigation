# Simulation storage

Simulation results are kept without deleting historical evidence or reducing
their precision. Text data can be compressed losslessly by the filesystem.

## Completed result copies

The batch runner publishes scalar, vector and vector-index files using hard
links when the run and raw-result folders use the same filesystem. Both paths
remain available, but share one physical copy. Cross-filesystem publishing
falls back to a normal copy. Before rerunning a previously completed case, the
runner gives its working outputs private copies so earlier raw evidence cannot
be changed by the rerun.

For experiments already running with the previous runner, run inside WSL:

```bash
python3 /mnt/d/Codex/EmergencyNavigation/scripts/deduplicate_policy_storage.py --watch
```

This only replaces byte-identical result copies for completed cases in the four
policy tuning/report workspaces. It skips incomplete or different files and
records saved bytes in `artifacts/policy_validation/storage_savings.json`.
No raw log, CSV, graph, simulation input or binary is edited.

## Windows storage

Lossless NTFS compression is enabled for historical project result, log,
simulation and archive folders. Readers continue to use the same paths.
The WSL virtual disk must not be compressed with NTFS compression.

Freeing files inside WSL makes space available for new Linux files. It does not
necessarily reduce the Windows size of `D:\WSL\opp_env\ext4.vhdx` immediately.
Reclaiming those blocks on Windows requires an offline virtual-disk compaction
after the simulation and analysis processes have finished. Do not shut down or
compact the active WSL disk during a batch.
