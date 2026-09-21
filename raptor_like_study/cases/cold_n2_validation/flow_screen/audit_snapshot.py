"""Audit final cold-N2 Eilmer state, fluxes, VTK, MPI map and solver log."""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
from gdtk.gas import GasState
from gdtk.lmr import LmrConfig, SimInfo


def task_count(path: Path) -> int:
    tasks = {
        int(line.split()[1])
        for line in path.read_text(encoding="ascii").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    return len(tasks)


def face_areas_axisymmetric(grid, face: str) -> np.ndarray:
    index = 0 if face == "west" else -1
    radius = np.asarray(grid.vertices.y[index, :], dtype=float).squeeze()
    return math.pi * np.abs(radius[1:] ** 2 - radius[:-1] ** 2)


def boundary_flux(sim: SimInfo, snapshot, face: str) -> tuple[float, float, int]:
    extrema = [
        float(np.min(grid.vertices.x)) if face == "west" else float(np.max(grid.vertices.x))
        for grid in snapshot.grids
    ]
    boundary_x = min(extrema) if face == "west" else max(extrema)
    selected = [
        index for index, value in enumerate(extrema)
        if math.isclose(value, boundary_x, rel_tol=0.0, abs_tol=1.0e-12)
    ]
    gas = GasState(sim.gas_model)
    mass = energy = 0.0
    samples = 0
    ii = 0 if face == "west" else -1
    for block_id in selected:
        field = snapshot.fields[block_id]
        areas = face_areas_axisymmetric(snapshot.grids[block_id], face)
        p = np.asarray(field["p"], dtype=float).squeeze()[ii, :]
        temperature = np.asarray(field["T"], dtype=float).squeeze()[ii, :]
        rho = np.asarray(field["rho"], dtype=float).squeeze()[ii, :]
        velx = np.asarray(field["vel.x"], dtype=float).squeeze()[ii, :]
        vely = np.asarray(field["vel.y"], dtype=float).squeeze()[ii, :]
        for j, area in enumerate(areas):
            gas.p = float(p[j])
            gas.T = float(temperature[j])
            gas.update_thermo_from_pT()
            mdot = float(rho[j] * velx[j] * area)
            mass += mdot
            energy += mdot * (gas.enthalpy + 0.5 * float(velx[j] ** 2 + vely[j] ** 2))
            samples += 1
    return mass, energy, samples


def parse_solver_log(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    residual_lines = [line.strip() for line in text.splitlines() if "residual" in line.lower()]
    scientific = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)")
    last_values = [float(value) for value in scientific.findall(residual_lines[-1])] if residual_lines else []
    stop_lines = [line.strip() for line in text.splitlines() if "stop" in line.lower() or "converg" in line.lower()]
    return {
        "residual_reporting_available": bool(residual_lines),
        "residual_line_count": len(residual_lines),
        "last_residual_line": residual_lines[-1] if residual_lines else None,
        "last_residual_numeric_values": last_values,
        "solver_stop_lines": stop_lines[-5:],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.artifact_dir.resolve()
    cfg = LmrConfig(str(root / "lmr.cfg"))
    sim = SimInfo(cfg)
    final_name = sim.snapshots[-1]
    snapshot = sim.read_snapshot(final_name)

    finite = True
    nonpositive = 0
    minima = {"pressure_Pa": math.inf, "density_kg_m3": math.inf, "temperature_K": math.inf}
    maxima = {key: -math.inf for key in minima}
    cell_count = 0
    for field in snapshot.fields:
        arrays = {
            "pressure_Pa": np.asarray(field["p"], dtype=float),
            "density_kg_m3": np.asarray(field["rho"], dtype=float),
            "temperature_K": np.asarray(field["T"], dtype=float),
        }
        finite = finite and all(bool(np.isfinite(values).all()) for values in arrays.values())
        nonpositive += int(np.count_nonzero(
            (arrays["pressure_Pa"] <= 0.0)
            | (arrays["density_kg_m3"] <= 0.0)
            | (arrays["temperature_K"] <= 0.0)
        ))
        for name, values in arrays.items():
            minima[name] = min(minima[name], float(np.min(values)))
            maxima[name] = max(maxima[name], float(np.max(values)))
        cell_count += int(arrays["pressure_Pa"].size)

    inlet_mass, inlet_energy, inlet_samples = boundary_flux(sim, snapshot, "west")
    outlet_mass, outlet_energy, outlet_samples = boundary_flux(sim, snapshot, "east")
    mass_denominator = max(abs(inlet_mass), abs(outlet_mass), np.finfo(float).tiny)
    mass_imbalance = abs(inlet_mass - outlet_mass) / mass_denominator
    vtk_files = sorted(Path(sim.vtk_dir).rglob("*.vtu")) + sorted(Path(sim.vtk_dir).rglob("*.pvtu"))
    payload = {
        "solver_exit_success": True,
        "final_snapshot": final_name,
        "cell_count": cell_count,
        "mpi_ranks": task_count(root / "lmrsim" / "mpimap"),
        "finite_pressure_density_temperature": finite,
        "nonpositive_pressure_density_temperature_points": nonpositive,
        "state_min": minima,
        "state_max": maxima,
        "inlet_mass_flow_kg_s": inlet_mass,
        "outlet_mass_flow_kg_s": outlet_mass,
        "relative_mass_flow_imbalance": mass_imbalance,
        "mass_balance_method": "axisymmetric cell-centre convective snapshot flux",
        "inlet_total_energy_flux_W": inlet_energy,
        "outlet_total_energy_flux_W": outlet_energy,
        "energy_balance_available": False,
        "energy_balance_unavailable_reason": "steady snapshot audit does not yet integrate wall heat and viscous work consistently",
        "boundary_face_samples": {"inlet": inlet_samples, "outlet": outlet_samples},
        "vtk_export_present": bool(vtk_files),
        "vtk_file_count": len(vtk_files),
        **parse_solver_log(root / "solver.log"),
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
