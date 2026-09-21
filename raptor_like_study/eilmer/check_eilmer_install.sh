#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=eilmer5-env.sh
source "$SCRIPT_DIR/eilmer5-env.sh"

expected_commit="f53f4609a0331d48efee69a4e4f3c3598378cc03"
actual_commit=$(git -C "$DGD_REPO" rev-parse HEAD)

test "$actual_commit" = "$expected_commit"
command -v lmr >/dev/null
command -v lmr-run >/dev/null
command -v lmr-mpi-run >/dev/null
command -v mpirun >/dev/null
command -v ldc2 >/dev/null
test -f "$DGD/lib/libgas.so"

printf 'Eilmer source: %s (%s)\n' "$DGD_REPO" "$actual_commit"
printf 'Eilmer install: %s\n' "$DGD"
printf 'lmr: %s\n' "$(command -v lmr)"
printf 'lmr-mpi-run: %s\n' "$(command -v lmr-mpi-run)"
printf 'libgas: %s\n' "$DGD/lib/libgas.so"
printf 'MPI: %s\n' "$(mpirun --version | sed -n '1p')"
printf 'LDC: %s\n' "$(ldc2 --version | sed -n '1p')"
lmr revision-id
