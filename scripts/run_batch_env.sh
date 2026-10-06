#!/usr/bin/env bash
set -eo pipefail
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

source /home/opp_env/workspace/omnetpp-6.3.0/setenv
export OPP_ENV_VERSION=0.36.1
export OMNETPP_ROOT=/home/opp_env/workspace/omnetpp-6.3.0
export VEINS_ROOT=/home/opp_env/workspace/veins-5.3.1
export SUMO_HOME=/home/opp_env/sumo118_pkg/sumo
export PATH="$SUMO_HOME/bin:$PATH"
mkdir -p "$project_dir/artifacts/logs"

# Inspect listening sockets without opening an empty launchd connection.
# Veins 5.3.1 waits forever for a message header on such a connection.
if ! python3 -c 'from pathlib import Path; rows = Path("/proc/net/tcp").read_text().splitlines()[1:]; raise SystemExit(not any(r.split()[1].endswith(":270E") and r.split()[3] == "0A" for r in rows))'; then
    echo "Starting veins_launchd on port 9998..."
    python3 "$VEINS_ROOT/bin/veins_launchd" -d -p 9998 -vv -c "$SUMO_HOME/bin/sumo" -L "$project_dir/artifacts/logs/grid-launchd.log"
fi

cd "$project_dir"
if [ "${1:-}" = "--congestion-validation" ]; then
    shift
    python3 "$project_dir/scripts/run_congestion_validation.py" "$@"
elif [ "${1:-}" = "--signal-validation" ]; then
    shift
    python3 "$project_dir/scripts/run_signal_validation.py" "$@"
else
    python3 "$project_dir/scripts/run_batch.py" "$@"
fi
