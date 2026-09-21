import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
from pathlib import Path

import numpy as np

from methalox_equilibrium import (
    PRODUCT_SPECIES,
    THERMO_DATABASE,
    assert_thermo_range,
    new_equilibrium_products,
)


HERE = Path(__file__).resolve().parent
VARIABLES = (
    "Density",
    "Energy",
    "s",
    "dsde",
    "dsdrho_e",
    "d2sde2",
    "d2sdedrho",
    "d2sdrho2",
)


def new_products(of_ratio):
    gas = new_equilibrium_products(of_ratio)
    gas.TP = 3485.33, 5.2e6
    gas.equilibrate("TP")
    assert_thermo_range(gas)
    return gas


def equilibrate_uv(gas, rho, energy, composition):
    gas.Y = composition
    gas.UV = energy, 1.0 / rho
    gas.equilibrate("UV", max_steps=1000)
    assert_thermo_range(gas)
    return gas.T, gas.P, gas.entropy_mass, gas.Y.copy()


def state_and_entropy_hessian(gas, perturb, rho, energy, composition, delta_rho, delta_energy):
    temperature, pressure, entropy, center_composition = equilibrate_uv(gas, rho, energy, composition)

    t_ep, p_ep, _, _ = equilibrate_uv(perturb, rho, energy + delta_energy, center_composition)
    t_em, p_em, _, _ = equilibrate_uv(perturb, rho, energy - delta_energy, center_composition)
    rho_plus = rho + delta_rho
    rho_minus = rho - delta_rho
    t_rp, p_rp, _, _ = equilibrate_uv(perturb, rho_plus, energy, center_composition)
    t_rm, p_rm, _, _ = equilibrate_uv(perturb, rho_minus, energy, center_composition)

    dsde = 1.0 / temperature
    dsdrho = -pressure / (temperature * rho**2)
    d2sde2 = ((1.0 / t_ep) - (1.0 / t_em)) / (2.0 * delta_energy)
    mixed_from_dsde = ((1.0 / t_rp) - (1.0 / t_rm)) / (2.0 * delta_rho)
    dsdrho_ep = -p_ep / (t_ep * rho**2)
    dsdrho_em = -p_em / (t_em * rho**2)
    mixed_from_dsdrho = (dsdrho_ep - dsdrho_em) / (2.0 * delta_energy)
    d2sdedrho = 0.5 * (mixed_from_dsde + mixed_from_dsdrho)
    dsdrho_rp = -p_rp / (t_rp * rho_plus**2)
    dsdrho_rm = -p_rm / (t_rm * rho_minus**2)
    d2sdrho2 = (dsdrho_rp - dsdrho_rm) / (2.0 * delta_rho)

    values = (
        rho,
        energy,
        entropy,
        dsde,
        dsdrho,
        d2sde2,
        d2sdedrho,
        d2sdrho2,
    )
    diagnostics = {
        "temperature_k": temperature,
        "pressure_pa": pressure,
        "mixed_derivative_relative_mismatch": abs(mixed_from_dsde - mixed_from_dsdrho)
        / max(abs(d2sdedrho), 1e-30),
    }
    return values, diagnostics, center_composition


def generate_row(task):
    i, rho, energy_values, of_ratio, delta_energy = task
    gas = new_products(of_ratio)
    perturb = new_products(of_ratio)
    gas.TD = 250.0, rho
    gas.equilibrate("TV", max_steps=1000)
    assert_thermo_range(gas)
    composition = gas.Y.copy()

    rows = []
    temperatures = []
    pressures = []
    mixed_mismatch = []
    failed = []
    for j, energy in enumerate(energy_values):
        delta_rho = max(1e-6, 1e-4 * rho)
        try:
            values, diagnostics, composition = state_and_entropy_hessian(
                gas, perturb, rho, energy, composition, delta_rho, delta_energy
            )
        except Exception as error:
            failed.append(
                {
                    "rho_index": i,
                    "energy_index": j,
                    "rho": float(rho),
                    "energy": float(energy),
                    "error": str(error),
                }
            )
            continue
        rows.append(values)
        temperatures.append(diagnostics["temperature_k"])
        pressures.append(diagnostics["pressure_pa"])
        mixed_mismatch.append(diagnostics["mixed_derivative_relative_mismatch"])
    return i, rows, temperatures, pressures, mixed_mismatch, failed


def connectivity(n_rho, n_energy):
    triangles = []
    for i in range(n_rho - 1):
        for j in range(n_energy - 1):
            n00 = i * n_energy + j
            n01 = n00 + 1
            n10 = (i + 1) * n_energy + j
            n11 = n10 + 1
            triangles.append((n00, n10, n11))
            triangles.append((n00, n11, n01))
    hull = []
    hull.extend(i * n_energy for i in range(n_rho))
    hull.extend((n_rho - 1) * n_energy + j for j in range(1, n_energy))
    hull.extend(i * n_energy + (n_energy - 1) for i in range(n_rho - 2, -1, -1))
    hull.extend(j for j in range(n_energy - 2, 0, -1))
    return np.asarray(triangles, dtype=int), np.asarray(hull, dtype=int)


def write_drg(path, data, triangles, hull, metadata):
    with path.open("w", encoding="ascii", newline="\n") as stream:
        stream.write("Dragon library\n\n<Header>\n\n[Version]\n1.0.1\n\n")
        stream.write("Fluid:\nLOX_CH4_equilibrium_products_NASA_Glenn\n")
        stream.write("Reference:\nNASA_CEA_3.3.4_cross_checked\n\n")
        stream.write(f"[Number of points]\n{len(data)}\n\n")
        stream.write(f"[Number of triangles]\n{len(triangles)}\n\n")
        stream.write(f"[Number of hull points]\n{len(hull)}\n\n")
        stream.write(f"[Number of variables]\n{len(VARIABLES)}\n\n")
        stream.write("[Variable names]\n")
        for index, name in enumerate(VARIABLES, start=1):
            stream.write(f"{index}:{name}\n")
        stream.write("\n</Header>\n\n<Data>\n")
        np.savetxt(stream, data, fmt="%.14e", delimiter="\t")
        stream.write("</Data>\n\n<Connectivity>\n")
        np.savetxt(stream, triangles + 1, fmt="%d", delimiter="\t")
        stream.write("</Connectivity>\n\n<Hull>\n")
        np.savetxt(stream, hull + 1, fmt="%d")
        stream.write("</Hull>\n")
    path.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="ascii")


def main():
    parser = argparse.ArgumentParser(description="Generate an SU2 equilibrium-products rho-e lookup table.")
    parser.add_argument("--n-rho", type=int, default=72)
    parser.add_argument("--n-energy", type=int, default=192)
    parser.add_argument("--rho-min", type=float, default=0.02)
    parser.add_argument("--rho-max", type=float, default=6.0)
    parser.add_argument("--energy-min", type=float, default=-1.078e7)
    parser.add_argument("--energy-max", type=float, default=-1.5e6)
    parser.add_argument("--of-ratio", type=float, default=3.20)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--output",
        type=Path,
        default=HERE / "LUT_lox_ch4_equilibrium_nasa_refined.drg",
    )
    args = parser.parse_args()

    rho_values = np.geomspace(args.rho_min, args.rho_max, args.n_rho)
    energy_values = np.linspace(args.energy_min, args.energy_max, args.n_energy)
    delta_energy = 1e-4 * (args.energy_max - args.energy_min)
    rows = []
    temperatures = []
    pressures = []
    mixed_mismatch = []
    failed = []
    tasks = [
        (i, float(rho), energy_values, args.of_ratio, delta_energy)
        for i, rho in enumerate(rho_values)
    ]
    if args.workers > 1:
        completed = {}
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(generate_row, task): task[0] for task in tasks}
            for future in as_completed(futures):
                result = future.result()
                completed[result[0]] = result
                print(f"rho row {result[0] + 1}/{args.n_rho} complete", flush=True)
        results = [completed[i] for i in range(args.n_rho)]
    else:
        results = []
        for task in tasks:
            result = generate_row(task)
            results.append(result)
            print(f"rho row {result[0] + 1}/{args.n_rho}: {task[1]:.6g} kg/m^3", flush=True)

    for _, row_data, row_temperatures, row_pressures, row_mismatch, row_failed in results:
        rows.extend(row_data)
        temperatures.extend(row_temperatures)
        pressures.extend(row_pressures)
        mixed_mismatch.extend(row_mismatch)
        failed.extend(row_failed)

    data = np.asarray(rows)
    if failed or len(data) != args.n_rho * args.n_energy:
        failure_path = args.output.with_suffix(".failures.json")
        failure_path.write_text(json.dumps(failed, indent=2) + "\n", encoding="ascii")
        raise RuntimeError(f"Table grid is incomplete; see {failure_path}")

    triangles, hull = connectivity(args.n_rho, args.n_energy)
    rho = data[:, 0]
    energy = data[:, 1]
    entropy = data[:, 2]
    dsde = data[:, 3]
    dsdrho = data[:, 4]
    d2sde2 = data[:, 5]
    mixed = data[:, 6]
    d2rho = data[:, 7]
    temperature_reconstructed = 1.0 / dsde
    pressure_reconstructed = -rho**2 * temperature_reconstructed * dsdrho
    dpde = -rho**2 * temperature_reconstructed * (
        -temperature_reconstructed * d2sde2 * dsdrho + mixed
    )
    dpdrho = -rho * temperature_reconstructed * (
        dsdrho * (2.0 - rho * temperature_reconstructed * mixed) + rho * d2rho
    )
    sound_speed_squared = dpdrho - (dsdrho / dsde) * dpde

    metadata = {
        "generator": "Cantera equilibrium at constant internal energy and volume",
        "thermo_database": THERMO_DATABASE,
        "thermo_species": list(PRODUCT_SPECIES),
        "thermo_valid_temperature_range_k": [200.0, 6000.0],
        "n_rho": args.n_rho,
        "n_energy": args.n_energy,
        "rho_bounds_kg_m3": [args.rho_min, args.rho_max],
        "energy_bounds_j_kg": [args.energy_min, args.energy_max],
        "of_ratio": args.of_ratio,
        "equivalence_ratio": 4.0 / args.of_ratio,
        "temperature_range_k": [float(np.min(temperatures)), float(np.max(temperatures))],
        "pressure_range_pa": [float(np.min(pressures)), float(np.max(pressures))],
        "entropy_range_j_kg_k": [float(np.min(entropy)), float(np.max(entropy))],
        "max_temperature_reconstruction_relative_error": float(
            np.max(np.abs(temperature_reconstructed / np.asarray(temperatures) - 1.0))
        ),
        "max_pressure_reconstruction_relative_error": float(
            np.max(np.abs(pressure_reconstructed / np.asarray(pressures) - 1.0))
        ),
        "mixed_derivative_mismatch_percentiles": np.percentile(mixed_mismatch, [50, 95, 99, 100]).tolist(),
        "sound_speed_squared_min": float(np.min(sound_speed_squared)),
        "nonpositive_sound_speed_squared_points": int(np.sum(sound_speed_squared <= 0.0)),
        "limitations": [
            "Gaseous equilibrium-products table; NASA CEA remains the combustion reference.",
            "The phase omits condensed species and does not represent ambient air.",
            "Equilibrium chemistry is a model choice; frozen and finite-rate sensitivities remain required.",
            "Do not use outside the tabulated rho-e rectangle.",
        ],
    }
    write_drg(args.output.resolve(), data, triangles, hull, metadata)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
