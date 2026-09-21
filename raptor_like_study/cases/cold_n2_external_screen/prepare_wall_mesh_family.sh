#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 ARTIFACT_ROOT" >&2
    exit 2
fi

artifact_root="$1"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
case_dir="$repo_dir/raptor_like_study/cases/cold_n2_external_screen"
source "$repo_dir/raptor_like_study/eilmer/eilmer5-env.sh"

for level in wall-coarse wall-medium wall-fine; do
    artifact_dir="$artifact_root/$level"
    mkdir -p "$artifact_dir"
    cp "$case_dir/grid.lua" "$artifact_dir/"
    python "$repo_dir/raptor_like_study/cases/dlr_par_geometry/prepare_contour.py" \
        "$repo_dir/DLR_PAR_full_contour.csv" \
        --output-dir "$artifact_dir" --audit "$artifact_dir/contour_audit.json" \
        --resample-spacing-m 0.0005
    python "$case_dir/prepare_run.py" \
        --stage 3 --npr 35 --mesh-level "$level" \
        --lua-output "$artifact_dir/run_parameters.lua" \
        --mesh-lua-output "$artifact_dir/mesh_parameters.lua" \
        --json-output "$artifact_dir/run_parameters.json"
    (
        cd "$artifact_dir"
        lmr prep-grid --job=grid.lua
    )
    python "$case_dir/audit_wall_mesh.py" \
        --artifact-dir "$artifact_dir" --output "$artifact_dir/mesh-audit.json"
done
