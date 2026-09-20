#!/usr/bin/env bash
set -u

export OMPI_MCA_osc=pt2pt
solver=/mnt/d/SU2/v8.5.0/bin/SU2_CFD
cases=(ideal_sst_hllc ideal_sst_slau2 ideal_sa_hllc lut_sst_hllc lut_sa_hllc)

for case_name in "${cases[@]}"; do
  echo "=== ${case_name} settle ==="
  start=$(date +%s)
  mpirun -np 6 "$solver" "${case_name}_settle.cfg" > "${case_name}/settle.log" 2>&1
  return_code=$?
  elapsed=$(($(date +%s) - start))
  echo "${case_name} rc=${return_code} seconds=${elapsed}"
  grep -E "Exit Success|Error in|rms\[Rho\]|nonphysical|NaN" "${case_name}/settle.log" | tail -4 || true
done
