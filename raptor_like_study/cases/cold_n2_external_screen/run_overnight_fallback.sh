#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
    echo "usage: $0 PRIMARY_ARTIFACT_ROOT FALLBACK_ARTIFACT_ROOT" >&2
    exit 2
fi

primary_root="$1"
artifact_root="$2"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
case_dir="$repo_dir/raptor_like_study/cases/cold_n2_external_screen"
gdtk_source="/home/adan/gdtk"
baseline="/home/adan/eilmer-artifacts/cold-n2-external-screen-20260921/stage3-npr35"
expected_revision="f53f4609a0331d48efee69a4e4f3c3598378cc03"

source /home/adan/eilmer-screen-venv/bin/activate
source "$repo_dir/raptor_like_study/eilmer/eilmer5-env.sh"

if [[ "$(git -C "$gdtk_source" rev-parse HEAD)" != "$expected_revision" ]]; then
    echo "Pinned GDTk revision mismatch" >&2
    exit 1
fi
if [[ -e "$artifact_root" ]]; then
    echo "Fallback artifact root already exists: $artifact_root" >&2
    exit 1
fi

mkdir -p "$artifact_root/logs" "$artifact_root/official" "$artifact_root/matrix"
status_file="$artifact_root/status.tsv"
printf 'label\texit_code\tstarted_utc\tfinished_utc\n' > "$status_file"

wait_started="$(date -u +%FT%TZ)"
while [[ ! -f "$primary_root/COMPLETE" ]]; do
    if ! tmux has-session -t eilmer-overnight 2>/dev/null; then
        break
    fi
    sleep 30
done
printf 'wait_for_primary\t0\t%s\t%s\n' "$wait_started" "$(date -u +%FT%TZ)" >> "$status_file"

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

primary_passed() {
    local label="$1"
    [[ -f "$primary_root/status.tsv" ]] && \
        awk -F '\t' -v wanted="$label" '$1 == wanted && $2 == 0 {found=1} END {exit !found}' \
            "$primary_root/status.tsv"
}

# A third untouched official ladder specifically exercises structured-grid
# FlowSolution continuation into a finer steady Newton/Krylov case.
diffuser_dir="$artifact_root/official/diffuser-busemann"
mkdir -p "$diffuser_dir"
cp -a "$gdtk_source/examples/lmr/2D/diffuser-busemann"/. "$diffuser_dir"/
find "$diffuser_dir" -type f ! -name source-sha256.txt -print0 \
    | sort -z | xargs -0 sha256sum > "$diffuser_dir/source-sha256.txt"

run_step diffuser_coarse_prep "$diffuser_dir/coarse-grid" 60m make prep
coarse_ok=$([[ "$last_rc" -eq 0 ]] && echo 1 || echo 0)
if [[ "$coarse_ok" -eq 1 ]]; then
    run_step diffuser_coarse_run "$diffuser_dir/coarse-grid" 60m make run
    [[ "$last_rc" -eq 0 ]] || coarse_ok=0
    if has_crash "$artifact_root/logs/diffuser_coarse_run.log"; then
        coarse_ok=0
    fi
fi
if [[ "$coarse_ok" -eq 1 ]]; then
    run_step diffuser_coarse_vtk "$diffuser_dir/coarse-grid" 20m make vtk
    [[ "$last_rc" -eq 0 ]] || coarse_ok=0
fi
if [[ "$coarse_ok" -eq 1 ]]; then
    run_step diffuser_fine_prep "$diffuser_dir/fine-grid" 60m make prep
    fine_ok=$([[ "$last_rc" -eq 0 ]] && echo 1 || echo 0)
    if [[ "$fine_ok" -eq 1 ]]; then
        run_step diffuser_fine_run "$diffuser_dir/fine-grid" 60m make run
        [[ "$last_rc" -eq 0 ]] || fine_ok=0
        if has_crash "$artifact_root/logs/diffuser_fine_run.log"; then
            fine_ok=0
        fi
    fi
    if [[ "$fine_ok" -eq 1 ]]; then
        run_step diffuser_fine_vtk "$diffuser_dir/fine-grid" 20m make vtk
    fi
else
    printf 'diffuser_fine_skipped_coarse_gate\t125\t%s\t%s\n' \
        "$(date -u +%FT%TZ)" "$(date -u +%FT%TZ)" >> "$status_file"
fi

first_crash_dir=""
run_matrix_fallback() {
    local label="$1"
    local mesh="$2"
    local initial_dir="$3"
    if primary_passed "$label"; then
        printf '%s_primary_already_passed\t0\t%s\t%s\n' \
            "$label" "$(date -u +%FT%TZ)" "$(date -u +%FT%TZ)" >> "$status_file"
        return
    fi
    local output_dir="$artifact_root/matrix/$label"
    run_step "$label" "$repo_dir" 60m \
        bash "$case_dir/run_case.sh" 3 35 "$output_dir" 0.000001 "$mesh" "$initial_dir" steady
    if [[ -f "$artifact_root/logs/$label.log" ]] && has_crash "$artifact_root/logs/$label.log"; then
        [[ -n "$first_crash_dir" ]] || first_crash_dir="$output_dir"
        # Diagnostic-only binary contrast: identical prepared case, using the
        # official complex-Frechet lmrZ executable used by the steady examples.
        run_step "${label}_complex_frechet" "$output_dir" 60m \
            mpirun -np 6 --oversubscribe lmrZ-mpi-run
    fi
}

run_matrix_fallback screen_uniform screen ""
run_matrix_fallback screen_restart screen "$baseline"
run_matrix_fallback wall_coarse_uniform wall-coarse ""
run_matrix_fallback wall_coarse_restart wall-coarse "$baseline"

debug_install="/home/adan/gdtkinst-debug-f53f460"
if [[ -n "$first_crash_dir" ]]; then
    if [[ ! -x "$debug_install/bin/lmr-mpi-run" ]]; then
        run_step debug_clean "$gdtk_source/src/lmr" 20m make clean
        run_step debug_build "$gdtk_source/src/lmr" 180m \
            make install DMD=ldc2 FLAVOUR=debug INSTALL_DIR="$debug_install"
    fi
    if [[ -x "$debug_install/bin/lmr-mpi-run" ]]; then
        export DGD="$debug_install"
        export PATH="$debug_install/bin:$PATH"
        export DGD_LUA_PATH="$debug_install/lib/?.lua"
        export DGD_LUA_CPATH="$debug_install/lib/?.so"
        export LD_LIBRARY_PATH="$debug_install/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
        run_step debug_backtrace "$first_crash_dir" 30m \
            mpirun -np 6 --oversubscribe \
            gdb -q -batch \
            -ex 'set pagination off' \
            -ex 'set debuginfod enabled off' \
            -ex run \
            -ex 'thread apply all bt full' \
            --args "$debug_install/bin/lmr-mpi-run"
    fi
fi

date -u +%FT%TZ > "$artifact_root/COMPLETE"
