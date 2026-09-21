#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 9 ]]; then
    echo "Usage: $0 ARTIFACT_DIR PA_PA NPR T0_K WALL TI LENGTH_M MESH SWEEP" >&2
    echo "WALL: adiabatic|280|300|320; MESH: coarse|medium|fine; SWEEP: startup|shutdown" >&2
    exit 2
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CASE_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../../.." && pwd)
ARTIFACT_DIR=$1
shift
if [[ $ARTIFACT_DIR != /* ]]; then
    echo "Artifact directory must be absolute." >&2
    exit 2
fi
mkdir -p -- "$ARTIFACT_DIR"
ARTIFACT_DIR=$(cd -- "$ARTIFACT_DIR" && pwd)
case "$ARTIFACT_DIR/" in
    "$REPO_ROOT/"*) echo "Artifacts must remain outside the repository." >&2; exit 2 ;;
esac

source "$REPO_ROOT/raptor_like_study/eilmer/eilmer5-env.sh"
python3 "$REPO_ROOT/raptor_like_study/scripts/check_model_readiness.py" \
    cold_n2_validation --stage screen

cp -- "$SCRIPT_DIR/gas-model.inp" "$SCRIPT_DIR/prepare_run.py" \
    "$SCRIPT_DIR/transient.lua" "$SCRIPT_DIR/postprocess_wall.py" \
    "$CASE_DIR/results/physical_separation_fig7a.csv" \
    "$CASE_DIR/mesh_family/grid.lua" \
    "$REPO_ROOT/DLR_PAR_full_contour.csv" \
    "$REPO_ROOT/raptor_like_study/cases/dlr_par_geometry/prepare_contour.py" \
    "$ARTIFACT_DIR/"
cd -- "$ARTIFACT_DIR"

python3 prepare_run.py --pa-pa "$1" --npr "$2" --t0-k "$3" \
    --wall "$4" --turbulence-intensity "$5" --length-scale-m "$6" \
    --mesh "$7" --sweep "$8" \
    --lua-output run_parameters.lua --json-output run_parameters.json
python3 prepare_contour.py DLR_PAR_full_contour.csv --output-dir . \
    --resample-spacing-m 5.0e-5 --audit contour_audit.json > prepare-contour.log
lmr prep-gas -i gas-model.inp -o gas-model.lua 2>&1 | tee prep-gas.log
DLR_MESH_LEVEL="$7" lmr prep-grid --job=grid.lua 2>&1 | tee prep-grid.log
lmr prep-sim --job=transient.lua 2>&1 | tee prep-sim.log

started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
started_epoch=$(date +%s)
set +e
timeout --signal=TERM --kill-after=30s 60m \
    mpirun --bind-to core -np 6 lmr-mpi-run 2>&1 | tee solver.log
solver_pipeline_status=("${PIPESTATUS[@]}")
set -e
solver_status=${solver_pipeline_status[0]}
if [[ $solver_status -ne 0 ]]; then
    echo "Solver failed or reached the 60-minute hard stop (status=$solver_status)." >&2
    exit "$solver_status"
fi
lmr snapshot2vtk --all 2>&1 | tee snapshot2vtk.log
python3 postprocess_wall.py --artifact-dir "$ARTIFACT_DIR" \
    --targets physical_separation_fig7a.csv \
    --output screen_metrics.json --profile-output wall_profile.csv
ended_epoch=$(date +%s)

python3 - "$ARTIFACT_DIR" "$started_utc" "$((ended_epoch-started_epoch))" \
    "$(git -C "$DGD_REPO" rev-parse HEAD)" <<'PY'
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
parameters = json.loads((root / "run_parameters.json").read_text())
payload = {
    "case_id": "dlr_par_cold_n2_internal_screen_v1",
    "classification": "provisional_internal_domain_screen_not_validation",
    "started_utc": sys.argv[2],
    "ended_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "solver_wall_seconds": int(sys.argv[3]),
    "eilmer_commit": sys.argv[4],
    "mpi_ranks": 6,
    "parameters": parameters,
    "external_plume_modeled": False,
    "physics_accepted": False,
    "training_eligible": False,
    "artifact_directory": str(root),
    "hostname": platform.node(),
}
(root / "provenance.json").write_text(json.dumps(payload, indent=2) + "\n")
PY

echo "Cold-N2 internal-domain screen completed; physics remains unaccepted."
