#!/usr/bin/env python3
"""Validate one provisional external-plume screen point and emit Lua input."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def positive(value: float, name: str) -> float:
    if not math.isfinite(value) or value <= 0.0:
        raise SystemExit(f"{name} must be finite and positive")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--pa-pa", type=float, default=100000.0)
    parser.add_argument("--npr", type=float, default=35.0)
    parser.add_argument("--t0-k", type=float, default=295.0)
    parser.add_argument("--wall-temperature-k", type=float, default=300.0)
    parser.add_argument("--turbulence-intensity", type=float, default=0.01)
    parser.add_argument("--length-scale-m", type=float, default=0.001)
    parser.add_argument("--max-time-s", type=float, default=0.001)
    parser.add_argument(
        "--mesh-level",
        choices=(
            "screen",
            "bridge-100um",
            "bridge-10um",
            "bridge-1um",
            "wall-coarse",
            "wall-medium",
            "wall-fine",
        ),
        default="screen",
    )
    parser.add_argument("--initial-solution-dir", type=Path)
    parser.add_argument("--solver-mode", choices=("transient", "steady"), default="transient")
    parser.add_argument("--lua-output", type=Path, required=True)
    parser.add_argument("--mesh-lua-output", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    args = parser.parse_args()

    pa = positive(args.pa_pa, "--pa-pa")
    npr = positive(args.npr, "--npr")
    if npr <= 1.0:
        raise SystemExit("--npr must be greater than one")
    t0 = positive(args.t0_k, "--t0-k")
    wall_t = positive(args.wall_temperature_k, "--wall-temperature-k")
    intensity = positive(args.turbulence_intensity, "--turbulence-intensity")
    length = positive(args.length_scale_m, "--length-scale-m")
    max_time = positive(args.max_time_s, "--max-time-s")
    p0 = npr * pa

    meshes = {
        "screen": {
            "ni_convergent": 32,
            "ni_divergent": 128,
            "ni_external": 160,
            "nj_core": 48,
            "nj_outer": 48,
            "wall_first_cell_m": None,
        },
        # Continuation-only meshes reduce the wall-normal spacing by one
        # decade at a time.  They are not members of the three-grid
        # convergence family and cannot produce accepted measurements.
        "bridge-100um": {
            "ni_convergent": 64,
            "ni_divergent": 256,
            "ni_external": 160,
            "nj_core": 64,
            "nj_outer": 48,
            "wall_first_cell_m": 4.0e-5,
            "wall_first_cell_max_goal_m": 1.0e-4,
        },
        "bridge-10um": {
            "ni_convergent": 64,
            "ni_divergent": 256,
            "ni_external": 160,
            "nj_core": 80,
            "nj_outer": 48,
            "wall_first_cell_m": 4.0e-6,
            "wall_first_cell_max_goal_m": 1.0e-5,
        },
        "bridge-1um": {
            "ni_convergent": 64,
            "ni_divergent": 256,
            "ni_external": 160,
            "nj_core": 96,
            "nj_outer": 48,
            "wall_first_cell_m": 4.0e-7,
            "wall_first_cell_max_goal_m": 1.0e-6,
        },
        "wall-coarse": {
            "ni_convergent": 64,
            "ni_divergent": 256,
            "ni_external": 160,
            "nj_core": 112,
            "nj_outer": 48,
            "wall_first_cell_m": 4.0e-8,
            "wall_first_cell_max_goal_m": 1.0e-7,
        },
        "wall-medium": {
            "ni_convergent": 64,
            "ni_divergent": 256,
            "ni_external": 160,
            "nj_core": 136,
            "nj_outer": 48,
            "wall_first_cell_m": 2.0e-8,
            "wall_first_cell_max_goal_m": 5.0e-8,
        },
        "wall-fine": {
            "ni_convergent": 64,
            "ni_divergent": 256,
            "ni_external": 160,
            "nj_core": 160,
            "nj_outer": 48,
            "wall_first_cell_m": 1.0e-8,
            "wall_first_cell_max_goal_m": 2.5e-8,
        },
    }
    mesh = meshes[args.mesh_level]
    initial_solution_dir = (
        str(args.initial_solution_dir.expanduser().resolve())
        if args.initial_solution_dir
        else None
    )

    payload = {
        "case_family": "cold_n2_external_screen",
        "classification": "provisional_external_plume_numerical_screen_not_validation",
        "stage": args.stage,
        "ambient_pressure_Pa": pa,
        "NPR": npr,
        "stagnation_pressure_Pa": p0,
        "stagnation_pressure_rule": "P0=NPR*Pa",
        "stagnation_temperature_K": t0,
        "wall_temperature_K": wall_t,
        "turbulence_intensity_fraction": intensity,
        "turbulence_length_scale_m": length,
        "max_time_s": max_time,
        "mesh_level": args.mesh_level,
        "mesh": mesh,
        "initial_solution_dir": initial_solution_dir,
        "solver_mode": args.solver_mode,
        "external_plume_modeled": True,
        "wall_function": False if args.stage == 3 else None,
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    args.lua_output.write_text(
        "-- Generated by prepare_run.py; do not edit in an artifact directory.\n"
        "screen = {\n"
        f"  stage = {args.stage},\n"
        f"  pa_Pa = {pa:.17g},\n"
        f"  npr = {npr:.17g},\n"
        f"  p0_Pa = {p0:.17g},\n"
        f"  T0_K = {t0:.17g},\n"
        f"  wall_temperature_K = {wall_t:.17g},\n"
        f"  turbulence_intensity = {intensity:.17g},\n"
        f"  turbulence_length_scale_m = {length:.17g},\n"
        f"  max_time_s = {max_time:.17g},\n"
        f"  solver_mode = {json.dumps(args.solver_mode)},\n"
        f"  initial_solution_dir = {json.dumps(initial_solution_dir)}\n"
        "}\n",
        encoding="ascii",
    )
    wall_first_cell = mesh["wall_first_cell_m"]
    args.mesh_lua_output.write_text(
        "-- Generated by prepare_run.py; do not edit in an artifact directory.\n"
        "mesh = {\n"
        f"  level = {json.dumps(args.mesh_level)},\n"
        f"  ni_convergent = {mesh['ni_convergent']},\n"
        f"  ni_divergent = {mesh['ni_divergent']},\n"
        f"  ni_external = {mesh['ni_external']},\n"
        f"  nj_core = {mesh['nj_core']},\n"
        f"  nj_outer = {mesh['nj_outer']},\n"
        f"  wall_first_cell_m = {('nil' if wall_first_cell is None else format(wall_first_cell, '.17g'))}\n"
        "}\n",
        encoding="ascii",
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
