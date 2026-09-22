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


THROAT_X_M = 0.0
EXIT_X_M = 0.12502


def nozzle_wall_samples(
    rows: list[dict[str, float]],
    throat_x: float = THROAT_X_M,
    exit_x: float = EXIT_X_M,
) -> list[dict[str, float]]:
    """Return nozzle-wall samples with downstream-positive tangential shear."""
    samples: list[dict[str, float]] = []
    for row in rows:
        x = row.get("pos.x")
        if x is None or x >= exit_x - 1.0e-12:
            # Excludes the vertical back plate at the nozzle lip.
            continue
        if "tau_wall.x" not in row or "tau_wall.y" not in row:
            continue
        tx, ty = row.get("n.y", 0.0), -row.get("n.x", 0.0)
        if tx < 0.0:
            tx, ty = -tx, -ty
        tau = row.get("outsign", 1.0) * (
            row["tau_wall.x"] * tx + row["tau_wall.y"] * ty
        )
        samples.append(
            {
                "x_m": x,
                "pressure_Pa": row.get("p", math.nan),
                "tau_tangent_Pa": tau,
                "y_plus": row.get("y+", math.nan),
                "cell_width_normal_m": row.get("cellWidthNormalToSurface", math.nan),
            }
        )
    samples.sort(key=lambda sample: sample["x_m"])
    return samples


def running_median(values: list[float], half_width: int = 1) -> list[float]:
    filtered: list[float] = []
    for index in range(len(values)):
        lo = max(0, index - half_width)
        hi = min(len(values), index + half_width + 1)
        filtered.append(float(np.median(values[lo:hi])))
    return filtered


def persistent_separation(
    samples: list[dict[str, float]],
    *,
    throat_exclusion_m: float,
    lip_exclusion_m: float,
    persistence_points: int,
    tau_zero_tolerance_pa: float,
    throat_x: float = THROAT_X_M,
    exit_x: float = EXIT_X_M,
) -> tuple[float | None, list[dict[str, float]]]:
    """Find first persistent +tau to -tau crossing in the usable divergent."""
    usable = [
        sample.copy()
        for sample in samples
        if throat_x + throat_exclusion_m <= sample["x_m"] <= exit_x - lip_exclusion_m
    ]
    if len(usable) < 2 * persistence_points:
        return None, usable
    filtered = running_median([sample["tau_tangent_Pa"] for sample in usable])
    for sample, value in zip(usable, filtered, strict=True):
        sample["tau_median3_Pa"] = value
    for index in range(persistence_points, len(usable) - persistence_points + 1):
        before = filtered[index - persistence_points:index]
        after = filtered[index:index + persistence_points]
        if all(value > tau_zero_tolerance_pa for value in before) and all(
            value < -tau_zero_tolerance_pa for value in after
        ):
            left, right = usable[index - 1], usable[index]
            tau_left, tau_right = filtered[index - 1], filtered[index]
            fraction = tau_left / (tau_left - tau_right)
            return left["x_m"] + fraction * (right["x_m"] - left["x_m"]), usable
    return None, usable


def pressure_shock(samples: list[dict[str, float]]) -> tuple[float | None, float | None]:
    """Locate the largest positive centred wall-pressure gradient."""
    gradients: list[tuple[float, float]] = []
    for left, center, right in zip(samples, samples[1:], samples[2:]):
        dx = right["x_m"] - left["x_m"]
        if dx > 0.0:
            gradient = (right["pressure_Pa"] - left["pressure_Pa"]) / dx
            if math.isfinite(gradient) and gradient > 0.0:
                gradients.append((gradient, center["x_m"]))
    if not gradients:
        return None, None
    gradient, x_shock = max(gradients)
    return x_shock, gradient


def finite_max_with_location(
    samples: list[dict[str, float]], key: str
) -> dict[str, float | None]:
    usable = [sample for sample in samples if math.isfinite(sample.get(key, math.nan))]
    if not usable:
        return {"max": None, "x_m": None}
    sample = max(usable, key=lambda item: item[key])
    return {"max": sample[key], "x_m": sample["x_m"]}


def solver_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    step = re.findall(r"FINAL-STEP:\s*(\d+)", text)
    final_time = re.findall(r"FINAL-TIME:\s*([0-9.eE+-]+)", text)
    stop = re.findall(r"STOP-REASON:\s*([^\r\n]+)", text)
    return {
        # Steady lmr runs report FINAL-STEP and STOP-REASON but no FINAL-TIME.
        # A final time is therefore informative for transient runs, not a
        # prerequisite for recognizing a normal steady stop.
        "normal_stop_recorded": bool(step and stop),
        "stop_reason": stop[-1].strip() if stop else None,
        "final_step": int(step[-1]) if step else None,
        "final_time_s": float(final_time[-1]) if final_time else None,
        "nonphysical_error_text_present": bool(
            re.search(r"NaN|floating.point|non.?physical|negative (?:pressure|density|temperature)", text, re.I)
        ),
    }


def read_wall_load_snapshot(snapshot: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for path in sorted(snapshot.glob("*.dat")):
        with path.open(encoding="ascii") as stream:
            headers = stream.readline().split()
            for line in stream:
                values = line.split()
                if values:
                    rows.append(dict(zip(headers, map(float, values), strict=True)))
    return rows


def read_wall_loads(root: Path) -> list[dict[str, float]]:
    loads = root / "lmrsim" / "loads"
    snapshots = sorted(path for path in loads.iterdir() if path.is_dir() and path.name.isdigit())
    if not snapshots:
        return []
    return read_wall_load_snapshot(snapshots[-1])


def main() -> None:
    from gdtk.lmr import LmrConfig, SimInfo

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--wall-profile-output", type=Path, required=True)
    parser.add_argument("--solver-log", type=Path, default=Path("solver.log"))
    parser.add_argument("--detector-profile-output", type=Path)
    parser.add_argument("--throat-exclusion-m", type=float, default=0.002)
    parser.add_argument("--lip-exclusion-m", type=float, default=0.002)
    parser.add_argument("--persistence-points", type=int, default=4)
    parser.add_argument("--tau-zero-tolerance-pa", type=float, default=1.0e-6)
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
    nozzle = nozzle_wall_samples(rows)
    x_sep, detector_samples = persistent_separation(
        nozzle,
        throat_exclusion_m=args.throat_exclusion_m,
        lip_exclusion_m=args.lip_exclusion_m,
        persistence_points=args.persistence_points,
        tau_zero_tolerance_pa=args.tau_zero_tolerance_pa,
    )
    x_shock, shock_gradient = pressure_shock(detector_samples)
    detector_profile_output = args.detector_profile_output or args.output.with_name(
        "wall-metrics-profile.csv"
    )
    if detector_samples:
        with detector_profile_output.open("w", newline="", encoding="ascii") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(detector_samples[0]))
            writer.writeheader()
            writer.writerows(detector_samples)

    throat_band = [sample for sample in nozzle if abs(sample["x_m"] - THROAT_X_M) <= args.throat_exclusion_m]
    divergent = [sample for sample in nozzle if sample["x_m"] >= THROAT_X_M]
    lip_band = [sample for sample in nozzle if sample["x_m"] >= EXIT_X_M - args.lip_exclusion_m]
    yplus_nozzle = finite_max_with_location(nozzle, "y_plus")
    vtk_files = [path for path in Path(sim.vtk_dir).rglob("*") if path.suffix in {".vtu", ".pvtu", ".pvd"}]
    log_path = args.solver_log
    if not log_path.is_absolute():
        log_path = root / log_path
    solver = solver_log(log_path)
    run_checks = {
        "normal_solver_stop": solver["normal_stop_recorded"],
        "no_nonphysical_error_text": not solver["nonphysical_error_text_present"],
        "finite_pressure_density_temperature": finite,
        "positive_pressure_density_temperature": nonpositive == 0,
        "vtk_export_present": bool(vtk_files),
        "wall_load_export_present": bool(rows),
    }
    payload = {
        "case_family": "cold_n2_external_screen",
        "final_snapshot": sim.snapshots[-1],
        "cell_count": cells,
        "finite_pressure_density_temperature": finite,
        "nonpositive_pressure_density_temperature_points": nonpositive,
        "state_min": minima,
        "state_max": maxima,
        "solver": solver,
        "vtk_export_present": bool(vtk_files),
        "vtk_file_count": len(vtk_files),
        "wall_load_export_present": bool(rows),
        "wall_load_point_count": len(rows),
        "wall_profile_export": str(args.wall_profile_output),
        "x_sep_m": x_sep,
        "separation_detector": {
            "definition": "first persistent positive-to-negative tangential wall-shear crossing",
            "throat_exclusion_m": args.throat_exclusion_m,
            "lip_exclusion_m": args.lip_exclusion_m,
            "median_window_points": 3,
            "persistence_points_each_side": args.persistence_points,
            "tau_zero_tolerance_Pa": args.tau_zero_tolerance_pa,
            "usable_sample_count": len(detector_samples),
            "profile": str(detector_profile_output),
        },
        "x_shock_m": x_shock,
        "shock_detector": {
            "definition": "maximum positive centred wall-pressure gradient in detector region",
            "max_dpdx_Pa_per_m": shock_gradient,
            "independent_of_separation_detector": True,
        },
        "y_plus_max": yplus_nozzle["max"],
        "y_plus": {
            "target_max": 1.0,
            "nozzle": yplus_nozzle,
            "throat_band": finite_max_with_location(throat_band, "y_plus"),
            "divergent": finite_max_with_location(divergent, "y_plus"),
            "lip_band": finite_max_with_location(lip_band, "y_plus"),
        },
        "wall_normal_cell_width_m": {
            "nozzle_min": min((sample["cell_width_normal_m"] for sample in nozzle), default=None),
            "nozzle_max": max((sample["cell_width_normal_m"] for sample in nozzle), default=None),
        },
        "mass_energy_balance": {"available": False, "reason": "open ambient and transient accumulation require a dedicated control-volume audit"},
        "run_checks": run_checks,
        "all_run_checks_pass": all(run_checks.values()),
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))
    if not payload["all_run_checks_pass"]:
        raise SystemExit("External-screen run audit failed")


if __name__ == "__main__":
    main()
