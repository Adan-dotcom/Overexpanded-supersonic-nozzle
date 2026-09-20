#!/usr/bin/env bash
set -euo pipefail

CASE_DIR="/mnt/d/PRUEBA SU2_2026/raptor_like_study/sensor_study/nominal_rans"
SU2="/mnt/d/SU2/v8.5.0/bin/SU2_CFD"
NPROC="${1:-4}"

cd "$CASE_DIR"
export OMPI_MCA_osc=pt2pt
mpirun --allow-run-as-root -np "$NPROC" "$SU2" coarse_npr100.cfg
