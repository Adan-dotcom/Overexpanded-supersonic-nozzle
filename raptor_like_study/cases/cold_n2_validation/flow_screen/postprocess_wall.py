"""Extract provisional wall metrics from the final Eilmer loads snapshot."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


THROAT_RADIUS_M = 0.010
PERSISTENCE_POINTS = 5


def read_loads(loads_dir: Path) -> tuple[str, list[dict[str, float]]]:
    indices = sorted(path for path in loads_dir.iterdir() if path.is_dir() and path.name.isdigit())
    if not indices:
        raise SystemExit(f"No numeric loads snapshots found under {loads_dir}")
    final_dir = indices[-1]
    rows: list[dict[str, float]] = []
    for path in sorted(final_dir.glob("*.dat")):
        with path.open(encoding="ascii") as stream:
            header = stream.readline().split()
            if not header:
                continue
            for line in stream:
                values = line.split()
                if values:
                    rows.append(dict(zip(header, map(float, values), strict=True)))
    if not rows:
        raise SystemExit(f"No loads records found in {final_dir}")
    return final_dir.name, rows


def signed_tangential_shear(row: dict[str, float]) -> float:
    # Rotate the outward normal to a tangent and orient it toward increasing x.
    tx, ty = row["n.y"], -row["n.x"]
    if tx < 0.0:
        tx, ty = -tx, -ty
    return row["outsign"] * (row["tau_wall.x"] * tx + row["tau_wall.y"] * ty)


def persistent_crossing(rows: list[dict[str, float]]) -> float | None:
    values = [(row["pos.x"], row["tau_tangent_Pa"]) for row in rows if row["pos.x"] >= 0.0]
    for index in range(1, len(values) - PERSISTENCE_POINTS + 1):
        x0, tau0 = values[index - 1]
        x1, tau1 = values[index]
        downstream = [tau for _, tau in values[index : index + PERSISTENCE_POINTS]]
        if tau0 > 0.0 and tau1 <= 0.0 and all(tau < 0.0 for tau in downstream[1:]):
            fraction = tau0 / (tau0 - tau1) if tau0 != tau1 else 0.0
            return x0 + fraction * (x1 - x0)
    return None


def interpolate_target(path: Path, sweep: str, npr: float) -> float | None:
    with path.open(newline="", encoding="utf-8") as stream:
        points = sorted(
            (float(row["npr"]), float(row["x_sep_over_rt"]))
            for row in csv.DictReader(stream)
            if row["sweep_direction"] == sweep
        )
    if not points or npr < points[0][0] or npr > points[-1][0]:
        return None
    for left, right in zip(points, points[1:]):
        if left[0] <= npr <= right[0]:
            weight = (npr - left[0]) / (right[0] - left[0])
            return left[1] + weight * (right[1] - left[1])
    return points[-1][1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile-output", type=Path, required=True)
    args = parser.parse_args()

    parameters = json.loads((args.artifact_dir / "run_parameters.json").read_text())
    loads_index, rows = read_loads(args.artifact_dir / "lmrsim" / "loads")
    for row in rows:
        row["tau_tangent_Pa"] = signed_tangential_shear(row)
        row["x_over_rt"] = row["pos.x"] / THROAT_RADIUS_M
        row["p_over_pa"] = row["p"] / parameters["ambient_pressure_Pa"]
    rows.sort(key=lambda row: row["pos.x"])

    x_sep_m = persistent_crossing(rows)
    x_sep_rt = None if x_sep_m is None else x_sep_m / THROAT_RADIUS_M
    divergent = [row for row in rows if row["pos.x"] >= 0.0]
    if len(divergent) < 3:
        raise SystemExit("Too few divergent-wall load points")
    gradients: list[tuple[float, float]] = []
    for left, right in zip(divergent, divergent[1:]):
        dx = right["pos.x"] - left["pos.x"]
        if dx > 0.0:
            gradients.append((0.5 * (left["pos.x"] + right["pos.x"]), (right["p"] - left["p"]) / dx))
    shock_x_m, shock_gradient = max(gradients, key=lambda item: abs(item[1]))
    target_rt = interpolate_target(
        args.targets, parameters["sweep_direction"], parameters["NPR"]
    )

    fields = ["pos.x", "pos.y", "x_over_rt", "p", "p_over_pa", "tau_tangent_Pa", "y+"]
    with args.profile_output.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    finite = all(math.isfinite(row[field]) for row in rows for field in fields)
    payload = {
        "case_id": "dlr_par_cold_n2_internal_screen_v1",
        "classification": "provisional_internal_domain_screen_not_validation",
        "loads_index": loads_index,
        "wall_point_count": len(rows),
        "all_exported_wall_values_finite": finite,
        "maximum_wall_y_plus": max(row["y+"] for row in rows),
        "median_wall_y_plus": sorted(row["y+"] for row in rows)[len(rows) // 2],
        "x_sep_definition": "first_post_throat_positive_to_five_point_persistent_negative_wall_shear_crossing",
        "x_sep_m": x_sep_m,
        "x_sep_over_rt": x_sep_rt,
        "x_sep_digitization_uncertainty_over_rt": 0.055,
        "published_x_sep_over_rt_interpolated": target_rt,
        "x_sep_error_over_rt": None if x_sep_rt is None or target_rt is None else x_sep_rt - target_rt,
        "shock_definition": "maximum_absolute_adjacent_wall_pressure_gradient_post_throat",
        "shock_x_m": shock_x_m,
        "shock_x_over_rt": shock_x_m / THROAT_RADIUS_M,
        "shock_pressure_gradient_Pa_per_m": shock_gradient,
        "external_plume_modeled": False,
        "flow_stationarity_qualified": False,
        "mesh_convergence_qualified": False,
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
