import argparse
import csv
import json
from pathlib import Path

import gmsh


HERE = Path(__file__).resolve().parent
CONTOUR = HERE.parent.parent / "DLR_PAR_full_contour.csv"

PROFILES = {
    "screen": {"axial_cells": 600, "radial_cells": 128, "first_wall_cell_m": 1.0e-6},
    "pilot": {"axial_cells": 800, "radial_cells": 128, "first_wall_cell_m": 1.0e-6},
    "medium": {"axial_cells": 1600, "radial_cells": 200, "first_wall_cell_m": 5.0e-7},
    "fine": {"axial_cells": 3200, "radial_cells": 320, "first_wall_cell_m": 2.5e-7},
}


def read_contour(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    return [(float(row["x_mm"]) * 1e-3, float(row["r_mm"]) * 1e-3) for row in rows]


def growth_ratio(first_cell, total_length, cells):
    if first_cell * cells >= total_length:
        return 1.0
    low, high = 1.0, 2.0
    for _ in range(100):
        ratio = 0.5 * (low + high)
        length = first_cell * (ratio**cells - 1.0) / (ratio - 1.0)
        if length < total_length:
            low = ratio
        else:
            high = ratio
    return 0.5 * (low + high)


def main():
    parser = argparse.ArgumentParser(description="Create a structured internal DLR-PAR nozzle mesh.")
    parser.add_argument("--profile", choices=PROFILES, default="pilot")
    args = parser.parse_args()
    settings = PROFILES[args.profile]
    contour = read_contour(CONTOUR)
    x_inlet, r_inlet = contour[0]
    x_exit, r_exit = contour[-1]
    output_dir = HERE / args.profile
    output_dir.mkdir(parents=True, exist_ok=True)

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add(f"dlr_par_internal_{args.profile}")

    wall_points = [gmsh.model.geo.addPoint(x, r, 0.0) for x, r in contour]
    inlet_axis_point = gmsh.model.geo.addPoint(x_inlet, 0.0, 0.0)
    exit_axis_point = gmsh.model.geo.addPoint(x_exit, 0.0, 0.0)
    axis = gmsh.model.geo.addLine(inlet_axis_point, exit_axis_point)
    outlet = gmsh.model.geo.addLine(wall_points[-1], exit_axis_point)
    wall = gmsh.model.geo.addSpline(list(reversed(wall_points)))
    inlet = gmsh.model.geo.addLine(wall_points[0], inlet_axis_point)
    loop = gmsh.model.geo.addCurveLoop([axis, -outlet, wall, inlet])
    surface = gmsh.model.geo.addPlaneSurface([loop])
    gmsh.model.geo.synchronize()

    for dimension, entities, name in (
        (1, [wall], "WALL"),
        (1, [inlet], "INLET"),
        (1, [axis], "AXIS"),
        (1, [outlet], "OUTLET"),
        (2, [surface], "FLUID"),
    ):
        tag = gmsh.model.addPhysicalGroup(dimension, entities)
        gmsh.model.setPhysicalName(dimension, tag, name)

    axial_nodes = settings["axial_cells"] + 1
    radial_nodes = settings["radial_cells"] + 1
    inlet_growth = growth_ratio(settings["first_wall_cell_m"], r_inlet, settings["radial_cells"])
    exit_growth = growth_ratio(settings["first_wall_cell_m"], r_exit, settings["radial_cells"])
    gmsh.model.mesh.setTransfiniteCurve(axis, axial_nodes)
    gmsh.model.mesh.setTransfiniteCurve(wall, axial_nodes)
    gmsh.model.mesh.setTransfiniteCurve(inlet, radial_nodes, "Progression", inlet_growth)
    gmsh.model.mesh.setTransfiniteCurve(outlet, radial_nodes, "Progression", exit_growth)
    gmsh.model.mesh.setTransfiniteSurface(
        surface,
        "Left",
        [inlet_axis_point, exit_axis_point, wall_points[-1], wall_points[0]],
    )
    gmsh.model.mesh.setRecombine(2, surface)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.model.mesh.generate(2)

    element_types, element_tags, _ = gmsh.model.mesh.getElements(2)
    element_counts = {
        gmsh.model.mesh.getElementProperties(element_type)[0]: len(tags)
        for element_type, tags in zip(element_types, element_tags)
    }
    all_2d_tags = [tag for tags in element_tags for tag in tags]
    qualities = gmsh.model.mesh.getElementQualities(all_2d_tags, "minSJ")
    node_tags, _, _ = gmsh.model.mesh.getNodes()

    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.Binary", 0)
    gmsh.write(str(output_dir / "dlr_par_internal.msh"))
    gmsh.write(str(output_dir / "dlr_par_internal.su2"))
    summary = {
        "profile": args.profile,
        "purpose": "equilibrium-products internal-nozzle RANS",
        "topology": "wall-normal clustered structured quadrilaterals",
        "contour_file": str(CONTOUR),
        "settings": settings,
        "inlet_growth_ratio": inlet_growth,
        "exit_growth_ratio": exit_growth,
        "nodes": len(node_tags),
        "elements_2d": element_counts,
        "min_scaled_jacobian": min(qualities),
        "mean_scaled_jacobian": sum(qualities) / len(qualities),
        "boundaries": ["WALL", "INLET", "AXIS", "OUTLET"],
    }
    (output_dir / "mesh_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    print(json.dumps(summary, indent=2))
    gmsh.finalize()


if __name__ == "__main__":
    main()
