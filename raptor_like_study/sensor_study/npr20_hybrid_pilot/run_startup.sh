#!/usr/bin/env bash
set -euo pipefail
export OMPI_MCA_osc=pt2pt
mpirun --allow-run-as-root -np 4 /mnt/d/SU2/v8.5.0/bin/SU2_CFD npr20_startup.cfg
