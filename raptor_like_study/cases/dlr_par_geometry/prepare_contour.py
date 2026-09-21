"""Validate the DLR-PAR CSV and convert millimetres to Eilmer metre paths."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path


EXPECTED = {
    "row_count": 385,
    "inlet_x_m": -0.02268,
    "inlet_radius_m": 0.020,
    "throat_x_m": 0.0,
    "throat_radius_m": 0.010,
    "exit_x_m": 0.12502,
    "exit_radius_m": 0.05477226,
}


def close(actual: float, expected: float, tolerance: float = 5.0e-10) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()

    raw = args.csv_file.read_bytes()
    canonical_bytes = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    rows: list[tuple[float, float]] = []
    with args.csv_file.open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["x_mm", "r_mm"]:
            raise SystemExit(f"Expected columns x_mm,r_mm; got {reader.fieldnames!r}")
        for line_number, row in enumerate(reader, start=2):
            try:
                x_m = float(row["x_mm"]) * 1.0e-3
                r_m = float(row["r_mm"]) * 1.0e-3
            except (TypeError, ValueError) as exc:
                raise SystemExit(f"Invalid numeric value on CSV line {line_number}") from exc
            if not (math.isfinite(x_m) and math.isfinite(r_m)):
                raise SystemExit(f"Non-finite coordinate on CSV line {line_number}")
            rows.append((x_m, r_m))

    xs = [point[0] for point in rows]
    radii = [point[1] for point in rows]
    failures: list[str] = []
    if len(rows) != EXPECTED["row_count"]:
        failures.append(f"row_count={len(rows)}")
    if any(b <= a for a, b in zip(xs, xs[1:])):
        failures.append("x_not_strictly_increasing")
    if any(radius <= 0.0 for radius in radii):
        failures.append("nonpositive_radius")

    throat_index = min(range(len(rows)), key=lambda index: radii[index])
    throat_count = sum(close(radius, EXPECTED["throat_radius_m"]) for radius in radii)
    if throat_count != 1:
        failures.append(f"expected_one_throat_point_got_{throat_count}")
    if any(b >= a for a, b in zip(radii[:throat_index], radii[1 : throat_index + 1])):
        failures.append("convergent_radius_not_strictly_decreasing")
    if any(b <= a for a, b in zip(radii[throat_index:], radii[throat_index + 1 :])):
        failures.append("divergent_radius_not_strictly_increasing")

    landmarks = {
        "inlet_x_m": xs[0],
        "inlet_radius_m": radii[0],
        "throat_x_m": xs[throat_index],
        "throat_radius_m": radii[throat_index],
        "exit_x_m": xs[-1],
        "exit_radius_m": radii[-1],
    }
    for name, actual in landmarks.items():
        if not close(actual, EXPECTED[name]):
            failures.append(f"{name}={actual:.12g}_expected_{EXPECTED[name]:.12g}")

    slopes = [
        (r1 - r0) / (x1 - x0)
        for (x0, r0), (x1, r1) in zip(rows, rows[1:])
    ]
    area_ratio = (radii[-1] / radii[throat_index]) ** 2
    if not close(area_ratio, 30.000004655076, tolerance=5.0e-9):
        failures.append(f"exit_area_ratio={area_ratio:.12g}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if not failures:
        sections = {
            "convergent.txt": rows[: throat_index + 1],
            "divergent.txt": rows[throat_index:],
        }
        for filename, points in sections.items():
            with (args.output_dir / filename).open("w", encoding="ascii", newline="\n") as stream:
                stream.write("# x_m r_m\n")
                for x_m, r_m in points:
                    stream.write(f"{x_m:.12g}\t{r_m:.12g}\n")

    payload = {
        "source_file": str(args.csv_file.resolve()),
        "source_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "sha256_line_ending_policy": "canonical_lf",
        "source_classification": "user_reconstruction_not_certified_cad",
        "units_input": "mm",
        "units_output": "m",
        "row_count": len(rows),
        "strictly_increasing_x": all(b > a for a, b in zip(xs, xs[1:])),
        "throat_index_zero_based": throat_index,
        "landmarks": landmarks,
        "exit_area_ratio": area_ratio,
        "segment_slope_min": min(slopes),
        "segment_slope_max": max(slopes),
        "checks_pass": not failures,
        "failures": failures,
    }
    args.audit.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    if failures:
        raise SystemExit("Contour audit failed: " + ", ".join(failures))
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
