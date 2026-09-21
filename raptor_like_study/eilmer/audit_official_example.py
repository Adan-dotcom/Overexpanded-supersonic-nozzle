#!/usr/bin/env python3
"""Create compact, non-physics evidence for an official Eilmer example run."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path

import numpy as np
from gdtk.lmr import LmrConfig, SimInfo


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    final_step = re.findall(r"FINAL-STEP:\s*(\d+)", text)
    final_time = re.findall(r"FINAL-TIME:\s*([0-9.eE+-]+)", text)
    stop_reason = re.findall(r"STOP-REASON:\s*([^\r\n]+)", text)
    return {
        "sha256": sha256(path),
        "normal_stop_recorded": bool(stop_reason and final_step and final_time),
        "stop_reason": stop_reason[-1].strip() if stop_reason else None,
        "final_step": int(final_step[-1]) if final_step else None,
        "final_time_s": float(final_time[-1]) if final_time else None,
        "nonphysical_error_text_present": bool(
            re.search(
                r"(?:NaN|floating.point|non.?physical|negative (?:pressure|density|temperature))",
                text,
                flags=re.IGNORECASE,
            )
        ),
    }


def audit(root: Path, log_path: Path, source_pairs: list[tuple[Path, Path]]) -> dict:
    os.chdir(root)
    (root / "lmrsim" / "loads").mkdir(exist_ok=True)
    sim = SimInfo(LmrConfig())
    final_snapshot = sim.snapshots[-1]
    snapshot = sim.read_snapshot(final_snapshot)

    finite = True
    nonpositive = 0
    cells = 0
    minima = {"pressure_Pa": math.inf, "density_kg_m3": math.inf, "temperature_K": math.inf}
    maxima = {name: -math.inf for name in minima}
    for field in snapshot.fields:
        arrays = {
            "pressure_Pa": np.asarray(field["p"], dtype=float),
            "density_kg_m3": np.asarray(field["rho"], dtype=float),
            "temperature_K": np.asarray(field["T"], dtype=float),
        }
        finite = finite and all(bool(np.isfinite(values).all()) for values in arrays.values())
        nonpositive += int(
            np.count_nonzero(
                (arrays["pressure_Pa"] <= 0.0)
                | (arrays["density_kg_m3"] <= 0.0)
                | (arrays["temperature_K"] <= 0.0)
            )
        )
        cells += int(arrays["pressure_Pa"].size)
        for name, values in arrays.items():
            minima[name] = min(minima[name], float(np.min(values)))
            maxima[name] = max(maxima[name], float(np.max(values)))

    vtk_files = [
        path
        for path in Path(sim.vtk_dir).rglob("*")
        if path.suffix in {".vtu", ".pvtu", ".pvd"}
    ]
    sources = []
    for installed, executed in source_pairs:
        sources.append(
            {
                "installed": str(installed),
                "executed": str(executed),
                "installed_sha256": sha256(installed),
                "executed_sha256": sha256(executed),
                "identical": sha256(installed) == sha256(executed),
            }
        )

    log = parse_log(log_path)
    return {
        "scope": "official_example_installation_verification_not_physics_validation",
        "artifact_directory": str(root),
        "final_snapshot": final_snapshot,
        "cell_count": cells,
        "finite_pressure_density_temperature": finite,
        "nonpositive_pressure_density_temperature_points": nonpositive,
        "state_min": minima,
        "state_max": maxima,
        "vtk_export_present": bool(vtk_files),
        "vtk_file_count": len(vtk_files),
        "solver_log": log,
        "source_files": sources,
        "source_copy_unmodified": all(item["identical"] for item in sources),
        "physics_accepted": False,
        "training_eligible": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--solver-log", type=Path, required=True)
    parser.add_argument("--source-pair", action="append", nargs=2, metavar=("INSTALLED", "EXECUTED"), default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = audit(
        args.artifact_dir.resolve(),
        args.solver_log.resolve(),
        [(Path(left).resolve(), Path(right).resolve()) for left, right in args.source_pair],
    )
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
