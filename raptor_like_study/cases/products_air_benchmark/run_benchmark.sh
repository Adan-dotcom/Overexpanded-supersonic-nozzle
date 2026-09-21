#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 ABSOLUTE_ARTIFACT_DIRECTORY" >&2
    exit 2
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
ARTIFACT_DIR=$1

if [[ $ARTIFACT_DIR != /* ]]; then
    echo "Artifact directory must be an absolute path." >&2
    exit 2
fi
mkdir -p -- "$ARTIFACT_DIR"
ARTIFACT_DIR=$(cd -- "$ARTIFACT_DIR" && pwd)
case "$ARTIFACT_DIR/" in
    "$REPO_ROOT/"*)
        echo "Artifact directory must be outside the repository: $REPO_ROOT" >&2
        exit 2
        ;;
esac

source "$REPO_ROOT/raptor_like_study/eilmer/eilmer5-env.sh"
python3 "$REPO_ROOT/raptor_like_study/scripts/check_model_readiness.py" \
    products_air_benchmark --stage screen

cp -- "$SCRIPT_DIR/gas-model.inp" "$SCRIPT_DIR/grid.lua" \
    "$SCRIPT_DIR/transient.lua" "$SCRIPT_DIR/postprocess.py" \
    "$SCRIPT_DIR/validate_gas_model.py" \
    "$ARTIFACT_DIR/"

cd -- "$ARTIFACT_DIR"

started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
started_epoch=$(date +%s)
eilmer_commit=$(git -C "$DGD_REPO" rev-parse HEAD)

lmr prep-gas -i gas-model.inp -o gas-model.lua 2>&1 | tee prep-gas.log
python3 validate_gas_model.py gas-model.lua --output gas_model_validation.json
lmr prep-grid --job=grid.lua 2>&1 | tee prep-grid.log
lmr prep-sim --job=transient.lua 2>&1 | tee prep-sim.log

set +e
solver_started_epoch=$(date +%s)
timeout --signal=TERM --kill-after=30s 60m \
    mpirun --bind-to core -np 6 lmr-mpi-run 2>&1 | tee solver.log
solver_pipeline_status=("${PIPESTATUS[@]}")
solver_ended_epoch=$(date +%s)
set -e
solver_status=${solver_pipeline_status[0]}
if [[ $solver_status -ne 0 ]]; then
    echo "Solver failed or hit the 60-minute hard stop (status=$solver_status)." >&2
    exit "$solver_status"
fi

lmr snapshot2vtk --all 2>&1 | tee snapshot2vtk.log
python3 postprocess.py --artifact-dir "$ARTIFACT_DIR" \
    --output "$ARTIFACT_DIR/benchmark_metrics.json"
python3 "$REPO_ROOT/raptor_like_study/scripts/evaluate_physics_gate.py" \
    "$ARTIFACT_DIR/benchmark_metrics.json" --stage screen \
    --output "$ARTIFACT_DIR/benchmark_acceptance.json"

ended_epoch=$(date +%s)
ended_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
gas_input_sha256=$(sha256sum gas-model.inp | awk '{print $1}')
gas_model_sha256=$(sha256sum gas-model.lua | awk '{print $1}')
python3 - "$ARTIFACT_DIR/provenance.json" <<PY
import json
import platform
import sys
from pathlib import Path

payload = {
    "case_id": "products_air_benchmark_v1",
    "started_utc": "$started_utc",
    "ended_utc": "$ended_utc",
    "wall_seconds": $((ended_epoch-started_epoch)),
    "solver_wall_seconds": $((solver_ended_epoch-solver_started_epoch)),
    "eilmer_commit": "$eilmer_commit",
    "gas_input_sha256": "$gas_input_sha256",
    "generated_gas_model_sha256": "$gas_model_sha256",
    "cell_count": 36000,
    "block_count": 6,
    "mpi_ranks": 6,
    "hostname": platform.node(),
    "platform": platform.platform(),
    "artifact_directory": "$ARTIFACT_DIR",
    "source_repository": "$REPO_ROOT",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
PY

python3 - "$ARTIFACT_DIR/benchmark_acceptance.json" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
if not result.get("screening_survivor", False):
    raise SystemExit("Benchmark completed but failed one or more screen gates.")
print("Products/air benchmark passed every screening gate.")
PY
