import csv
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
OUTPUT = HERE / "mock_sensor_dataset.csv"


def main():
    rng = np.random.default_rng(20260919)
    sensor_x = np.linspace(0.002, 0.124, 128)
    rows = []
    for index in range(160):
        pc = rng.uniform(2.0e6, 5.4e6)
        pa = rng.uniform(5.0e4, 1.01325e5)
        of_ratio = rng.uniform(3.1, 3.3)
        npr = pc / pa
        separated = npr < 66.0
        x_sep = np.clip(0.119 - 0.00155 * (npr - 20.0), 0.018, 0.124) if separated else np.nan
        baseline = pc * 0.42 * np.exp(-31.0 * sensor_x)
        if separated:
            pressure_rise = 0.82 * pa / (1.0 + np.exp(-(sensor_x - x_sep) / 0.0018))
        else:
            pressure_rise = np.zeros_like(sensor_x)
        pressure = baseline + pressure_rise + rng.normal(0.0, 2500.0, len(sensor_x))
        row = {
            "case_id": f"mock_{index:04d}",
            "geometry_id": "DLR_PAR",
            "pc_pa": pc,
            "t0_k": 3485.0 + 35.0 * (of_ratio - 3.2),
            "pa_pa": pa,
            "of_ratio": of_ratio,
            "separated": int(separated),
            "x_sep_m": x_sep,
            "physics_accepted": 0,
            "provisional": 1,
        }
        row.update({f"p_s{i:03d}": value for i, value in enumerate(pressure)})
        rows.append(row)

    with OUTPUT.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {OUTPUT} with {len(rows)} explicitly provisional cases")


if __name__ == "__main__":
    main()
