#!/usr/bin/env bash
set -uo pipefail

if [[ $# -ne 1 ]]; then
    echo "usage: $0 PREPARED_CASE_DIR" >&2
    exit 2
fi

case_dir="$1"
repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
source /home/adan/eilmer-screen-venv/bin/activate
source "$repo_dir/raptor_like_study/eilmer/eilmer5-env.sh"

cd "$case_dir"
started="$(date -u +%FT%TZ)"
printf 'started_utc=%s\n' "$started" | tee no-limit-status.txt

# lmrZ is the complex-Frechet executable used by the pinned official steady
# examples.  There is deliberately no wall-clock timeout: this diagnostic is
# allowed to run until normal convergence or an unequivocal solver failure.
mpirun -np 6 --oversubscribe lmrZ-mpi-run 2>&1 | tee no-limit-complex.log
solver_rc=${PIPESTATUS[0]}

printf 'solver_exit_code=%s\nfinished_utc=%s\n' \
    "$solver_rc" "$(date -u +%FT%TZ)" | tee -a no-limit-status.txt

post_rc=125
if [[ "$solver_rc" -eq 0 ]]; then
    lmr snapshot2vtk 2>&1 | tee no-limit-post.log
    post_rc=${PIPESTATUS[0]}
fi
printf 'post_exit_code=%s\n' "$post_rc" | tee -a no-limit-status.txt
exit "$solver_rc"
