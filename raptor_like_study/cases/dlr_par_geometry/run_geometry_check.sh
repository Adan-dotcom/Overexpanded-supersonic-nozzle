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

cp -- "$REPO_ROOT/DLR_PAR_full_contour.csv" "$SCRIPT_DIR/prepare_contour.py" \
    "$SCRIPT_DIR/grid.lua" "$SCRIPT_DIR/audit_grid.py" "$ARTIFACT_DIR/"
cd -- "$ARTIFACT_DIR"

started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
started_epoch=$(date +%s)
eilmer_commit=$(git -C "$DGD_REPO" rev-parse HEAD)

python3 prepare_contour.py DLR_PAR_full_contour.csv --output-dir . \
    --audit contour_audit.json 2>&1 | tee prepare-contour.log
lmr prep-grid --job=grid.lua 2>&1 | tee prep-grid.log
python3 audit_grid.py lmrsim/grid --output grid_quality.json \
    --plot grid_overview.png 2>&1 | tee audit-grid.log

ended_epoch=$(date +%s)
ended_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
contour_sha256=$(python3 -c 'import json; print(json.load(open("contour_audit.json"))["source_sha256"])')
grid_lua_sha256=$(sha256sum grid.lua | awk '{print $1}')
python3 - provenance.json <<PY
import json
import platform
import sys
from pathlib import Path

payload = {
    "case_id": "dlr_par_geometry_screen_v1",
    "classification": "geometry_and_mesh_quality_only_not_flow_validation",
    "started_utc": "$started_utc",
    "ended_utc": "$ended_utc",
    "wall_seconds": $((ended_epoch-started_epoch)),
    "eilmer_commit": "$eilmer_commit",
    "contour_sha256": "$contour_sha256",
    "grid_lua_sha256": "$grid_lua_sha256",
    "cell_count": 92160,
    "block_count": 6,
    "solver_executed": False,
    "mpi_ranks_used": 0,
    "hostname": platform.node(),
    "platform": platform.platform(),
    "artifact_directory": "$ARTIFACT_DIR",
    "source_repository": "$REPO_ROOT",
}
Path(sys.argv[1]).write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
PY

echo "DLR-PAR geometry and grid-quality screen passed."
