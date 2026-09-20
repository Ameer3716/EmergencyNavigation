# Installation

Installation is in progress. The machine audit and current state are recorded in `PROGRESS.md`.

The requested stack is OMNeT++ 6.3.0, Veins 5.3.1, and SUMO 1.18.0. INET 4.6.0 is optional because native Veins IEEE 802.11p is the intended radio model. The official Veins 5.3.1 compatibility list names SUMO 1.18.0 but does not name OMNeT++ 6.3.0. Therefore the stock Veins example build and run are mandatory compatibility checks before custom development. Source: https://veins.car2x.org/download/ .

OMNeT++ recommends `opp_env` for versioned installs under WSL2. Source: https://omnetpp.org/download-items/omnetpp/omnetpp-630.html . Installation commands and any required compatibility patch will be documented after they execute successfully.

Observed successful host setup:

```powershell
wsl --install -d Ubuntu-24.04 --no-launch
curl.exe -L --fail --output D:\codex\opp_env.wsl https://github.com/omnetpp/opp_env/releases/download/wsl/opp_env.wsl
wsl --install --from-file D:\codex\opp_env.wsl --no-launch
wsl -d opp_env -- bash -lc 'opp_env --version'
```

The official `opp_env` image reports version `0.36.1.20260515`. It resolves Veins 5.3.1, OMNeT++ 6.3.0, and INET 4.6.0. A release-only installation is in progress using:

```bash
cd ~/workspace
opp_env install veins-5.3.1 omnetpp-6.3.0 --build-modes release --smoke-test
```

The exact SUMO binary was installed from `eclipse-sumo==1.18.0` into `/home/opp_env/sumo118_pkg`; `sumo --version` reports 1.18.0. The Veins launcher must be pointed at `/home/opp_env/sumo118_pkg/sumo/bin/sumo` explicitly because the `opp_env` Nix environment otherwise exposes SUMO 1.22.0. Native Veins 802.11p remains the planned radio model even though `opp_env` compiles its optional INET integration as a dependency.

The core Veins example passed by starting the launcher with the explicit SUMO binary, then running `scripts/verify-veins-example.sh` in an `opp_env run veins-5.3.1 omnetpp-6.3.0 --no-deps --no-build --build-modes release` session. The output and launcher transcript are saved in `artifacts/logs/`. The `opp_env` WSL image did not automount Windows drives; `/mnt/d` was created and mounted with `mount -t drvfs D: /mnt/d` as root before using project scripts and log paths.
