#!/usr/bin/env bash
set -euo pipefail

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cea_bin="$root/tools/cea-3.3.4/cea-linux"
input_dir="$root/cases/cea/physical_doe_inputs"

chmod +x "$cea_bin"
cd "$(dirname "$cea_bin")"
for input_file in "$input_dir"/*.inp; do
  "$cea_bin" "$input_file" >/dev/null
done
echo "CEA completed for $(find "$input_dir" -maxdepth 1 -name '*.out' | wc -l) physical DOE cases"
