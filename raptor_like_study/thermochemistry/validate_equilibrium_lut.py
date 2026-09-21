import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from io import StringIO
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from generate_equilibrium_lut import state_and_entropy_hessian
from methalox_equilibrium import assert_thermo_range, new_equilibrium_products


def load_drg(path):
    text = path.read_text(encoding="ascii")
    header, remainder = text.split("</Header>", 1)
    n_variables = int(header.split("[Number of variables]", 1)[1].split()[0])
    names_block = header.split("[Variable names]", 1)[1]
    names = []
    for line in names_block.splitlines():
        line = line.strip()
        if not line:
            continue
        names.append(line.split(":", 1)[-1])
        if len(names) == n_variables:
            break
    data_text = remainder.split("<Data>", 1)[1].split("</Data>", 1)[0]
    return names, np.loadtxt(StringIO(data_text))


def interpolate_cell(table, rho_values, energy_values, rho, energy):
    i = int(np.clip(np.searchsorted(rho_values, rho) - 1, 0, len(rho_values) - 2))
    j = int(np.clip(np.searchsorted(energy_values, energy) - 1, 0, len(energy_values) - 2))
    u = (rho - rho_values[i]) / (rho_values[i + 1] - rho_values[i])
    v = (energy - energy_values[j]) / (energy_values[j + 1] - energy_values[j])
    n00 = table[i, j]
    n01 = table[i, j + 1]
    n10 = table[i + 1, j]
    n11 = table[i + 1, j + 1]
    if u >= v:
        return (1.0 - u) * n00 + (u - v) * n10 + v * n11
    return (1.0 - v) * n00 + u * n11 + (v - u) * n01


def reconstruct(row):
    rho, _, _, dsde, dsdrho, d2sde2, mixed, d2rho = row
    temperature = 1.0 / dsde
    pressure = -rho**2 * temperature * dsdrho
    dpde = -rho**2 * temperature * (-temperature * d2sde2 * dsdrho + mixed)
    dpdrho = -rho * temperature * (
        dsdrho * (2.0 - rho * temperature * mixed) + rho * d2rho
    )
    sound_speed_squared = dpdrho - (dsdrho / dsde) * dpde
    return temperature, pressure, sound_speed_squared


def equilibrium_products(of_ratio):
    gas = new_equilibrium_products(of_ratio)
    return gas, gas.Y.copy()


def equilibrate_to_energy(gas, rho, target_energy, initial_composition, minimum_energy, step=3.0e5):
    gas.Y = initial_composition
    gas.TD = 250.0, rho
    gas.equilibrate("TV", max_steps=1000)
    n_steps = max(1, int(np.ceil((target_energy - minimum_energy) / step)))
    for energy in np.linspace(minimum_energy, target_energy, n_steps + 1):
        gas.UV = energy, 1.0 / rho
        gas.equilibrate("UV", max_steps=1000)
        assert_thermo_range(gas)


def validate_chunk(task):
    rho_chunk, energy_chunk, table, rho_values, energy_values, of_ratio = task
    gas, initial_composition = equilibrium_products(of_ratio)
    perturb, _ = equilibrium_products(of_ratio)
    delta_energy = 1.0e-4 * (energy_values[-1] - energy_values[0])
    result = []
    for rho, energy in zip(rho_chunk, energy_chunk):
        equilibrate_to_energy(gas, rho, energy, initial_composition, energy_values[0])
        direct_row, direct_diagnostics, _ = state_and_entropy_hessian(
            gas,
            perturb,
            rho,
            energy,
            gas.Y.copy(),
            max(1.0e-6, 1.0e-4 * rho),
            delta_energy,
        )
        _, _, direct_sound_speed_squared = reconstruct(direct_row)
        row = interpolate_cell(table, rho_values, energy_values, rho, energy)
        temperature, pressure, sound_speed_squared = reconstruct(row)
        result.append(
            (
                rho,
                energy,
                direct_diagnostics["temperature_k"],
                direct_diagnostics["pressure_pa"],
                direct_sound_speed_squared,
                temperature,
                pressure,
                sound_speed_squared,
            )
        )
    return result


def error_summary(relative_error):
    values = 100.0 * np.abs(relative_error)
    return {
        "median_percent": float(np.percentile(values, 50)),
        "p95_percent": float(np.percentile(values, 95)),
        "p99_percent": float(np.percentile(values, 99)),
        "max_percent": float(np.max(values)),
    }


def main():
    parser = argparse.ArgumentParser(description="Validate an SU2 rho-e LUT away from its nodes.")
    parser.add_argument("table", type=Path)
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260918)
    parser.add_argument("--of-ratio", type=float, default=3.20)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    names, data = load_drg(args.table)
    rho_values = np.unique(data[:, names.index("Density")])
    energy_values = np.unique(data[:, names.index("Energy")])
    table = data.reshape(len(rho_values), len(energy_values), len(names))
    rng = np.random.default_rng(args.seed)

    # Keep holdout points away from the hull, where SU2 intentionally clamps.
    rho_samples = np.exp(
        rng.uniform(np.log(rho_values[0] * 1.02), np.log(rho_values[-1] / 1.02), args.samples)
    )
    energy_margin = 0.02 * (energy_values[-1] - energy_values[0])
    energy_samples = rng.uniform(
        energy_values[0] + energy_margin, energy_values[-1] - energy_margin, args.samples
    )

    indices = np.array_split(np.arange(args.samples), max(1, args.workers))
    tasks = [
        (
            rho_samples[index], energy_samples[index], table,
            rho_values, energy_values, args.of_ratio,
        )
        for index in indices if len(index)
    ]
    if args.workers > 1:
        records = []
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(validate_chunk, task) for task in tasks]
            for future in as_completed(futures):
                chunk = future.result()
                records.extend(chunk)
                print(f"validated {len(records)}/{args.samples} holdout points", flush=True)
    else:
        records = validate_chunk(tasks[0])

    records = np.asarray(records)
    rho_samples = records[:, 0]
    energy_samples = records[:, 1]
    actual_temperature = records[:, 2]
    actual_pressure = records[:, 3]
    actual_a2 = records[:, 4]
    predicted_temperature = records[:, 5]
    predicted_pressure = records[:, 6]
    predicted_a2 = records[:, 7]

    temperature_error = predicted_temperature / actual_temperature - 1.0
    pressure_error = predicted_pressure / actual_pressure - 1.0
    sound_speed_squared_error = predicted_a2 / actual_a2 - 1.0

    summary = {
        "table": str(args.table.resolve()),
        "samples": args.samples,
        "seed": args.seed,
        "sampling": "log-uniform density, uniform energy, two-percent hull margin",
        "density_range_kg_m3": [float(rho_samples.min()), float(rho_samples.max())],
        "energy_range_j_kg": [float(energy_samples.min()), float(energy_samples.max())],
        "direct_temperature_range_k": [float(actual_temperature.min()), float(actual_temperature.max())],
        "temperature_error": error_summary(temperature_error),
        "pressure_error": error_summary(pressure_error),
        "equilibrium_sound_speed_squared_error": error_summary(sound_speed_squared_error),
        "interpolated_sound_speed_squared_min": float(predicted_a2.min()),
        "nonpositive_sound_speed_squared_points": int(np.sum(predicted_a2 <= 0.0)),
        "reference_thermo_temperature_range_k": [200.0, 6000.0],
        "points_outside_reference_thermo_range": int(
            np.sum((actual_temperature < 200.0) | (actual_temperature > 6000.0))
        ),
    }
    output = args.table.with_suffix(".validation.json")
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), constrained_layout=True)
    axes[0].scatter(actual_temperature, 100.0 * temperature_error, s=10, alpha=0.65)
    axes[0].set(xlabel="Direct equilibrium temperature [K]", ylabel="LUT error [%]", title="Temperature")
    axes[1].scatter(actual_pressure / 1e6, 100.0 * pressure_error, s=10, alpha=0.65)
    axes[1].set(xlabel="Direct equilibrium pressure [MPa]", ylabel="LUT error [%]", title="Pressure")
    for axis in axes:
        axis.grid(alpha=0.25)
    fig.savefig(args.table.with_suffix(".validation.png"), dpi=180)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
