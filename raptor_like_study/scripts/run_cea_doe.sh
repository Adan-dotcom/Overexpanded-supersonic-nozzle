#!/usr/bin/env bash
set -euo pipefail

STUDY_ROOT="/mnt/d/PRUEBA SU2_2026/raptor_like_study"
CEA_BIN="$STUDY_ROOT/tools/cea-3.3.4/cea-linux"
INPUT_DIR="$STUDY_ROOT/cases/cea/doe_inputs"

chmod +x "$CEA_BIN"
cd "$(dirname "$CEA_BIN")"
for input_file in "$INPUT_DIR"/*.inp; do
  "$CEA_BIN" "$input_file" >/dev/null
done
echo "CEA completed for $(find "$INPUT_DIR" -maxdepth 1 -name '*.out' | wc -l) cases"
