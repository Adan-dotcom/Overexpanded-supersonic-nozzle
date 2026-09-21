#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 ABSOLUTE_ARTIFACT_DIRECTORY" >&2
    exit 2
fi

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
CASE_DIR=$(cd -- "$SCRIPT_DIR/.." && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../../.." && pwd)
ARTIFACT_DIR=$1

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

started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
eilmer_commit=$(git -C "$DGD_REPO" rev-parse HEAD)

for level in coarse medium fine; do
    level_dir="$ARTIFACT_DIR/$level"
    mkdir -p -- "$level_dir"
    cp -- "$REPO_ROOT/DLR_PAR_full_contour.csv" \
        "$REPO_ROOT/raptor_like_study/cases/dlr_par_geometry/prepare_contour.py" \
        "$REPO_ROOT/raptor_like_study/cases/dlr_par_geometry/audit_grid.py" \
        "$SCRIPT_DIR/grid.lua" "$level_dir/"
    (
        cd -- "$level_dir"
        python3 prepare_contour.py DLR_PAR_full_contour.csv --output-dir . \
            --resample-spacing-m 5.0e-5 \
            --audit contour_audit.json > prepare-contour.log
        DLR_MESH_LEVEL=$level lmr prep-grid --job=grid.lua > prep-grid.log 2>&1
        case "$level" in
            coarse) expected_cells=51840 ;;
            medium) expected_cells=103680 ;;
            fine) expected_cells=207360 ;;
        esac
        python3 audit_grid.py lmrsim/grid --output grid_quality.json \
            --plot grid_overview.png --expected-cells "$expected_cells" \
            > audit-grid.log 2>&1
    )
done

python3 - "$ARTIFACT_DIR" "$started_utc" "$eilmer_commit" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(sys.argv[1])
levels = {}
for name in ("coarse", "medium", "fine"):
    quality = json.loads((root / name / "grid_quality.json").read_text())
    metrics = quality["mesh_quality"]
    levels[name] = {
        "cells": quality["cell_count"],
        "blocks": quality["block_count"],
        "all_checks_pass": quality["all_checks_pass"],
        "minimum_cell_area_m2": metrics["signed_cell_area_m2"]["min"],
        "maximum_aspect_ratio": metrics["edge_length_aspect_ratio"]["max"],
        "maximum_adjacent_area_ratio": metrics["adjacent_cell_area_ratio"]["max"],
        "minimum_wall_spacing_m": metrics["wall_adjacent_vertex_spacing_m"]["min"],
        "maximum_wall_spacing_m": metrics["wall_adjacent_vertex_spacing_m"]["max"],
    }
payload = {
    "case_id": "dlr_par_cold_n2_mesh_family_v1",
    "classification": "geometry_screen_pending_flow_based_y_plus_qualification",
    "started_utc": sys.argv[2],
    "ended_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "eilmer_commit": sys.argv[3],
    "mpi_ranks_planned": 6,
    "levels": levels,
    "passes_geometry_gate": all(v["all_checks_pass"] and v["blocks"] == 6 for v in levels.values()),
    "flow_was_solved": False,
    "wall_y_plus_evaluated": False,
    "physics_accepted": False,
    "training_eligible": False,
    "heavy_artifact_directory": str(root),
}
(root / "mesh_family_summary.json").write_text(json.dumps(payload, indent=2) + "\n")
if not payload["passes_geometry_gate"]:
    raise SystemExit("Mesh family failed the geometry gate")
PY

echo "Cold-N2 mesh-family geometry screen passed."
