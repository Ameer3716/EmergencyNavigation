# Progress and verification

## Stage 1: machine audit — complete

Audit date: 2026-09-20, Windows host in Asia/Karachi timezone.

| Component | Observed state |
| --- | --- |
| Windows | Windows 10 Pro, 64-bit (`Get-ComputerInfo`); WSL 2.7.12.0 kernel 6.18.33.2 |
| WSL distributions | None installed (`wsl --list --verbose`) |
| Git | 2.55.0.windows.4 |
| Python | 3.14.7 |
| SUMO | Not found on PATH |
| OMNeT++ | `opp_run` not found on PATH |
| Veins | Not present in empty project workspace |
| opp_env | Not found on PATH |
| INET | Not found; optional unless needed directly |

The version-command transcript is in `artifacts/logs/machine-audit.txt`. This audit establishes that the requested Veins example and custom simulations cannot yet run.

## Stage 2: repository structure — complete

Git repository and required directories created and committed as `ed239d8` and `28d04ce`. No simulation validation tests have passed yet.

## Stage 3: simulator installation — in progress

Ubuntu 24.04.5 LTS installed through `wsl --install -d Ubuntu-24.04 --no-launch`; launch and `/etc/os-release` inspection succeeded. The official `opp_env.wsl` image was downloaded and installed through `wsl --install --from-file D:\codex\opp_env.wsl --no-launch`. Its `opp_env --version` command reports `0.36.1.20260515`. The image is also a WSL2 distribution. Both launches reported a WSL NAT configuration fallback to VirtioProxy; neither failed.

An `opp_env` workspace was initialized at `/home/opp_env/workspace`. Installation of `veins-5.3.1` and `omnetpp-6.3.0` is running with `--smoke-test`. Dependency resolution selected `inet-4.6.0` automatically. This does not change the chosen native Veins radio model. `opp_env info veins-5.3.1` explicitly lists OMNeT++ 6.3.0 and INET 4.6.0 as compatible requirements, and its Nix environment supplies SUMO without an independently selectable `sumo-1.18.0` project. The exact SUMO 1.18.0 runtime must still be installed and verified.
