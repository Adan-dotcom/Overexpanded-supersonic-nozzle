import csv
import json
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import PchipInterpolator


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
GEOMETRY = ROOT / "DLR_PAR_full_contour.csv"

LEVELS = {
    "coarse": {
        "axial_segments": (120, 180, 500),
        "core_layers": 80,
        "bl_layers": 48,
        "first_cell_m": 1.00e-6,
    },
    "medium": {
        "axial_segments": (240, 360, 1000),
        "core_layers": 128,
        "bl_layers": 72,
        "first_cell_m": 0.50e-6,
    },
    "fine": {
        "axial_segments": (480, 720, 2000),
        "core_layers": 192,
        "bl_layers": 104,
        "first_cell_m": 0.25e-6,
    },
}

BL_THICKNESS_M = 1.50e-3
X_BREAKS_M = (-5.0e-3, 10.0e-3)


def read_contour():
    with GEOMETRY.open(newline="", encoding="ascii") as stream:
        rows = list(csv.DictReader(stream))
    x = np.array([float(row["x_mm"]) * 1e-3 for row in rows])
    r = np.array([float(row["r_mm"]) * 1e-3 for row in rows])
    if not np.all(np.diff(x) > 0):
        raise ValueError("Contour x coordinates must be strictly increasing")
    return x, r


def geometric_growth(first, layers, total):
    lo, hi = 1.0, 1.5
    for _ in range(100):
        g = 0.5 * (lo + hi)
        distance = first * (g**layers - 1.0) / (g - 1.0)
        if distance < total:
            lo = g
        else:
            hi = g
    return 0.5 * (lo + hi)


def axial_coordinates(xmin, xmax, counts):
    bounds = (xmin, X_BREAKS_M[0], X_BREAKS_M[1], xmax)
    pieces = []
    for i, count in enumerate(counts):
        segment = np.linspace(bounds[i], bounds[i + 1], count + 1)
        pieces.append(segment if i == 0 else segment[1:])
    return np.concatenate(pieces)


def build_coordinates(level, contour_x, contour_r):
    spec = LEVELS[level]
    xwall = axial_coordinates(contour_x[0], contour_x[-1], spec["axial_segments"])
    radius = PchipInterpolator(contour_x, contour_r)
    slope_fn = radius.derivative()
    rwall = radius(xwall)
    slope = slope_fn(xwall)

    ncore = spec["core_layers"]
    nbl = spec["bl_layers"]
    nr = ncore + nbl
    growth = geometric_growth(spec["first_cell_m"], nbl, BL_THICKNESS_M)
    heights = spec["first_cell_m"] * growth ** np.arange(nbl)
    distances = np.concatenate(([0.0], np.cumsum(heights)))
    distances[-1] = BL_THICKNESS_M

    coordinates = np.empty((len(xwall), nr + 1, 2), dtype=float)
    normal_norm = np.sqrt(1.0 + slope * slope)
    nx_in = slope / normal_norm
    nr_in = -1.0 / normal_norm
    interface_x = xwall + nx_in * BL_THICKNESS_M
    interface_r = rwall + nr_in * BL_THICKNESS_M
    if np.any(interface_r <= 0):
        raise ValueError("Boundary-layer block intersects the axis")

    # Core block: axis to the inner edge of the wall-normal layer.
    core_eta = np.linspace(0.0, 1.0, ncore + 1)
    for j, eta in enumerate(core_eta):
        coordinates[:, j, 0] = xwall + eta * (interface_x - xwall)
        coordinates[:, j, 1] = eta * interface_r

    # Boundary-layer block: true offsets along the local inward wall normal.
    for k, distance in enumerate(distances[-2::-1], start=1):
        j = ncore + k
        coordinates[:, j, 0] = xwall + nx_in * distance
        coordinates[:, j, 1] = rwall + nr_in * distance

    return coordinates, xwall, rwall, growth


def mesh_quality(coordinates):
    p00 = coordinates[:-1, :-1]
    p10 = coordinates[1:, :-1]
    p11 = coordinates[1:, 1:]
    p01 = coordinates[:-1, 1:]
    area2 = (
        p00[..., 0] * p10[..., 1] - p00[..., 1] * p10[..., 0]
        + p10[..., 0] * p11[..., 1] - p10[..., 1] * p11[..., 0]
        + p11[..., 0] * p01[..., 1] - p11[..., 1] * p01[..., 0]
        + p01[..., 0] * p00[..., 1] - p01[..., 1] * p00[..., 0]
    )
    area = 0.5 * area2
    edge_lengths = np.stack(
        (
            np.linalg.norm(p10 - p00, axis=2),
            np.linalg.norm(p11 - p10, axis=2),
            np.linalg.norm(p01 - p11, axis=2),
            np.linalg.norm(p00 - p01, axis=2),
        ),
        axis=2,
    )
    aspect = edge_lengths.max(axis=2) / edge_lengths.min(axis=2)

    def vertex_angle(before, vertex, after):
        a = before - vertex
        b = after - vertex
        cosine = np.sum(a * b, axis=2) / (
            np.linalg.norm(a, axis=2) * np.linalg.norm(b, axis=2)
        )
        return np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))

    angles = np.stack(
        (
            vertex_angle(p01, p00, p10),
            vertex_angle(p00, p10, p11),
            vertex_angle(p10, p11, p01),
            vertex_angle(p11, p01, p00),
        ),
        axis=2,
    )
    wall_tangent = coordinates[1:, -1] - coordinates[:-1, -1]
    wall_inward = coordinates[:-1, -2] - coordinates[:-1, -1]
    cosine = np.sum(wall_tangent * wall_inward, axis=1) / (
        np.linalg.norm(wall_tangent, axis=1) * np.linalg.norm(wall_inward, axis=1)
    )
    wall_angle = np.degrees(np.arccos(np.clip(np.abs(cosine), 0.0, 1.0)))
    return {
        "minimum_signed_area_m2": float(area.min()),
        "negative_or_zero_cells": int(np.count_nonzero(area <= 0)),
        "minimum_corner_angle_deg": float(angles.min()),
        "maximum_corner_angle_deg": float(angles.max()),
        "median_aspect_ratio": float(np.median(aspect)),
        "maximum_aspect_ratio": float(aspect.max()),
        "minimum_wall_orthogonality_deg": float(wall_angle.min()),
        "median_wall_orthogonality_deg": float(np.median(wall_angle)),
    }


def write_su2(path, coordinates):
    ni, nj = coordinates.shape[:2]
    nx, nr = ni - 1, nj - 1
    node = lambda i, j: i * nj + j
    with path.open("w", encoding="ascii", newline="\n") as mesh:
        mesh.write("NDIME= 2\n")
        mesh.write(f"NELEM= {nx * nr}\n")
        eid = 0
        for i in range(nx):
            for j in range(nr):
                mesh.write(
                    f"9 {node(i,j)} {node(i+1,j)} {node(i+1,j+1)} "
                    f"{node(i,j+1)} {eid}\n"
                )
                eid += 1
        mesh.write(f"NPOIN= {ni * nj}\n")
        for i in range(ni):
            for j in range(nj):
                x, r = coordinates[i, j]
                mesh.write(f"{x:.12e} {r:.12e} {node(i,j)}\n")
        mesh.write("NMARK= 4\n")
        mesh.write(f"MARKER_TAG= WALL\nMARKER_ELEMS= {nx}\n")
        for i in range(nx):
            mesh.write(f"3 {node(i+1,nr)} {node(i,nr)}\n")
        mesh.write(f"MARKER_TAG= INLET\nMARKER_ELEMS= {nr}\n")
        for j in range(nr):
            mesh.write(f"3 {node(0,j+1)} {node(0,j)}\n")
        mesh.write(f"MARKER_TAG= OUTLET\nMARKER_ELEMS= {nr}\n")
        for j in range(nr):
            mesh.write(f"3 {node(nx,j)} {node(nx,j+1)}\n")
        mesh.write(f"MARKER_TAG= AXIS\nMARKER_ELEMS= {nx}\n")
        for i in range(nx):
            mesh.write(f"3 {node(i,0)} {node(i+1,0)}\n")


def plot_mesh(coordinates, contour_x, contour_r, path):
    fig, axes = plt.subplots(2, 1, figsize=(13, 8))
    ax = axes[0]
    axial_stride = max(1, (coordinates.shape[0] - 1) // 90)
    radial_stride = max(1, (coordinates.shape[1] - 1) // 35)
    for i in range(0, coordinates.shape[0], axial_stride):
        ax.plot(coordinates[i, :, 0] * 1e3, coordinates[i, :, 1] * 1e3, color="#4477aa", lw=0.35)
    for j in range(0, coordinates.shape[1], radial_stride):
        ax.plot(coordinates[:, j, 0] * 1e3, coordinates[:, j, 1] * 1e3, color="#4477aa", lw=0.35)
    ax.plot(contour_x * 1e3, contour_r * 1e3, color="#cc3311", lw=1.2)
    ax.set(xlabel="x [mm]", ylabel="r [mm]", title="DLR-PAR structured axisymmetric mesh")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(True, alpha=0.2)

    ax = axes[1]
    mask = (coordinates[:, -1, 0] >= -2e-3) & (coordinates[:, -1, 0] <= 4e-3)
    indices = np.flatnonzero(mask)
    for i in indices[::max(1, len(indices) // 70)]:
        ax.plot(coordinates[i, -24:, 0] * 1e3, coordinates[i, -24:, 1] * 1e3, color="#4477aa", lw=0.45)
    for j in range(coordinates.shape[1] - 24, coordinates.shape[1]):
        ax.plot(coordinates[mask, j, 0] * 1e3, coordinates[mask, j, 1] * 1e3, color="#4477aa", lw=0.45)
    ax.plot(contour_x * 1e3, contour_r * 1e3, color="#cc3311", lw=1.2)
    ax.set_xlim(-2, 4)
    ax.set_ylim(9.7, 11.0)
    ax.set(xlabel="x [mm]", ylabel="r [mm]", title="Throat and wall-normal layers")
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main():
    contour_x, contour_r = read_contour()
    HERE.mkdir(parents=True, exist_ok=True)
    summary = []
    for level in LEVELS:
        level_dir = HERE / level
        level_dir.mkdir(exist_ok=True)
        coords, xwall, rwall, growth = build_coordinates(level, contour_x, contour_r)
        quality = mesh_quality(coords)
        if quality["negative_or_zero_cells"]:
            raise RuntimeError(f"{level} mesh contains invalid cells: {quality}")
        mesh_path = level_dir / "dlr_par.su2"
        write_su2(mesh_path, coords)
        plot_mesh(coords, contour_x, contour_r, level_dir / "mesh_preview.png")
        spec = LEVELS[level]
        metadata = {
            "level": level,
            "cells": int((coords.shape[0] - 1) * (coords.shape[1] - 1)),
            "points": int(coords.shape[0] * coords.shape[1]),
            "axial_cells": int(coords.shape[0] - 1),
            "radial_cells": int(coords.shape[1] - 1),
            "core_layers": spec["core_layers"],
            "boundary_layer_layers": spec["bl_layers"],
            "first_cell_height_m": spec["first_cell_m"],
            "boundary_layer_block_thickness_m": BL_THICKNESS_M,
            "boundary_layer_growth_ratio": growth,
            "area_ratio": float((rwall[-1] / rwall[np.argmin(rwall)]) ** 2),
            **quality,
        }
        (level_dir / "mesh_metadata.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="ascii"
        )
        summary.append(metadata)
        print(
            f"{level}: {metadata['cells']:,} cells, h1={spec['first_cell_m']*1e6:.2f} um, "
            f"min angle={quality['minimum_corner_angle_deg']:.2f} deg"
        )
    with (HERE / "mesh_summary.csv").open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=summary[0].keys())
        writer.writeheader()
        writer.writerows(summary)


if __name__ == "__main__":
    main()
