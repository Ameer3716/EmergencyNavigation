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

if ! python3 -c 'import socket; s = socket.socket(); s.settimeout(0.5); result = s.connect_ex(("127.0.0.1", 9998)); s.close(); raise SystemExit(result != 0)'; then
    echo "Starting veins_launchd on port 9998..."
    python3 "$VEINS_ROOT/bin/veins_launchd" -d -p 9998 -vv -c "$SUMO_HOME/bin/sumo" -L "$project_dir/artifacts/logs/grid-launchd.log"
fi

cd "$project_dir"
python3 "$project_dir/scripts/run_batch.py" "$@"
