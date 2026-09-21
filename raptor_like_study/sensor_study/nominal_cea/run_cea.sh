#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
CEA_DIR="$ROOT/tools/cea-3.3.4"
CASE_DIR="$ROOT/sensor_study/nominal_cea"

chmod +x "$CEA_DIR/cea-linux"
cd "$CEA_DIR"
"$CEA_DIR/cea-linux" "$CASE_DIR/equilibrium.inp" >/dev/null
"$CEA_DIR/cea-linux" "$CASE_DIR/frozen_throat.inp" >/dev/null
echo "CEA nominal equilibrium and frozen-at-throat cases completed"
