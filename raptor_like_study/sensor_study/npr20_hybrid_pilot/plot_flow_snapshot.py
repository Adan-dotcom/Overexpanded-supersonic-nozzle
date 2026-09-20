"""Create a near-field Mach/temperature plot from an ASCII legacy VTK file."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


def read_ascii_vtk(path: Path) -> tuple[np.ndarray, np.ndarray, dict[str, np.ndarray]]:
    with path.open("r", encoding="ascii") as stream:
        for _ in range(4):
            stream.readline()
        point_header = stream.readline().split()
        n_points = int(point_header[1])
        points = np.fromstring(stream.readline(), sep=" ").reshape(n_points, 3)

        cell_header = stream.readline().split()
        n_cells = int(cell_header[1])
        packed_cells = np.fromstring(stream.readline(), sep=" ", dtype=np.int64)
        stream.readline()
        stream.readline()
        point_data_header = stream.readline().split()
        if point_data_header[0] != "POINT_DATA" or int(point_data_header[1]) != n_points:
            raise ValueError("Unexpected VTK POINT_DATA section")

        arrays: dict[str, np.ndarray] = {}
        while True:
            header = stream.readline()
            if not header:
                break
            fields = header.split()
            if not fields:
                continue
            if fields[0] == "SCALARS":
                name = fields[1]
                stream.readline()
                arrays[name] = np.fromstring(stream.readline(), sep=" ")
            elif fields[0] == "VECTORS":
                name = fields[1]
                arrays[name] = np.fromstring(stream.readline(), sep=" ").reshape(n_points, 3)
            else:
                raise ValueError(f"Unsupported VTK section: {header.strip()}")

    triangles: list[tuple[int, int, int]] = []
    offset = 0
    for _ in range(n_cells):
        count = int(packed_cells[offset])
        nodes = packed_cells[offset + 1 : offset + 1 + count]
        if count == 3:
            triangles.append((int(nodes[0]), int(nodes[1]), int(nodes[2])))
        elif count == 4:
            triangles.append((int(nodes[0]), int(nodes[1]), int(nodes[2])))
            triangles.append((int(nodes[0]), int(nodes[2]), int(nodes[3])))
        offset += count + 1
    return points, np.asarray(triangles, dtype=np.int64), arrays


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("vtk", type=Path)
    parser.add_argument("--output", type=Path, default=Path("flow_snapshot.png"))
    parser.add_argument("--x-max", type=float, default=0.22)
    parser.add_argument("--r-max", type=float, default=0.12)
    args = parser.parse_args()

    points, triangles, arrays = read_ascii_vtk(args.vtk)
    x = points[:, 0]
    radius = points[:, 1]
    keep = np.all(
        (x[triangles] >= -0.023)
        & (x[triangles] <= args.x_max)
        & (radius[triangles] >= 0.0)
        & (radius[triangles] <= args.r_max),
        axis=1,
    )
    triangulation = mtri.Triangulation(x * 1e3, radius * 1e3, triangles[keep])

    fig, axes = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True, sharey=True)
    fields = [
        ("Mach", arrays["Mach"], 0.0, 4.5, "turbo", "Mach number"),
        ("Temperature", arrays["Temperature"], 250.0, 4000.0, "inferno", "Temperature [K]"),
    ]
    for axis, (_, values, vmin, vmax, cmap, label) in zip(axes, fields):
        image = axis.tripcolor(
            triangulation,
            values,
            shading="gouraud",
            cmap=cmap,
            vmin=vmin,
            vmax=vmax,
            rasterized=True,
        )
        fig.colorbar(image, ax=axis, label=label, pad=0.01)
        axis.set_ylabel("r [mm]")
        axis.set_xlim(-23.0, args.x_max * 1e3)
        axis.set_ylim(0.0, args.r_max * 1e3)
        axis.set_aspect("equal")
        axis.grid(False)

    max_temperature_index = int(np.nanargmax(arrays["Temperature"]))
    axes[1].plot(
        x[max_temperature_index] * 1e3,
        radius[max_temperature_index] * 1e3,
        marker="x",
        color="cyan",
        markersize=8,
        markeredgewidth=2,
        label=f"Tmax = {arrays['Temperature'][max_temperature_index]:.0f} K",
    )
    axes[1].legend(loc="upper right")
    axes[1].set_xlabel("x [mm]")
    axes[0].set_title(f"NPR 20 URANS near field: {args.vtk.name}")
    fig.tight_layout()
    fig.savefig(args.output, dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    main()
