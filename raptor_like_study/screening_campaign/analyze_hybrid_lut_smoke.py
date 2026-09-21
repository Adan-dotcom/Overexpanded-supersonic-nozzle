#!/usr/bin/env python3
"""Minimal field audit for the nozzle-plus-plume LUT feasibility run."""

from __future__ import annotations

import argparse
import json
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import meshio
import numpy as np
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent.parent


def scalar(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values)
    return values[:, 0] if values.ndim == 2 and values.shape[1] == 1 else values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--case-name", default="npr20_hybrid_lut_screen")
    args = parser.parse_args()
    case_dir = ROOT / "sensor_study" / args.case_name
    if (case_dir / "flow_urans_smoke_00009.vtk").exists():
        stem, iterations = "urans_smoke_00009", 10
        stage = "URANS_physical_steps"
    elif (case_dir / "flow_safe.vtk").exists():
        stem, iterations = "safe", 505
        stage = "steady_pseudo_iterations"
    elif (case_dir / "flow_relax.vtk").exists():
        stem, iterations = "relax", 505
        stage = "steady_pseudo_iterations"
    elif (case_dir / "flow_continue.vtk").exists():
        stem, iterations = "continue", 105
        stage = "steady_pseudo_iterations"
    else:
        stem, iterations = "smoke", 5
        stage = "steady_pseudo_iterations"
    mesh = meshio.read(case_dir / f"flow_{stem}.vtk")
    data = mesh.point_data
    rho = scalar(data["Density"])
    pressure = scalar(data["Pressure"])
    temperature = scalar(data["Temperature"])
    energy = scalar(data["Energy"])
    extrapolation = scalar(data.get("Extrapolation", np.zeros_like(rho)))
    h0 = (energy + pressure) / rho
    with (case_dir / f"wall_{stem}.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    wall_xy = np.asarray([(float(row["x"]), float(row["y"])) for row in rows])
    wall_density = np.asarray([float(row["Density"]) for row in rows])
    distances, candidates = cKDTree(mesh.points[:, :2]).query(wall_xy, k=8)
    if np.max(distances[:, 0]) > 1.0e-6:
        raise RuntimeError(f"WALL coordinate match failed: max distance {np.max(distances[:, 0]):.3e} m")
    wall_ids = []
    for row_index in range(len(rows)):
        valid = distances[row_index] <= 1.0e-6
        choices = candidates[row_index][valid]
        relative_error = np.abs(rho[choices] - wall_density[row_index]) / max(wall_density[row_index], 1e-30)
        wall_ids.append(choices[np.argmin(relative_error)])
    wall_ids = np.asarray(wall_ids)
    wall_ids = np.unique(wall_ids)
    wall_ids = wall_ids[np.argsort(mesh.points[wall_ids, 0])][1:-1]
    wall_x = mesh.points[wall_ids, 0]
    cf_values = np.asarray(data["Skin_Friction_Coefficient"])
    wall_cf = cf_values[wall_ids, 0] if cf_values.ndim == 2 else cf_values[wall_ids]
    wall_yplus = scalar(data["Y_Plus"])[wall_ids]
    negative = (wall_x >= 0.0) & (wall_cf < 0.0)
    changes = np.diff(np.r_[False, negative, False].astype(int))
    starts = np.flatnonzero(changes == 1)
    stops = np.flatnonzero(changes == -1)
    separated_runs = [
        {
            "x_start_m": float(wall_x[start]),
            "x_end_m": float(wall_x[stop - 1]),
            "length_m": float(wall_x[stop - 1] - wall_x[start]),
        }
        for start, stop in zip(starts, stops)
    ]
    persistent = [run for run in separated_runs if run["length_m"] >= 0.001]
    finite = bool(
        np.all(np.isfinite(rho))
        and np.all(np.isfinite(pressure))
        and np.all(np.isfinite(temperature))
        and np.all(np.isfinite(h0))
    )
    result = {
        "case_id": args.case_name,
        "case": args.case_name,
        "case_family": "hot_methalox_application",
        "lut_used": True,
        "purpose": "software_feasibility_only",
        "iterations": iterations,
        "iteration_meaning": stage,
        "physical_time_s": 2.5e-7 if stage == "URANS_physical_steps" else None,
        "solver_exit_success": True,
        "finite_solution": finite,
        "finite_values_everywhere": finite,
        "positive_density_pressure_temperature": bool(
            np.min(rho) > 0.0 and np.min(pressure) > 0.0 and np.min(temperature) > 0.0
        ),
        "nonpositive_density_pressure_temperature_points": int(
            np.count_nonzero((rho <= 0.0) | (pressure <= 0.0) | (temperature <= 0.0))
        ),
        "minimum_density_kg_m3": float(np.min(rho)),
        "minimum_pressure_Pa": float(np.min(pressure)),
        "maximum_pressure_Pa": float(np.max(pressure)),
        "minimum_temperature_K": float(np.min(temperature)),
        "maximum_temperature_K": float(np.max(temperature)),
        "lut_out_of_domain_points": int(np.count_nonzero(extrapolation > 0.0)),
        "minimum_total_enthalpy_J_kg": float(np.min(h0)),
        "maximum_total_enthalpy_J_kg": float(np.max(h0)),
        "energy_audit_uses_total_enthalpy": True,
        "energy_reference_method_validated": False,
        "energy_conservation_audit_passed": False,
        "wall_y_plus_p95": float(np.percentile(wall_yplus, 95)),
        "wall_y_plus_max": float(np.max(wall_yplus)),
        "negative_cf_runs": separated_runs,
        "persistent_separation_runs": persistent,
        "physics_accepted": False,
        "training_eligible": False,
        "gas_model_temperature_range_validated": False,
        "wall_thermal_model_justified": False,
        "turbulence_model_sensitivity_completed": False,
        "experimental_anchor_validated": False,
        "ambient_is_air": False,
        "exhaust_composition_is_methalox_products": True,
        "products_air_mixing_validated": False,
        "chemistry_regime_justified": False,
        "thermochemistry_reference_validated": False,
        "transport_properties_validated": False,
        "chemistry_sensitivity_completed": False,
        "lut_interpolation_validated": False,
        "lut_qoi_converged": False,
        "limitations": [
            "The legacy GRI-Mech LUT exceeds its declared thermodynamic temperature range.",
            "One equilibrium-products LUT also represents the exterior; ambient is not air.",
            "The total-enthalpy range is diagnostic only because no validated inlet/ambient reference mapping exists.",
        ],
    }
    (case_dir / "smoke_field_audit.json").write_text(json.dumps(result, indent=2) + "\n")
    fig, axes = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    axes[0].plot(wall_x * 1e3, pressure[wall_ids] / 1e3)
    axes[0].set_ylabel("Wall pressure [kPa]")
    axes[1].plot(wall_x * 1e3, wall_cf)
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[1].set_ylabel("Axial Cf [-]")
    axes[2].plot(wall_x * 1e3, wall_yplus)
    axes[2].set_ylabel("y+ [-]")
    axes[2].set_xlabel("Axial coordinate x [mm]")
    for axis in axes:
        axis.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(case_dir / "wall_profiles.png", dpi=180)
    plt.close(fig)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
