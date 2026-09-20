#!/usr/bin/env python3
"""Audit fast-screening SU2 solutions before they can enter the CFD dataset."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import meshio
import numpy as np
from scipy.spatial import cKDTree


ROOT = Path(__file__).resolve().parent
CASES = (
    "ideal_sst_hllc",
    "ideal_sst_slau2",
    "ideal_sa_hllc",
    "lut_sst_hllc",
    "lut_sa_hllc",
)

LIMITS = {
    "mass_flux_imbalance_fraction": 0.005,
    "energy_flux_imbalance_fraction": 0.01,
    "local_total_enthalpy_excess_fraction": 0.01,
    "minimum_residual_drop_decades": 2.0,
    "wall_y_plus_p95": 1.0,
    "wall_y_plus_max": 2.0,
    "minimum_separated_length_m": 0.001,
}


def as_scalar(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values)
    return values[:, 0] if values.ndim == 2 and values.shape[1] == 1 else values


def integrate_axisymmetric(y: np.ndarray, flux: np.ndarray) -> float:
    order = np.argsort(y)
    return float(2.0 * np.pi * np.trapezoid(flux[order] * y[order], y[order]))


def boundary_indices(points: np.ndarray, at_exit: bool) -> np.ndarray:
    x = points[:, 0]
    edge = np.max(x) if at_exit else np.min(x)
    tolerance = max(np.ptp(x) * 1.0e-10, 1.0e-12)
    return np.flatnonzero(np.abs(x - edge) <= tolerance)


def wall_indices(case_dir: Path, points: np.ndarray, density: np.ndarray, continued: bool) -> np.ndarray:
    # MPI output may renumber VTK points, so match the exact WALL coordinates
    # rather than trusting surface-CSV PointID values.
    name = "wall_continue.csv" if continued else "wall_settle.csv"
    with (case_dir / name).open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    wall_xy = np.asarray([(float(row["x"]), float(row["y"])) for row in rows])
    wall_density = np.asarray([float(row["Density"]) for row in rows])
    distances, candidates = cKDTree(points[:, :2]).query(wall_xy, k=8)
    if np.max(distances[:, 0]) > 1.0e-6:
        raise RuntimeError(f"WALL coordinate match failed: max distance {np.max(distances[:, 0]):.3e} m")
    result = []
    for row_index in range(len(rows)):
        valid = distances[row_index] <= 1.0e-6
        choices = candidates[row_index][valid]
        relative_error = np.abs(density[choices] - wall_density[row_index]) / max(wall_density[row_index], 1e-30)
        result.append(choices[np.argmin(relative_error)])
    result = np.asarray(result)
    result = np.unique(result)
    result = result[np.argsort(points[result, 0])]
    return result[1:-1]


def residual_drop(case_dir: Path) -> tuple[float, float, float]:
    values = []
    names = ["history.csv", "history_settle.csv"]
    if (case_dir / "history_continue.csv").exists():
        names.append("history_continue.csv")
    for name in names:
        with (case_dir / name).open(newline="") as stream:
            reader = csv.DictReader(stream, skipinitialspace=True)
            for row in reader:
                clean = {key.strip().strip('"'): value for key, value in row.items()}
                values.append(float(clean["rms[Rho]"]))
    first, final = values[0], values[-1]
    return first, final, first - final


def separated_runs(x: np.ndarray, cf: np.ndarray) -> list[dict[str, float]]:
    valid = np.isfinite(x) & np.isfinite(cf) & (x >= 0.0)
    x, cf = x[valid], cf[valid]
    negative = cf < 0.0
    changes = np.diff(np.r_[False, negative, False].astype(int))
    starts = np.flatnonzero(changes == 1)
    stops = np.flatnonzero(changes == -1)
    runs = []
    for start, stop in zip(starts, stops):
        x0 = float(x[start])
        x1 = float(x[stop - 1])
        runs.append({"x_start_m": x0, "x_end_m": x1, "length_m": x1 - x0})
    return runs


def audit(case: str) -> tuple[dict, dict[str, np.ndarray]]:
    case_dir = ROOT / case
    continued = (case_dir / "flow_continue.vtk").exists()
    mesh = meshio.read(case_dir / ("flow_continue.vtk" if continued else "flow_settle.vtk"))
    points = np.asarray(mesh.points)
    data = {key: np.asarray(value) for key, value in mesh.point_data.items()}

    rho = as_scalar(data["Density"])
    pressure = as_scalar(data["Pressure"])
    temperature = as_scalar(data["Temperature"])
    energy_density = as_scalar(data["Energy"])
    momentum = np.asarray(data["Momentum"])
    h0 = (energy_density + pressure) / rho

    inlet = boundary_indices(points, at_exit=False)
    outlet = boundary_indices(points, at_exit=True)
    y_in, y_out = points[inlet, 1], points[outlet, 1]
    mdot_in = integrate_axisymmetric(y_in, momentum[inlet, 0])
    mdot_out = integrate_axisymmetric(y_out, momentum[outlet, 0])
    eflux_in = integrate_axisymmetric(y_in, momentum[inlet, 0] * h0[inlet])
    eflux_out = integrate_axisymmetric(y_out, momentum[outlet, 0] * h0[outlet])
    mass_error = abs(mdot_out - mdot_in) / max(abs(mdot_in), abs(mdot_out), 1.0e-30)
    energy_error = abs(eflux_out - eflux_in) / max(abs(eflux_in), abs(eflux_out), 1.0e-30)

    # A mass-flux-weighted inlet reference remains well-defined when Cantera's
    # arbitrary formation-enthalpy datum makes h0 negative.
    h0_ref = eflux_in / mdot_in
    h0_excess = float(np.nanmax(h0) - h0_ref)
    h0_scale = max(abs(h0_ref), 1.0e6)
    h0_excess_fraction = max(0.0, h0_excess) / h0_scale

    wall = wall_indices(case_dir, points, rho, continued)
    wx = points[wall, 0]
    cf_data = np.asarray(data["Skin_Friction_Coefficient"])
    cf = cf_data[wall, 0] if cf_data.ndim == 2 else cf_data[wall]
    yplus = as_scalar(data["Y_Plus"])[wall]
    runs = separated_runs(wx, cf)
    persistent = [run for run in runs if run["length_m"] >= LIMITS["minimum_separated_length_m"]]

    first_res, final_res, drop = residual_drop(case_dir)
    extrapolation = as_scalar(data.get("Extrapolation", np.zeros_like(rho)))
    finite = bool(
        np.all(np.isfinite(rho))
        and np.all(np.isfinite(pressure))
        and np.all(np.isfinite(temperature))
        and np.all(np.isfinite(h0))
    )

    checks = {
        "finite_solution": finite,
        "positive_density_pressure_temperature": bool(
            np.min(rho) > 0.0 and np.min(pressure) > 0.0 and np.min(temperature) > 0.0
        ),
        "zero_lut_out_of_domain_points": int(np.count_nonzero(extrapolation > 0.0)) == 0,
        "mass_flux_closure": mass_error <= LIMITS["mass_flux_imbalance_fraction"],
        "energy_flux_closure": energy_error <= LIMITS["energy_flux_imbalance_fraction"],
        "local_total_enthalpy_bound": h0_excess_fraction <= LIMITS["local_total_enthalpy_excess_fraction"],
        "residual_drop": drop >= LIMITS["minimum_residual_drop_decades"],
        "wall_y_plus_p95": float(np.nanpercentile(yplus, 95)) <= LIMITS["wall_y_plus_p95"],
        "wall_y_plus_max": float(np.nanmax(yplus)) <= LIMITS["wall_y_plus_max"],
        "persistent_separation": len(persistent) > 0,
    }

    result = {
        "case": case,
        "purpose": "fast_model_screening_only",
        "operating_condition": {
            "p0_Pa": 5.2e6,
            "pa_Pa": 2.6e5,
            "NPR": 20.0,
            "physical_interpretation": "pressurized_test_chamber_not_open_atmosphere",
        },
        "iterations_completed": 1600 if continued else 400,
        "metrics": {
            "minimum_density_kg_m3": float(np.min(rho)),
            "minimum_pressure_Pa": float(np.min(pressure)),
            "minimum_temperature_K": float(np.min(temperature)),
            "maximum_temperature_K": float(np.max(temperature)),
            "lut_out_of_domain_points": int(np.count_nonzero(extrapolation > 0.0)),
            "mass_flow_in_kg_s": mdot_in,
            "mass_flow_out_kg_s": mdot_out,
            "mean_inlet_pressure_Pa": float(np.mean(pressure[inlet])),
            "mean_exit_pressure_Pa": float(np.mean(pressure[outlet])),
            "mass_flux_imbalance_fraction": mass_error,
            "energy_flux_imbalance_fraction": energy_error,
            "inlet_total_enthalpy_J_kg": h0_ref,
            "maximum_local_total_enthalpy_excess_J_kg": h0_excess,
            "local_total_enthalpy_excess_fraction": h0_excess_fraction,
            "density_residual_initial_log10": first_res,
            "density_residual_final_log10": final_res,
            "density_residual_drop_decades": drop,
            "wall_y_plus_p95": float(np.nanpercentile(yplus, 95)),
            "wall_y_plus_max": float(np.nanmax(yplus)),
            "negative_cf_runs": runs,
            "persistent_separation_runs": persistent,
        },
        "checks": checks,
        "screening_pass": bool(all(checks.values())),
        "training_eligible": False,
        "training_exclusion": "screening mesh and unconverged state; final campaign gate still required",
    }
    profiles = {"x": wx * 1e3, "cf": cf, "yplus": yplus, "pressure": pressure[wall] / 1e3}
    return result, profiles


def main() -> None:
    results = []
    profiles = {}
    for case in CASES:
        result, profile = audit(case)
        results.append(result)
        profiles[case] = profile

    output = {
        "schema_version": 1,
        "limits": LIMITS,
        "note": "No screening result is eligible for ML training.",
        "cases": results,
    }
    (ROOT / "screening_summary.json").write_text(json.dumps(output, indent=2) + "\n")

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    for case, profile in profiles.items():
        axes[0].plot(profile["x"], profile["pressure"], label=case)
        axes[1].plot(profile["x"], profile["cf"], label=case)
        axes[2].plot(profile["x"], profile["yplus"], label=case)
    axes[0].set_ylabel("Wall pressure [kPa]")
    axes[1].set_ylabel("Axial Cf [-]")
    axes[1].axhline(0.0, color="black", linewidth=0.8)
    axes[2].set_ylabel("y+ [-]")
    axes[2].set_xlabel("Axial coordinate x [mm]")
    axes[0].legend(fontsize=8, ncol=2)
    for axis in axes:
        axis.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(ROOT / "screening_wall_profiles.png", dpi=180)

    for result in results:
        metrics = result["metrics"]
        failed = [name for name, passed in result["checks"].items() if not passed]
        print(
            f"{result['case']}: pass={result['screening_pass']} "
            f"mass={metrics['mass_flux_imbalance_fraction']:.3e} "
            f"energy={metrics['energy_flux_imbalance_fraction']:.3e} "
            f"h0_excess={metrics['local_total_enthalpy_excess_fraction']:.3e} "
            f"y+95={metrics['wall_y_plus_p95']:.3f} failed={','.join(failed)}"
        )


if __name__ == "__main__":
    main()
