#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 ]]; then
    echo "usage: $0 STAGE NPR ARTIFACT_DIR [MAX_TIME_S]" >&2
    exit 2
fi

stage="$1"
npr="$2"
artifact_dir="$3"
max_time="${4:-0.001}"
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
python "$repo_dir/raptor_like_study/cases/cold_n2_external_screen/prepare_run.py" \
    --stage "$stage" --npr "$npr" --max-time-s "$max_time" \
    --lua-output "$artifact_dir/run_parameters.lua" \
    --json-output "$artifact_dir/run_parameters.json"

cd "$artifact_dir"
{
    echo "command: make-like external screen stage=$stage NPR=$npr"
    echo "solver revision: $(lmr revision-id)"
    date -u +%FT%TZ
    lmr prep-gas -i ideal-n2.lua -o ideal-n2.gas
    lmr prep-grid --job=grid.lua
    lmr prep-sim --job=transient.lua
    mpirun -np 6 --oversubscribe lmr-mpi-run
} 2>&1 | tee solver.log
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
