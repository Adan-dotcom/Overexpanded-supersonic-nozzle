#!/usr/bin/env python3
"""Generate a LUT-compatible nozzle-plus-plume seed for a short feasibility test."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

from scipy.interpolate import PchipInterpolator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "thermochemistry"))

MESH = ROOT / "ambient_mesh" / "hybrid_pilot" / "dlr_par_hybrid.su2"
GEOMETRY = ROOT.parent / "DLR_PAR_full_contour.csv"
OF_RATIO = 3.2
T_AMBIENT = 300.0
MACH_AMBIENT = 0.001
R_THROAT = 0.010


def ambient_state(pressure: float) -> tuple[float, float, float, float, float]:
    from methalox_equilibrium import assert_thermo_range, new_equilibrium_products

    gas = new_equilibrium_products(OF_RATIO)
    gas.TP = T_AMBIENT, pressure
    gas.equilibrate("TP", max_steps=1000)
    assert_thermo_range(gas)
    velocity = MACH_AMBIENT * gas.sound_speed
    return gas.density, velocity, gas.int_energy_mass, gas.T, gas.P


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ambient-pressure", type=float, default=260_000.0)
    parser.add_argument("--case-name", default="npr20_hybrid_lut_screen")
    parser.add_argument(
        "--allow-software-feasibility-only",
        action="store_true",
        help="Acknowledge that the exterior will be cold methalox products, not air.",
    )
    args = parser.parse_args()
    if not args.allow_software_feasibility_only:
        parser.error(
            "Blocked: one DATADRIVEN_FLUID LUT would represent both exhaust and exterior. "
            "Pass --allow-software-feasibility-only only for a nonphysical integration test."
        )
    from generate_quasi1d_seed import (
        equilibrium_isentrope,
        interpolate_equilibrium,
        read_mesh_points,
        transport_and_turbulence,
    )

    output_dir = ROOT / "sensor_study" / args.case_name
    output = output_dir / "restart_hybrid_lut_seed.csv"
    output_dir.mkdir(parents=True, exist_ok=True)
    with GEOMETRY.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    gx = [float(row["x_mm"]) * 1.0e-3 for row in rows]
    gr = [float(row["r_mm"]) * 1.0e-3 for row in rows]
    radius = PchipInterpolator(gx, gr)
    x_exit, r_exit = gx[-1], gr[-1]

    states, area_curve, throat = equilibrium_isentrope()
    points = read_mesh_points(MESH)
    unique_x = sorted({x for _, x, _ in points if gx[0] <= x <= x_exit})
    axial_state = {}
    for x in unique_x:
        area_ratio = max((float(radius(x)) / R_THROAT) ** 2, 1.0)
        axial_state[x] = interpolate_equilibrium(area_ratio, x >= 0.0, states, area_curve, throat)
    exit_state = interpolate_equilibrium((r_exit / R_THROAT) ** 2, True, states, area_curve, throat)
    outside_state = ambient_state(args.ambient_pressure)

    header = (
        "PointID", "x", "y", "Density", "Momentum_x", "Momentum_y", "Energy",
        "Turb_Kin_Energy", "Omega",
    )
    with output.open("w", newline="", encoding="ascii") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for point_id, x, y in points:
            # The mesh wall and the CSV spline differ by up to about 5 nm.
            # Keep the tolerance well above that and below the 1 um first cell.
            inside = gx[0] <= x <= x_exit and y <= float(radius(x)) + 1.0e-7
            initial_jet = x_exit < x <= x_exit + 6.0 * r_exit and y <= r_exit
            density, velocity, internal_energy, temperature, _ = (
                axial_state[x] if inside else exit_state if initial_jet else outside_state
            )
            total_energy = density * (internal_energy + 0.5 * velocity**2)
            tke, omega = transport_and_turbulence(density, velocity, temperature, "sst")
            writer.writerow(
                (
                    point_id, f"{x:.15e}", f"{y:.15e}", f"{density:.15e}",
                    f"{density * velocity:.15e}", "0.000000000000000e+00",
                    f"{total_energy:.15e}", f"{tke:.15e}", f"{omega:.15e}",
                )
            )
    print(f"Wrote {output} with {len(points)} points")
    print(
        f"LUT exit seed p={exit_state[4]:.1f} Pa, T={exit_state[3]:.1f} K; "
        f"NONPHYSICAL cold-products exterior p={outside_state[4]:.1f} Pa, "
        f"T={outside_state[3]:.1f} K"
    )


if __name__ == "__main__":
    main()
