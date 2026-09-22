#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: $0 STAGE NPR ARTIFACT_DIR [MAX_TIME_S] [MESH_LEVEL] [INITIAL_SOLUTION_DIR] [SOLVER_MODE]" >&2
    exit 2
fi

stage="$1"
npr="$2"
artifact_dir="$3"
max_time="${4:-0.001}"
mesh_level="${5:-screen}"
initial_solution_dir="${6:-}"
solver_mode="${7:-transient}"
solver_runner="${EILMER_RUNNER:-lmr-mpi-run}"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source "$repo_dir/raptor_like_study/eilmer/eilmer5-env.sh"

mkdir -p "$artifact_dir"
cp "$repo_dir/raptor_like_study/cases/cold_n2_external_screen/ideal-n2.lua" "$artifact_dir/"
cp "$repo_dir/raptor_like_study/cases/cold_n2_external_screen/grid.lua" "$artifact_dir/"
cp "$repo_dir/raptor_like_study/cases/cold_n2_external_screen/transient.lua" "$artifact_dir/"
python "$repo_dir/raptor_like_study/cases/dlr_par_geometry/prepare_contour.py" \
    "$repo_dir/DLR_PAR_full_contour.csv" \
    --output-dir "$artifact_dir" --audit "$artifact_dir/contour_audit.json" \
    --resample-spacing-m 0.0005
prepare_args=(
    --stage "$stage" --npr "$npr" --max-time-s "$max_time"
    --mesh-level "$mesh_level"
    --solver-mode "$solver_mode"
    --lua-output "$artifact_dir/run_parameters.lua"
    --mesh-lua-output "$artifact_dir/mesh_parameters.lua"
    --json-output "$artifact_dir/run_parameters.json"
)
if [[ -n "$initial_solution_dir" ]]; then
    prepare_args+=(--initial-solution-dir "$initial_solution_dir")
fi
python "$repo_dir/raptor_like_study/cases/cold_n2_external_screen/prepare_run.py" "${prepare_args[@]}"

cd "$artifact_dir"
{
    echo "command: external screen stage=$stage NPR=$npr mesh=$mesh_level solver=$solver_mode runner=$solver_runner"
    echo "solver revision: $(lmr revision-id)"
    date -u +%FT%TZ
    lmr prep-gas -i ideal-n2.lua -o ideal-n2.gas
    lmr prep-grid --job=grid.lua
    if [[ "$mesh_level" != "screen" ]]; then
        python "$repo_dir/raptor_like_study/cases/cold_n2_external_screen/audit_wall_mesh.py" \
            --artifact-dir "$artifact_dir" --output "$artifact_dir/mesh-audit.json"
    fi
    lmr prep-sim --job=transient.lua
    mpirun -np 6 --oversubscribe "$solver_runner"
} 2>&1 | tee solver.log
if [[ "$solver_mode" == "steady" ]] && \
   ! grep -q 'STOP-REASON: relative-global-residual-target' solver.log; then
    echo "steady solver did not reach the declared residual target" >&2
    exit 1
fi
lmr snapshot2vtk --all --add-vars=mach,pitot 2>&1 | tee post-vtk.log
if [[ -d lmrsim/loads ]] && find lmrsim/loads -mindepth 2 -type f -name '*.dat' -print -quit | grep -q .; then
    echo "wall loads exported under lmrsim/loads"
else
    echo "wall loads were not exported" >&2
    exit 1
fi

python "$repo_dir/raptor_like_study/cases/cold_n2_external_screen/audit_external.py" \
    --artifact-dir "$artifact_dir" --output "$artifact_dir/audit.json" \
    --wall-profile-output "$artifact_dir/wall-profile.csv"
