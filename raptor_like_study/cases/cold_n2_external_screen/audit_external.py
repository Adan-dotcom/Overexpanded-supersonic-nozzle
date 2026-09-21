#!/usr/bin/env python3
"""Audit a cold-N2 external screen without assigning physics acceptance."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np
from gdtk.lmr import LmrConfig, SimInfo


def solver_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    step = re.findall(r"FINAL-STEP:\s*(\d+)", text)
    final_time = re.findall(r"FINAL-TIME:\s*([0-9.eE+-]+)", text)
    stop = re.findall(r"STOP-REASON:\s*([^\r\n]+)", text)
    return {
        "normal_stop_recorded": bool(step and final_time and stop),
        "stop_reason": stop[-1].strip() if stop else None,
        "final_step": int(step[-1]) if step else None,
        "final_time_s": float(final_time[-1]) if final_time else None,
        "nonphysical_error_text_present": bool(
            re.search(r"NaN|floating.point|non.?physical|negative (?:pressure|density|temperature)", text, re.I)
        ),
    }


def read_wall_loads(root: Path) -> list[dict[str, float]]:
    loads = root / "lmrsim" / "loads"
    snapshots = sorted(path for path in loads.iterdir() if path.is_dir() and path.name.isdigit())
    if not snapshots:
        return []
    rows: list[dict[str, float]] = []
    for path in sorted(snapshots[-1].glob("*.dat")):
        with path.open(encoding="ascii") as stream:
            headers = stream.readline().split()
            for line in stream:
                values = line.split()
                if values:
                    rows.append(dict(zip(headers, map(float, values), strict=True)))
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wall-profile-output", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_dir.resolve()
    import os
    os.chdir(root)
    (root / "lmrsim" / "loads").mkdir(exist_ok=True)
    sim = SimInfo(LmrConfig())
    snapshot = sim.read_snapshot(sim.snapshots[-1])
    minima = {"pressure_Pa": math.inf, "density_kg_m3": math.inf, "temperature_K": math.inf}
    maxima = {key: -math.inf for key in minima}
    nonpositive = 0
    finite = True
    cells = 0
    for field in snapshot.fields:
        values = {
            "pressure_Pa": np.asarray(field["p"], dtype=float),
            "density_kg_m3": np.asarray(field["rho"], dtype=float),
            "temperature_K": np.asarray(field["T"], dtype=float),
        }
        finite = finite and all(bool(np.isfinite(value).all()) for value in values.values())
        nonpositive += int(np.count_nonzero((values["pressure_Pa"] <= 0.0) | (values["density_kg_m3"] <= 0.0) | (values["temperature_K"] <= 0.0)))
        cells += int(values["pressure_Pa"].size)
        for key, value in values.items():
            minima[key] = min(minima[key], float(np.min(value)))
            maxima[key] = max(maxima[key], float(np.max(value)))

    rows = read_wall_loads(root)
    rows.sort(key=lambda row: (row.get("pos.x", 0.0), row.get("pos.y", 0.0)))
    fields = sorted({key for row in rows for key in row})
    if rows:
        with args.wall_profile_output.open("w", newline="", encoding="ascii") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    nozzle = [row for row in rows if row.get("pos.x", 1.0) <= 0.12502 + 1.0e-10]
    gradients = []
    for left, right in zip(nozzle, nozzle[1:]):
        dx = right.get("pos.x", 0.0) - left.get("pos.x", 0.0)
        if dx > 0.0 and left.get("pos.x", 0.0) >= 0.0:
            gradients.append((abs((right.get("p", 0.0) - left.get("p", 0.0)) / dx), left.get("pos.x", 0.0)))
    yplus = [row["y+"] for row in rows if "y+" in row and math.isfinite(row["y+"])]
    shear = [row for row in nozzle if "tau_wall.x" in row and "tau_wall.y" in row]
    x_sep = None
    if shear:
        values = []
        for row in shear:
            tx, ty = row.get("n.y", 0.0), -row.get("n.x", 0.0)
            if tx < 0.0:
                tx, ty = -tx, -ty
            values.append((row.get("pos.x", 0.0), row.get("outsign", 1.0) * (row["tau_wall.x"] * tx + row["tau_wall.y"] * ty)))
        values.sort()
        for (x0, t0), (x1, t1) in zip(values, values[1:]):
            if x0 >= 0.0 and t0 > 0.0 and t1 <= 0.0:
                x_sep = x0 + t0 / (t0 - t1) * (x1 - x0)
                break
    vtk_files = [path for path in Path(sim.vtk_dir).rglob("*") if path.suffix in {".vtu", ".pvtu", ".pvd"}]
    payload = {
        "case_family": "cold_n2_external_screen",
        "final_snapshot": sim.snapshots[-1],
        "cell_count": cells,
        "finite_pressure_density_temperature": finite,
        "nonpositive_pressure_density_temperature_points": nonpositive,
        "state_min": minima,
        "state_max": maxima,
        "solver": solver_log(root / "solver.log"),
        "vtk_export_present": bool(vtk_files),
        "vtk_file_count": len(vtk_files),
        "wall_load_export_present": bool(rows),
        "wall_load_point_count": len(rows),
        "wall_profile_export": str(args.wall_profile_output),
        "x_sep_m": x_sep,
        "x_shock_m": max(gradients)[1] if gradients else None,
        "y_plus_max": max(yplus) if yplus else None,
        "mass_energy_balance": {"available": False, "reason": "open ambient and transient accumulation require a dedicated control-volume audit"},
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
