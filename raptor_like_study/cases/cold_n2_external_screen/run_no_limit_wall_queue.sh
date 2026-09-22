#!/usr/bin/env bash
set -uo pipefail

if [[ $# -ne 3 ]]; then
    echo "usage: $0 SCREEN_RESTART_DIR BASELINE_DIR ARTIFACT_ROOT" >&2
    exit 2
fi

screen_restart="$1"
baseline="$2"
artifact_root="$3"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
case_dir="$repo_dir/raptor_like_study/cases/cold_n2_external_screen"
source /home/adan/eilmer-screen-venv/bin/activate
source "$repo_dir/raptor_like_study/eilmer/eilmer5-env.sh"

mkdir -p "$artifact_root"
status_file="$artifact_root/status.tsv"
printf 'label\texit_code\tstarted_utc\tfinished_utc\n' > "$status_file"

record() {
    printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$(date -u +%FT%TZ)" >> "$status_file"
}

# Wait for the independent no-limit screen continuation to finish.  The
# status line is written only after MPI exits, so a partially written solver
# log cannot accidentally open the wall-mesh gate.
while ! grep -q '^solver_exit_code=' "$screen_restart/no-limit-status.txt" 2>/dev/null; do
    sleep 30
done

screen_rc="$(sed -n 's/^solver_exit_code=//p' "$screen_restart/no-limit-status.txt" | tail -1)"
screen_source="$screen_restart"
if [[ "$screen_rc" -eq 0 ]] && \
   ! grep -q 'STOP-REASON: relative-global-residual-target' \
       "$screen_restart/no-limit-complex.log"; then
    screen_rc=1
fi
record screen_restart_complex "$screen_rc" "$(sed -n 's/^started_utc=//p' "$screen_restart/no-limit-status.txt" | head -1)"

# One predefined fallback is permitted: the identical official lmrZ steady
# formulation started from a uniform field instead of interpolated transient
# data.  No numerical controls or boundary conditions are changed.
if [[ "$screen_rc" -ne 0 ]]; then
    fallback="$artifact_root/screen-uniform-fallback"
    started="$(date -u +%FT%TZ)"
    EILMER_RUNNER=lmrZ-mpi-run bash "$case_dir/run_case.sh" \
        3 35 "$fallback" 0.000001 screen '' steady
    screen_rc=$?
    record screen_uniform_complex "$screen_rc" "$started"
    screen_source="$fallback"
fi

if [[ "$screen_rc" -ne 0 ]]; then
    record wall_mesh_chain_skipped 125 "$(date -u +%FT%TZ)"
    exit "$screen_rc"
fi

started="$(date -u +%FT%TZ)"
python "$case_dir/audit_external.py" \
    --artifact-dir "$screen_source" \
    --solver-log "$screen_source/no-limit-complex.log" \
    --output "$screen_source/no-limit-audit.json" \
    --wall-profile-output "$screen_source/no-limit-wall-profile.csv"
audit_rc=$?
record screen_flow_audit "$audit_rc" "$started"
if [[ "$audit_rc" -ne 0 ]]; then
    record wall_mesh_chain_skipped 125 "$(date -u +%FT%TZ)"
    exit "$audit_rc"
fi

# Each mesh begins from the converged coarser solution.  This is the exact
# coarse-to-fine FlowSolution continuation pattern used by the pinned official
# Busemann example; lmrZ is the same complex-Frechet executable used by the
# official steady examples.  There is intentionally no wall-clock timeout.
initial="$screen_source"
for level in wall-coarse wall-medium wall-fine; do
    output="$artifact_root/$level"
    started="$(date -u +%FT%TZ)"
    EILMER_RUNNER=lmrZ-mpi-run bash "$case_dir/run_case.sh" \
        3 35 "$output" 0.000001 "$level" "$initial" steady
    rc=$?
    record "$level" "$rc" "$started"
    if [[ "$rc" -ne 0 ]]; then
        record remaining_wall_meshes_skipped 125 "$(date -u +%FT%TZ)"
        exit "$rc"
    fi
    initial="$output"
done

date -u +%FT%TZ > "$artifact_root/COMPLETE"
