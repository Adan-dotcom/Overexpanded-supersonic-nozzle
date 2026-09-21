"""Audit Eilmer structured grids for DLR-PAR geometry and mesh quality."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from gdtk.geom.sgrid import StructuredGrid


EXPECTED = {
    "blocks": 6,
    "cells": 92160,
    "inlet_x_m": -0.02268,
    "inlet_radius_m": 0.020,
    "throat_x_m": 0.0,
    "throat_radius_m": 0.010,
    "exit_x_m": 0.12502,
    "exit_radius_m": 0.05477226,
    "area_ratio": 30.000004655076,
}


def angle_degrees(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    dot = np.sum(a * b, axis=-1)
    denom = np.linalg.norm(a, axis=-1) * np.linalg.norm(b, axis=-1)
    cosine = np.clip(dot / denom, -1.0, 1.0)
    return np.degrees(np.arccos(cosine))


def edge_arrays(x: np.ndarray, y: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "west": np.column_stack((x[0, :], y[0, :])),
        "east": np.column_stack((x[-1, :], y[-1, :])),
        "south": np.column_stack((x[:, 0], y[:, 0])),
        "north": np.column_stack((x[:, -1], y[:, -1])),
    }


def percentile_summary(values: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(values)),
        "p05": float(np.percentile(values, 5)),
        "median": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
        "max": float(np.max(values)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("grid_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plot", type=Path, required=True)
    parser.add_argument("--expected-cells", type=int, default=EXPECTED["cells"])
    args = parser.parse_args()

    paths = sorted(args.grid_dir.glob("grid-*.gz"))
    if not paths:
        raise SystemExit(f"No grid-*.gz files found in {args.grid_dir}")

    grids: list[dict] = []
    all_areas: list[np.ndarray] = []
    all_aspects: list[np.ndarray] = []
    all_angles: list[np.ndarray] = []
    all_size_ratios: list[np.ndarray] = []
    ratio_maxima: list[dict[str, object]] = []
    all_wall_spacing: list[np.ndarray] = []
    total_cells = 0

    for path in paths:
        grid = StructuredGrid(gzfile=str(path))
        x = np.asarray(grid.vertices.x, dtype=float)
        y = np.asarray(grid.vertices.y, dtype=float)
        if x.ndim == 3:
            x = x[:, :, 0]
            y = y[:, :, 0]
        if x.ndim != 2:
            raise SystemExit(f"Expected a two-dimensional grid in {path}")

        p00 = np.stack((x[:-1, :-1], y[:-1, :-1]), axis=-1)
        p10 = np.stack((x[1:, :-1], y[1:, :-1]), axis=-1)
        p11 = np.stack((x[1:, 1:], y[1:, 1:]), axis=-1)
        p01 = np.stack((x[:-1, 1:], y[:-1, 1:]), axis=-1)
        twice_area = (
            p00[..., 0] * p10[..., 1] - p00[..., 1] * p10[..., 0]
            + p10[..., 0] * p11[..., 1] - p10[..., 1] * p11[..., 0]
            + p11[..., 0] * p01[..., 1] - p11[..., 1] * p01[..., 0]
            + p01[..., 0] * p00[..., 1] - p01[..., 1] * p00[..., 0]
        )
        areas = 0.5 * twice_area
        lengths = np.stack(
            (
                np.linalg.norm(p10 - p00, axis=-1),
                np.linalg.norm(p11 - p10, axis=-1),
                np.linalg.norm(p01 - p11, axis=-1),
                np.linalg.norm(p00 - p01, axis=-1),
            )
        )
        aspects = np.max(lengths, axis=0) / np.min(lengths, axis=0)
        angles = np.stack(
            (
                angle_degrees(p10 - p00, p01 - p00),
                angle_degrees(p00 - p10, p11 - p10),
                angle_degrees(p10 - p11, p01 - p11),
                angle_degrees(p11 - p01, p00 - p01),
            )
        )
        ratios: list[np.ndarray] = []
        if areas.shape[0] > 1:
            axial_ratios = np.maximum(
                areas[1:, :] / areas[:-1, :], areas[:-1, :] / areas[1:, :]
            )
            ratios.append(axial_ratios)
            axial_index = np.unravel_index(np.argmax(axial_ratios), axial_ratios.shape)
            ratio_maxima.append(
                {
                    "grid": path.name,
                    "direction": "axial",
                    "cell_pair_index": [int(axial_index[0]), int(axial_index[1])],
                    "approximate_vertex_location_m": [
                        float(x[axial_index[0] + 1, axial_index[1] + 1]),
                        float(y[axial_index[0] + 1, axial_index[1] + 1]),
                    ],
                    "ratio": float(axial_ratios[axial_index]),
                }
            )
        if areas.shape[1] > 1:
            radial_ratios = np.maximum(
                areas[:, 1:] / areas[:, :-1], areas[:, :-1] / areas[:, 1:]
            )
            ratios.append(radial_ratios)
            radial_index = np.unravel_index(np.argmax(radial_ratios), radial_ratios.shape)
            ratio_maxima.append(
                {
                    "grid": path.name,
                    "direction": "radial",
                    "cell_pair_index": [int(radial_index[0]), int(radial_index[1])],
                    "approximate_vertex_location_m": [
                        float(x[radial_index[0] + 1, radial_index[1] + 1]),
                        float(y[radial_index[0] + 1, radial_index[1] + 1]),
                    ],
                    "ratio": float(radial_ratios[radial_index]),
                }
            )

        wall_spacing = np.hypot(x[:, -1] - x[:, -2], y[:, -1] - y[:, -2])
        cells = (x.shape[0] - 1) * (x.shape[1] - 1)
        total_cells += cells
        grids.append(
            {
                "path": path,
                "x": x,
                "y": y,
                "edges": edge_arrays(x, y),
                "cells": cells,
                "shape_vertices": list(x.shape),
            }
        )
        all_areas.append(areas.ravel())
        all_aspects.append(aspects.ravel())
        all_angles.append(angles.ravel())
        all_size_ratios.extend(ratio.ravel() for ratio in ratios)
        all_wall_spacing.append(wall_spacing.ravel())

    areas = np.concatenate(all_areas)
    aspects = np.concatenate(all_aspects)
    angles = np.concatenate(all_angles)
    size_ratios = np.concatenate(all_size_ratios)
    wall_spacing = np.concatenate(all_wall_spacing)

    interface_mismatches: list[float] = []
    interface_pairs: list[list[str]] = []
    for left_index, left in enumerate(grids):
        for right_index in range(left_index + 1, len(grids)):
            right = grids[right_index]
            for left_name, left_edge in left["edges"].items():
                for right_name, right_edge in right["edges"].items():
                    if left_edge.shape != right_edge.shape:
                        continue
                    direct = float(np.max(np.linalg.norm(left_edge - right_edge, axis=1)))
                    reverse = float(np.max(np.linalg.norm(left_edge - right_edge[::-1], axis=1)))
                    mismatch = min(direct, reverse)
                    if mismatch <= 1.0e-10:
                        interface_mismatches.append(mismatch)
                        interface_pairs.append(
                            [f"{left['path'].name}:{left_name}", f"{right['path'].name}:{right_name}"]
                        )

    all_x = np.concatenate([grid["x"].ravel() for grid in grids])
    all_y = np.concatenate([grid["y"].ravel() for grid in grids])
    wall_points = np.concatenate(
        [np.column_stack((grid["x"][:, -1], grid["y"][:, -1])) for grid in grids]
    )
    inlet_point = wall_points[np.argmin(wall_points[:, 0])]
    exit_point = wall_points[np.argmax(wall_points[:, 0])]
    throat_point = wall_points[np.argmin(wall_points[:, 1])]
    area_ratio = (exit_point[1] / throat_point[1]) ** 2

    finite = all(
        np.all(np.isfinite(array))
        for array in (all_x, all_y, areas, aspects, angles, size_ratios, wall_spacing)
    )
    checks = {
        "six_blocks": len(paths) == EXPECTED["blocks"],
        "expected_cell_count": total_cells == args.expected_cells,
        "finite_coordinates_and_metrics": bool(finite),
        "positive_signed_cell_area": bool(np.all(areas > 0.0)),
        "axis_is_y_zero": bool(
            max(float(np.max(np.abs(grid["y"][:, 0]))) for grid in grids) <= 1.0e-14
        ),
        "no_negative_radius": bool(np.min(all_y) >= -1.0e-14),
        "five_conformal_internal_interfaces": len(interface_pairs) == 5,
        "interface_mismatch_le_1e-12_m": bool(
            len(interface_mismatches) == 5 and max(interface_mismatches) <= 1.0e-12
        ),
        "minimum_corner_angle_ge_20_deg": bool(np.min(angles) >= 20.0),
        "maximum_corner_angle_le_160_deg": bool(np.max(angles) <= 160.0),
        "maximum_edge_aspect_ratio_le_50": bool(np.max(aspects) <= 50.0),
        "maximum_adjacent_area_ratio_le_1p30": bool(np.max(size_ratios) <= 1.30),
        "inlet_landmark_matches": bool(
            abs(inlet_point[0] - EXPECTED["inlet_x_m"]) <= 1.0e-10
            and abs(inlet_point[1] - EXPECTED["inlet_radius_m"]) <= 1.0e-10
        ),
        "throat_landmark_matches": bool(
            abs(throat_point[0] - EXPECTED["throat_x_m"]) <= 1.0e-10
            and abs(throat_point[1] - EXPECTED["throat_radius_m"]) <= 1.0e-10
        ),
        "exit_landmark_matches": bool(
            abs(exit_point[0] - EXPECTED["exit_x_m"]) <= 1.0e-10
            and abs(exit_point[1] - EXPECTED["exit_radius_m"]) <= 1.0e-10
        ),
        "exit_area_ratio_matches": bool(abs(area_ratio - EXPECTED["area_ratio"]) <= 1.0e-8),
    }

    payload = {
        "case_id": "dlr_par_geometry_screen_v1",
        "classification": "geometry_and_mesh_quality_only_not_flow_validation",
        "source_classification": "user_reconstruction_not_certified_cad",
        "block_count": len(paths),
        "cell_count": total_cells,
        "cells_per_block": [grid["cells"] for grid in grids],
        "landmarks": {
            "inlet_x_m": float(inlet_point[0]),
            "inlet_radius_m": float(inlet_point[1]),
            "throat_x_m": float(throat_point[0]),
            "throat_radius_m": float(throat_point[1]),
            "exit_x_m": float(exit_point[0]),
            "exit_radius_m": float(exit_point[1]),
            "exit_area_ratio": float(area_ratio),
        },
        "mesh_quality": {
            "signed_cell_area_m2": percentile_summary(areas),
            "edge_length_aspect_ratio": percentile_summary(aspects),
            "corner_angle_deg": percentile_summary(angles),
            "adjacent_cell_area_ratio": percentile_summary(size_ratios),
            "maximum_adjacent_area_ratio_location": max(
                ratio_maxima, key=lambda item: item["ratio"]
            ),
            "wall_adjacent_vertex_spacing_m": percentile_summary(wall_spacing),
            "maximum_internal_interface_mismatch_m": max(interface_mismatches, default=math.inf),
        },
        "interfaces": interface_pairs,
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "flow_was_solved": False,
        "wall_y_plus_evaluated": False,
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")

    fig, axes = plt.subplots(2, 1, figsize=(12, 7), constrained_layout=True)
    for grid in grids:
        x, y = grid["x"], grid["y"]
        stride_i = max(1, (x.shape[0] - 1) // 30)
        stride_j = max(1, (x.shape[1] - 1) // 16)
        axes[0].plot(x[:, ::stride_j], y[:, ::stride_j], color="0.75", linewidth=0.35)
        axes[0].plot(x[::stride_i, :].T, y[::stride_i, :].T, color="0.75", linewidth=0.35)
        axes[0].plot(x[:, -1], y[:, -1], color="black", linewidth=1.0)
        axes[1].plot(x[:, ::stride_j], y[:, ::stride_j], color="0.72", linewidth=0.45)
        axes[1].plot(x[::stride_i, :].T, y[::stride_i, :].T, color="0.72", linewidth=0.45)
    axes[0].set_title("DLR-PAR geometry inspection grid (lines decimated for display)")
    axes[0].set_xlabel("x [m]")
    axes[0].set_ylabel("radius [m]")
    axes[0].set_aspect("equal", adjustable="box")
    axes[0].grid(alpha=0.2)
    axes[1].set_title("Throat detail")
    axes[1].set_xlim(-0.003, 0.008)
    axes[1].set_ylim(0.0085, 0.0125)
    axes[1].set_xlabel("x [m]")
    axes[1].set_ylabel("radius [m]")
    axes[1].grid(alpha=0.2)
    fig.savefig(args.plot, dpi=180)
    plt.close(fig)

    print(json.dumps(payload, indent=2))
    if not payload["all_checks_pass"]:
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit("Grid audit failed: " + ", ".join(failed))


if __name__ == "__main__":
    main()
