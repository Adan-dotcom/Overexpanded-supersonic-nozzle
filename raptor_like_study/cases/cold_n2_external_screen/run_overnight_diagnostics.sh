#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 ARTIFACT_ROOT" >&2
    exit 2
fi

artifact_root="$1"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
case_dir="$repo_dir/raptor_like_study/cases/cold_n2_external_screen"
gdtk_source="/home/adan/gdtk"
expected_revision="f53f4609a0331d48efee69a4e4f3c3598378cc03"
baseline="/home/adan/eilmer-artifacts/cold-n2-external-screen-20260921/stage3-npr35"

source /home/adan/eilmer-screen-venv/bin/activate
source "$repo_dir/raptor_like_study/eilmer/eilmer5-env.sh"

actual_revision="$(git -C "$gdtk_source" rev-parse HEAD)"
if [[ "$actual_revision" != "$expected_revision" ]]; then
    echo "Pinned GDTk revision mismatch: $actual_revision" >&2
    exit 1
fi
if [[ -e "$artifact_root" ]]; then
    echo "Artifact root already exists: $artifact_root" >&2
    exit 1
fi

mkdir -p "$artifact_root/logs" "$artifact_root/official" "$artifact_root/matrix"
status_file="$artifact_root/status.tsv"
printf 'label\texit_code\tstarted_utc\tfinished_utc\n' > "$status_file"

last_rc=0
run_step() {
    local label="$1"
    local workdir="$2"
    local limit="$3"
    shift 3
    local started finished
    started="$(date -u +%FT%TZ)"
    set +e
    (
        cd "$workdir"
        timeout --signal=TERM --kill-after=30s "$limit" "$@"
    ) > "$artifact_root/logs/$label.log" 2>&1
    last_rc=$?
    set -e
    finished="$(date -u +%FT%TZ)"
    printf '%s\t%s\t%s\t%s\n' "$label" "$last_rc" "$started" "$finished" >> "$status_file"
}

has_crash() {
    grep -Eq 'Segmentation fault|Floating point exception|Signal: (Segmentation fault|Floating point exception)' "$1"
}

copy_official_example() {
    local source_dir="$1"
    local destination="$2"
    mkdir -p "$destination"
    cp -a "$source_dir"/. "$destination"/
    find "$destination" -type f ! -name source-sha256.txt -print0 \
        | sort -z | xargs -0 sha256sum > "$destination/source-sha256.txt"
}

run_official_suite() {
    local label="$1"
    local workdir="$2"
    local failed=0
    run_step "${label}_prep" "$workdir" 60m make prep
    [[ "$last_rc" -eq 0 ]] || failed=1
    if [[ "$failed" -eq 0 ]]; then
        run_step "${label}_run" "$workdir" 60m make run
        [[ "$last_rc" -eq 0 ]] || failed=1
        has_crash "$artifact_root/logs/${label}_run.log" && failed=1
    fi
    if [[ "$failed" -eq 0 ]]; then
        run_step "${label}_post" "$workdir" 20m make post
        [[ "$last_rc" -eq 0 ]] || failed=1
    fi
    return "$failed"
}

mabey_dir="$artifact_root/official/flat-plate-turbulent-mabey"
structured_dir="$artifact_root/official/turbulent-flat-plate-structured"
copy_official_example "$gdtk_source/examples/lmr/2D/flat-plate-turbulent-mabey" "$mabey_dir"
copy_official_example "$gdtk_source/examples/lmr/2D/turbulent-flat-plate/structured" "$structured_dir"

official_ok=1
run_official_suite mabey "$mabey_dir" || official_ok=0
run_official_suite structured_flat_plate "$structured_dir" || official_ok=0

run_matrix_case() {
    local label="$1"
    local mesh="$2"
    local initial_dir="$3"
    local output_dir="$artifact_root/matrix/$label"
    run_step "$label" "$repo_dir" 60m \
        bash "$case_dir/run_case.sh" 3 35 "$output_dir" 0.000001 "$mesh" "$initial_dir" steady
}

if [[ "$official_ok" -eq 1 ]]; then
    run_matrix_case screen_uniform screen ""
    run_matrix_case screen_restart screen "$baseline"
    run_matrix_case wall_coarse_uniform wall-coarse ""
    run_matrix_case wall_coarse_restart wall-coarse "$baseline"
else
    printf 'matrix_skipped_official_gate\t125\t%s\t%s\n' \
        "$(date -u +%FT%TZ)" "$(date -u +%FT%TZ)" >> "$status_file"
fi

debug_workdir=""
debug_binary=""
debug_ranks=""
if [[ -f "$artifact_root/logs/mabey_run.log" ]] && has_crash "$artifact_root/logs/mabey_run.log"; then
    debug_workdir="$mabey_dir"
    debug_binary="lmrZ-mpi-run"
    debug_ranks=4
elif [[ -f "$artifact_root/logs/structured_flat_plate_run.log" ]] && has_crash "$artifact_root/logs/structured_flat_plate_run.log"; then
    debug_workdir="$structured_dir"
    debug_binary="lmrZ-mpi-run"
    debug_ranks=8
elif [[ -f "$artifact_root/logs/wall_coarse_restart.log" ]] && has_crash "$artifact_root/logs/wall_coarse_restart.log"; then
    debug_workdir="$artifact_root/matrix/wall_coarse_restart"
    debug_binary="lmr-mpi-run"
    debug_ranks=6
fi

if [[ -n "$debug_workdir" ]]; then
    debug_install="/home/adan/gdtkinst-debug-f53f460"
    run_step debug_clean "$gdtk_source/src/lmr" 20m make clean
    run_step debug_build "$gdtk_source/src/lmr" 180m \
        make install DMD=ldc2 FLAVOUR=debug INSTALL_DIR="$debug_install"
    if [[ "$last_rc" -eq 0 ]]; then
        export DGD="$debug_install"
        export PATH="$debug_install/bin:$PATH"
        export DGD_LUA_PATH="$debug_install/lib/?.lua"
        export DGD_LUA_CPATH="$debug_install/lib/?.so"
        export LD_LIBRARY_PATH="$debug_install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        run_step debug_backtrace "$debug_workdir" 30m \
            mpirun -np "$debug_ranks" --oversubscribe \
            gdb -q -batch \
            -ex 'set pagination off' \
            -ex 'set debuginfod enabled off' \
            -ex run \
            -ex 'thread apply all bt full' \
            --args "$debug_install/bin/$debug_binary"
    fi
fi

date -u +%FT%TZ > "$artifact_root/COMPLETE"
