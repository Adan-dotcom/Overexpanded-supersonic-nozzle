#!/usr/bin/env python3
"""Audit the three external-screen wall meshes without claiming a flow result."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from gdtk.geom.sgrid import StructuredGrid


def summary(values: np.ndarray) -> dict[str, float]:
    return {
        "min": float(np.min(values)),
        "median": float(np.median(values)),
        "max": float(np.max(values)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    parameters = json.loads((args.artifact_dir / "run_parameters.json").read_text())
    target = parameters["mesh"]["wall_first_cell_m"]
    maximum_goal = parameters["mesh"]["wall_first_cell_max_goal_m"]
    expected_cells = (
        (
            parameters["mesh"]["ni_convergent"]
            + parameters["mesh"]["ni_divergent"]
            + parameters["mesh"]["ni_external"]
        )
        * parameters["mesh"]["nj_core"]
        + parameters["mesh"]["ni_external"] * parameters["mesh"]["nj_outer"]
    )

    paths = sorted((args.artifact_dir / "lmrsim" / "grid").glob("grid-*.gz"))
    areas_all: list[np.ndarray] = []
    wall_spacing_all: list[np.ndarray] = []
    wall_x_all: list[np.ndarray] = []
    total_cells = 0
    wall_blocks = 0
    finite = True
    for path in paths:
        grid = StructuredGrid(gzfile=str(path))
        x = np.asarray(grid.vertices.x, dtype=float)
        y = np.asarray(grid.vertices.y, dtype=float)
        if x.ndim == 3:
            x, y = x[:, :, 0], y[:, :, 0]
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
        areas_all.append(areas.ravel())
        total_cells += int(areas.size)
        finite = finite and bool(np.isfinite(x).all() and np.isfinite(y).all())

        metadata = json.loads(path.with_suffix(".metadata").read_text())
        if metadata.get("bcTags", {}).get("north") == "wall":
            wall_blocks += 1
            spacing = np.hypot(x[:, -1] - x[:, -2], y[:, -1] - y[:, -2])
            wall_spacing_all.append(spacing)
            wall_x_all.append(x[:, -1])

    areas = np.concatenate(areas_all)
    wall_spacing = np.concatenate(wall_spacing_all)
    wall_x = np.concatenate(wall_x_all)
    relative_error = np.abs(wall_spacing - target) / target
    regions = {
        "throat_band": np.abs(wall_x) <= 0.002,
        "divergent": wall_x >= 0.0,
        "lip_band": wall_x >= 0.12502 - 0.002,
    }
    checks = {
        "nine_blocks": len(paths) == 9,
        "expected_cell_count": total_cells == expected_cells,
        "finite_coordinates": finite,
        "positive_signed_cell_area": bool(np.all(areas > 0.0)),
        "three_nozzle_wall_blocks": wall_blocks == 3,
        "maximum_first_cell_within_goal": bool(np.max(wall_spacing) <= maximum_goal * 1.05),
    }
    payload = {
        "case_family": "cold_n2_external_screen",
        "classification": "wall_mesh_geometry_only_not_flow_validation",
        "mesh_level": parameters["mesh_level"],
        "block_count": len(paths),
        "cell_count": total_cells,
        "nominal_edge_first_cell_m": target,
        "maximum_first_cell_goal_m": maximum_goal,
        "wall_normal_first_cell_m": summary(wall_spacing),
        "wall_normal_first_cell_relative_error": summary(relative_error),
        "regional_first_cell_m": {
            name: summary(wall_spacing[mask]) for name, mask in regions.items()
        },
        "signed_cell_area_m2": summary(areas),
        "checks": checks,
        "all_geometry_checks_pass": all(checks.values()),
        "flow_was_solved": False,
        "wall_y_plus_evaluated": False,
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))
    if not payload["all_geometry_checks_pass"]:
        raise SystemExit("Wall-mesh geometry audit failed")


if __name__ == "__main__":
    main()
