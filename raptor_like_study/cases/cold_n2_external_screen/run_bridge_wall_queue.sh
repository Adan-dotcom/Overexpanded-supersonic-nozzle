#!/usr/bin/env bash
set -uo pipefail

if [[ $# -ne 3 ]]; then
    echo "usage: $0 CONVERGED_SCREEN_DIR ARTIFACT_ROOT STATUS_FILE" >&2
    exit 2
fi

initial="$1"
artifact_root="$2"
status_file="$3"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
case_dir="$repo_dir/raptor_like_study/cases/cold_n2_external_screen"
source /home/adan/eilmer-screen-venv/bin/activate
source "$repo_dir/raptor_like_study/eilmer/eilmer5-env.sh"

mkdir -p "$artifact_root"
printf 'label\texit_code\tstarted_utc\tfinished_utc\n' > "$status_file"

for level in \
    bridge-100um bridge-10um bridge-1um \
    wall-coarse wall-medium wall-fine; do
    output="$artifact_root/$level"
    started="$(date -u +%FT%TZ)"
    EILMER_RUNNER=lmrZ-mpi-run bash "$case_dir/run_case.sh" \
        3 35 "$output" 0.000001 "$level" "$initial" steady
    rc=$?
    printf '%s\t%s\t%s\t%s\n' \
        "$level" "$rc" "$started" "$(date -u +%FT%TZ)" >> "$status_file"
    if [[ "$rc" -ne 0 ]]; then
        printf 'remaining_levels_skipped\t125\t%s\t%s\n' \
            "$(date -u +%FT%TZ)" "$(date -u +%FT%TZ)" >> "$status_file"
        exit "$rc"
    fi
    initial="$output"
done

date -u +%FT%TZ > "$artifact_root/COMPLETE"
