#!/usr/bin/env bash
set -euo pipefail

CASE_ID="${1:-case_0001}"
NPROC="${2:-1}"
ROOT="/mnt/d/PRUEBA SU2_2026/raptor_like_study"
CASE_DIR="$ROOT/cases/su2/$CASE_ID"
SU2="/mnt/d/SU2/v8.5.0/bin/SU2_CFD"

cd "$CASE_DIR"
export OMPI_MCA_osc=pt2pt
if [[ "$NPROC" -gt 1 ]]; then
  mpirun --allow-run-as-root -np "$NPROC" "$SU2" nozzle.cfg
else
  "$SU2" nozzle.cfg
fi
