import argparse
import json
from pathlib import Path

import numpy as np


GAMMA = 1.1982940938
R_GAS = 390.5997546790
INLET_T0 = 3485.33


def read_points_and_arrays(path):
    with path.open("r", encoding="ascii") as stream:
        for _ in range(4):
            stream.readline()
        point_header = stream.readline().split()
        n_points = int(point_header[1])
        points = np.fromstring(stream.readline(), sep=" ").reshape(n_points, 3)

        cell_header = stream.readline().split()
        stream.readline()
        stream.readline()
        stream.readline()
        point_data_header = stream.readline().split()
        if point_data_header[0] != "POINT_DATA" or int(point_data_header[1]) != n_points:
            raise ValueError("Unexpected VTK POINT_DATA section")

        arrays = {}
        while True:
            header = stream.readline()
            if not header:
                break
            fields = header.split()
            if not fields:
                continue
            if fields[0] == "SCALARS":
                stream.readline()
                arrays[fields[1]] = np.fromstring(stream.readline(), sep=" ")
            elif fields[0] == "VECTORS":
                arrays[fields[1]] = np.fromstring(stream.readline(), sep=" ").reshape(n_points, 3)
            else:
                raise ValueError(f"Unsupported VTK section: {header.strip()}")
    return points, arrays


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("vtk", type=Path)
    parser.add_argument("--output", type=Path, default=Path("temperature_overshoot_diagnostic.json"))
    args = parser.parse_args()

    points, arrays = read_points_and_arrays(args.vtk)
    temperature = arrays["Temperature"]
    mach = arrays["Mach"]
    total_temperature = temperature * (1.0 + 0.5 * (GAMMA - 1.0) * mach**2)
    index = int(np.nanargmax(temperature))
    total_index = int(np.nanargmax(total_temperature))
    energy_from_primitive = (
        arrays["Pressure"] / (GAMMA - 1.0)
        + 0.5 * arrays["Density"] * np.sum(arrays["Velocity"] ** 2, axis=1)
    )
    inside_nozzle = points[:, 0] <= 0.12502
    plume = ~inside_nozzle
    nozzle_indices = np.flatnonzero(inside_nozzle)
    nozzle_static_index = int(nozzle_indices[np.argmax(temperature[inside_nozzle])])
    nozzle_total_index = int(nozzle_indices[np.argmax(total_temperature[inside_nozzle])])

    result = {
        "source": args.vtk.name,
        "inlet_total_temperature_k": INLET_T0,
        "static_temperature_max": {
            "value_k": float(temperature[index]),
            "x_m": float(points[index, 0]),
            "r_m": float(points[index, 1]),
            "mach": float(mach[index]),
            "pressure_pa": float(arrays["Pressure"][index]),
            "density_kg_m3": float(arrays["Density"][index]),
            "velocity_m_s": arrays["Velocity"][index].tolist(),
            "local_total_temperature_k": float(total_temperature[index]),
            "stored_energy_density_j_m3": float(arrays["Energy"][index]),
            "reconstructed_energy_density_j_m3": float(energy_from_primitive[index]),
        },
        "local_total_temperature_max": {
            "value_k": float(total_temperature[total_index]),
            "x_m": float(points[total_index, 0]),
            "r_m": float(points[total_index, 1]),
            "static_temperature_k": float(temperature[total_index]),
            "mach": float(mach[total_index]),
        },
        "spatial_split": {
            "inside_nozzle_static_temperature_max_k": float(np.max(temperature[inside_nozzle])),
            "inside_nozzle_static_temperature_max_location_m": points[nozzle_static_index, :2].tolist(),
            "inside_nozzle_total_temperature_max_k": float(np.max(total_temperature[inside_nozzle])),
            "inside_nozzle_total_temperature_max_location_m": points[nozzle_total_index, :2].tolist(),
            "downstream_plume_static_temperature_max_k": float(np.max(temperature[plume])),
            "downstream_plume_total_temperature_max_k": float(np.max(total_temperature[plume])),
        },
        "point_fraction_static_temperature_above_inlet_t0": float(np.mean(temperature > INLET_T0)),
        "point_fraction_total_temperature_above_inlet_t0": float(np.mean(total_temperature > INLET_T0)),
        "interpretation": (
            "A local total temperature above the prescribed inlet total temperature demonstrates "
            "that the overshoot is in the computed energy field, not only the static-temperature plot."
        ),
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="ascii")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
