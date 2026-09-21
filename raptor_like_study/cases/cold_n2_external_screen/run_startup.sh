#!/usr/bin/env bash
set -u

if [[ $# -ne 1 ]]; then
    echo "usage: $0 ARTIFACT_ROOT" >&2
    exit 2
fi
root="$1"
mkdir -p "$root"
status=0
for npr in 30 33 35 37 40; do
    artifact="$root/stage3-npr${npr}"
    if bash "$(dirname "${BASH_SOURCE[0]}")/run_case.sh" 3 "$npr" "$artifact" 0.001 >"$root/npr-${npr}.log" 2>&1; then
        echo "NPR=$npr status=completed artifact=$artifact"
    else
        echo "NPR=$npr status=failed artifact=$artifact"
        status=1
    fi
done
exit "$status"
