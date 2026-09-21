import argparse
import csv
import math
from pathlib import Path
import sys

import numpy as np
from scipy.interpolate import PchipInterpolator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent / "thermochemistry"))

from methalox_equilibrium import assert_thermo_range, new_equilibrium_products

MESH = HERE.parent / "internal_mesh" / "screen" / "dlr_par_internal.su2"
GEOMETRY = ROOT / "DLR_PAR_full_contour.csv"

P0 = 5.2e6
T0 = 3485.33
OF_RATIO = 3.2
GAMMA = 1.1982940938
GAS_CONSTANT = 390.5997546790
R_THROAT = 0.010
MU_REF = 1.0707e-4
T_REF = 3312.09
SUTHERLAND = 683.0362
TURBULENCE_INTENSITY = 0.01
TURB2LAM_RATIO = 10.0


def read_mesh_points(path):
    with path.open(encoding="ascii") as stream:
        for line in stream:
            if line.startswith("NPOIN="):
                count = int(line.split("=", 1)[1])
                break
        else:
            raise RuntimeError("NPOIN not found")
        return [
            (int(values[2]), float(values[0]), float(values[1]))
            for values in (stream.readline().split() for _ in range(count))
        ]


def contour_radius():
    with GEOMETRY.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    x = np.asarray([float(row["x_mm"]) * 1e-3 for row in rows])
    radius = np.asarray([float(row["r_mm"]) * 1e-3 for row in rows])
    return x, radius, PchipInterpolator(x, radius)


def ideal_area_mach(mach):
    term = 2.0 / (GAMMA + 1.0) * (1.0 + 0.5 * (GAMMA - 1.0) * mach**2)
    return term ** ((GAMMA + 1.0) / (2.0 * (GAMMA - 1.0))) / mach


def ideal_mach(area_ratio, supersonic):
    low, high = ((1.0, 12.0) if supersonic else (1.0e-7, 1.0))
    for _ in range(100):
        middle = 0.5 * (low + high)
        if (ideal_area_mach(middle) < area_ratio) == supersonic:
            low = middle
        else:
            high = middle
    return 0.5 * (low + high)


def ideal_state(area_ratio, supersonic):
    mach = ideal_mach(area_ratio, supersonic)
    factor = 1.0 + 0.5 * (GAMMA - 1.0) * mach**2
    temperature = T0 / factor
    pressure = P0 / factor ** (GAMMA / (GAMMA - 1.0))
    density = pressure / (GAS_CONSTANT * temperature)
    velocity = mach * math.sqrt(GAMMA * GAS_CONSTANT * temperature)
    internal_energy = GAS_CONSTANT * temperature / (GAMMA - 1.0)
    return density, velocity, internal_energy, temperature, pressure


def equilibrium_isentrope():
    gas = new_equilibrium_products(OF_RATIO)
    gas.TP = T0, P0
    gas.equilibrate("TP", max_steps=1000)
    assert_thermo_range(gas)
    entropy0 = gas.entropy_mass
    enthalpy0 = gas.enthalpy_mass
    pressures = np.geomspace(P0 * (1.0 - 1e-7), 500.0, 2400)
    states = []
    for pressure in pressures:
        gas.SP = entropy0, pressure
        gas.equilibrate("SP", max_steps=1000)
        assert_thermo_range(gas)
        velocity = math.sqrt(max(0.0, 2.0 * (enthalpy0 - gas.enthalpy_mass)))
        states.append(
            (pressure, gas.density, velocity, gas.int_energy_mass, gas.T, gas.density * velocity)
        )
    states = np.asarray(states)
    throat = int(np.argmax(states[:, 5]))
    mass_flux_star = states[throat, 5]
    area_ratio = mass_flux_star / np.maximum(states[:, 5], 1e-30)
    if np.max(area_ratio[throat:]) < 30.0:
        raise RuntimeError("Equilibrium isentrope does not cover area ratio 30")
    return states, area_ratio, throat


def interpolate_equilibrium(area_target, supersonic, states, area_ratio, throat):
    if supersonic:
        area = area_ratio[throat:]
        data = states[throat:]
    else:
        area = area_ratio[: throat + 1][::-1]
        data = states[: throat + 1][::-1]
    area_target = min(max(area_target, 1.0), float(np.max(area)))
    return tuple(np.interp(area_target, area, data[:, column]) for column in (1, 2, 3, 4, 0))


def transport_and_turbulence(density, velocity, temperature, model):
    viscosity = MU_REF * (temperature / T_REF) ** 1.5 * (T_REF + SUTHERLAND) / (temperature + SUTHERLAND)
    if model == "sst":
        tke = max(1.5 * (TURBULENCE_INTENSITY * velocity) ** 2, 1.0e-10)
        omega = max(density * tke / (TURB2LAM_RATIO * viscosity), 1.0e-6)
        return tke, omega
    return (TURB2LAM_RATIO * viscosity / density,)


def main():
    parser = argparse.ArgumentParser(description="Generate a quasi-1D internal-nozzle SU2 restart.")
    parser.add_argument("--fluid", choices=("ideal", "lut"), required=True)
    parser.add_argument("--turbulence", choices=("sst", "sa"), required=True)
    args = parser.parse_args()
    x_geometry, radius_geometry, radius = contour_radius()
    points = read_mesh_points(MESH)
    unique_x = sorted({x for _, x, _ in points})
    if args.fluid == "lut":
        states, area_curve, throat = equilibrium_isentrope()

    axial_state = {}
    for x in unique_x:
        local_radius = float(radius(np.clip(x, x_geometry[0], x_geometry[-1])))
        area_ratio = max((local_radius / R_THROAT) ** 2, 1.0)
        if args.fluid == "ideal":
            axial_state[x] = ideal_state(area_ratio, x >= 0.0)
        else:
            axial_state[x] = interpolate_equilibrium(area_ratio, x >= 0.0, states, area_curve, throat)

    name = f"seed_{args.fluid}_{args.turbulence}.csv"
    output = HERE / name
    turbulence_names = ["Turb_Kin_Energy", "Omega"] if args.turbulence == "sst" else ["Nu_Tilde"]
    header = ["PointID", "x", "y", "Density", "Momentum_x", "Momentum_y", "Energy", *turbulence_names]
    with output.open("w", newline="", encoding="ascii") as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        for point_id, x, y in points:
            density, velocity, internal_energy, temperature, _ = axial_state[x]
            total_energy_density = density * (internal_energy + 0.5 * velocity**2)
            turbulence = transport_and_turbulence(density, velocity, temperature, args.turbulence)
            writer.writerow(
                [
                    point_id, f"{x:.15e}", f"{y:.15e}", f"{density:.15e}",
                    f"{density * velocity:.15e}", "0.000000000000000e+00",
                    f"{total_energy_density:.15e}", *[f"{value:.15e}" for value in turbulence],
                ]
            )
    exit_state = axial_state[unique_x[-1]]
    print(
        f"Wrote {output} with {len(points)} points; exit p={exit_state[4]:.3f} Pa, "
        f"T={exit_state[3]:.3f} K, u={exit_state[1]:.3f} m/s"
    )


if __name__ == "__main__":
    main()
