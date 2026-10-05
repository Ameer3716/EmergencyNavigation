#!/usr/bin/env bash
set -eo pipefail
source /home/opp_env/workspace/omnetpp-6.3.0/setenv
set -u
export OPP_ENV_VERSION=0.36.1
export OMNETPP_ROOT=/home/opp_env/workspace/omnetpp-6.3.0
export VEINS_ROOT=/home/opp_env/workspace/veins-5.3.1
if ! command -v make >/dev/null 2>&1; then
  for candidate in /nix/store/*-clang-wrapper-19.1.7/bin; do PATH="$candidate:$PATH"; break; done
  for candidate in /nix/store/*-lld-19.1.7/bin; do PATH="$candidate:$PATH"; break; done
  for candidate in /nix/store/*-gnumake-4.4.1/bin; do PATH="$candidate:$PATH"; break; done
  for candidate in /nix/store/*-ccache-*/bin; do PATH="$candidate:$PATH"; break; done
  export PATH
fi
project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir/src"
opp_makemake -f --make-so --deep \
  -I . -I "$VEINS_ROOT/src" -L "$VEINS_ROOT/src" -l veins
make -j4 MODE=release
