import argparse
import csv
import json
from pathlib import Path

import gmsh


HERE = Path(__file__).resolve().parent
CONTOUR = HERE.parent.parent / "DLR_PAR_full_contour.csv"

PROFILES = {
    "pilot": {
        "axial_cells": 800,
        "radial_cells": 128,
        "first_wall_cell_m": 1.0e-6,
        "h_lip": 2.0e-5,
        "h_near": 2.5e-4,
        "h_plume": 1.0e-3,
        "h_far": 2.0e-2,
    },
    "medium": {
        "axial_cells": 1600,
        "radial_cells": 200,
        "first_wall_cell_m": 5.0e-7,
        "h_lip": 1.0e-5,
        "h_near": 1.0e-4,
        "h_plume": 4.0e-4,
        "h_far": 1.0e-2,
    },
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


def add_box(value_in, value_out, xmin, xmax, ymin, ymax):
    tag = gmsh.model.mesh.field.add("Box")
    for key, value in {
        "VIn": value_in,
        "VOut": value_out,
        "XMin": xmin,
        "XMax": xmax,
        "YMin": ymin,
        "YMax": ymax,
        "Thickness": 0.0,
    }.items():
        gmsh.model.mesh.field.setNumber(tag, key, value)
    return tag


def main():
    parser = argparse.ArgumentParser(description="Create a conformal structured-nozzle/unstructured-ambient mesh.")
    parser.add_argument("--profile", choices=PROFILES, default="pilot")
    args = parser.parse_args()
    settings = PROFILES[args.profile]
    contour = read_contour(CONTOUR)
    x_inlet, r_inlet = contour[0]
    x_exit, r_exit = contour[-1]
    exit_diameter = 2.0 * r_exit
    x_far = x_exit + 10.0 * exit_diameter
    r_far = 5.0 * exit_diameter
    output_dir = HERE / f"hybrid_{args.profile}"
    output_dir.mkdir(parents=True, exist_ok=True)

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add(f"dlr_par_hybrid_{args.profile}")

    wall_points = [gmsh.model.geo.addPoint(x, r, 0.0) for x, r in contour]
    p_inlet_axis = gmsh.model.geo.addPoint(x_inlet, 0.0, 0.0)
    p_exit_axis = gmsh.model.geo.addPoint(x_exit, 0.0, 0.0)
    p_far_axis = gmsh.model.geo.addPoint(x_far, 0.0, 0.0)
    p_far_top = gmsh.model.geo.addPoint(x_far, r_far, 0.0)
    p_exit_top = gmsh.model.geo.addPoint(x_exit, r_far, 0.0)

    nozzle_axis = gmsh.model.geo.addLine(p_inlet_axis, p_exit_axis)
    ambient_axis = gmsh.model.geo.addLine(p_exit_axis, p_far_axis)
    far_outlet = gmsh.model.geo.addLine(p_far_axis, p_far_top)
    far_top = gmsh.model.geo.addLine(p_far_top, p_exit_top)
    ambient_inlet = gmsh.model.geo.addLine(p_exit_top, wall_points[-1])
    interface = gmsh.model.geo.addLine(wall_points[-1], p_exit_axis)
    wall = gmsh.model.geo.addSpline(list(reversed(wall_points)))
    inlet = gmsh.model.geo.addLine(wall_points[0], p_inlet_axis)

    nozzle_loop = gmsh.model.geo.addCurveLoop([nozzle_axis, -interface, wall, inlet])
    ambient_loop = gmsh.model.geo.addCurveLoop(
        [ambient_axis, far_outlet, far_top, ambient_inlet, interface]
    )
    nozzle_surface = gmsh.model.geo.addPlaneSurface([nozzle_loop])
    ambient_surface = gmsh.model.geo.addPlaneSurface([ambient_loop])
    gmsh.model.geo.synchronize()

    for dim, entities, name in (
        (1, [wall], "WALL"),
        (1, [inlet], "INLET"),
        (1, [nozzle_axis, ambient_axis], "AXIS"),
        (1, [far_outlet, far_top, ambient_inlet], "FARFIELD"),
        (2, [nozzle_surface, ambient_surface], "FLUID"),
    ):
        physical = gmsh.model.addPhysicalGroup(dim, entities)
        gmsh.model.setPhysicalName(dim, physical, name)

    axial_nodes = settings["axial_cells"] + 1
    radial_nodes = settings["radial_cells"] + 1
    inlet_growth = growth_ratio(
        settings["first_wall_cell_m"], r_inlet, settings["radial_cells"]
    )
    exit_growth = growth_ratio(
        settings["first_wall_cell_m"], r_exit, settings["radial_cells"]
    )
    gmsh.model.mesh.setTransfiniteCurve(nozzle_axis, axial_nodes)
    gmsh.model.mesh.setTransfiniteCurve(wall, axial_nodes)
    gmsh.model.mesh.setTransfiniteCurve(inlet, radial_nodes, "Progression", inlet_growth)
    gmsh.model.mesh.setTransfiniteCurve(interface, radial_nodes, "Progression", exit_growth)
    gmsh.model.mesh.setTransfiniteSurface(
        nozzle_surface,
        "Left",
        [p_inlet_axis, p_exit_axis, wall_points[-1], wall_points[0]],
    )
    gmsh.model.mesh.setRecombine(2, nozzle_surface)

    lip_distance = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(lip_distance, "PointsList", [wall_points[-1]])
    lip_threshold = gmsh.model.mesh.field.add("Threshold")
    gmsh.model.mesh.field.setNumber(lip_threshold, "InField", lip_distance)
    gmsh.model.mesh.field.setNumber(lip_threshold, "SizeMin", settings["h_lip"])
    gmsh.model.mesh.field.setNumber(lip_threshold, "SizeMax", settings["h_far"])
    gmsh.model.mesh.field.setNumber(lip_threshold, "DistMin", 5.0e-5)
    gmsh.model.mesh.field.setNumber(lip_threshold, "DistMax", 5.0e-3)
    near_box = add_box(
        settings["h_near"], settings["h_far"], x_exit, x_exit + 0.03, 0.0, r_exit + 0.03
    )
    plume_box = add_box(
        settings["h_plume"],
        settings["h_far"],
        x_exit,
        x_exit + 3.0 * exit_diameter,
        0.0,
        1.5 * exit_diameter,
    )
    background = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(background, "FieldsList", [lip_threshold, near_box, plume_box])
    gmsh.model.mesh.field.setAsBackgroundMesh(background)

    gmsh.option.setNumber("Mesh.Algorithm", 6)
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
    gmsh.write(str(output_dir / "dlr_par_hybrid.msh"))
    gmsh.write(str(output_dir / "dlr_par_hybrid.su2"))
    summary = {
        "profile": args.profile,
        "purpose": "topology validation" if args.profile == "pilot" else "grid-convergence candidate",
        "topology": "transfinite quadrilateral nozzle plus conformal triangular ambient domain",
        "contour_file": str(CONTOUR),
        "x_far_m": x_far,
        "r_far_m": r_far,
        "exit_diameter_m": exit_diameter,
        "downstream_extent_exit_diameters": 10.0,
        "radial_extent_exit_diameters": 5.0,
        "settings": settings,
        "inlet_growth_ratio": inlet_growth,
        "exit_growth_ratio": exit_growth,
        "nodes": len(node_tags),
        "elements_2d": element_counts,
        "min_scaled_jacobian": min(qualities),
        "mean_scaled_jacobian": sum(qualities) / len(qualities),
        "boundaries": ["WALL", "INLET", "AXIS", "FARFIELD"],
    }
    (output_dir / "mesh_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")
    print(json.dumps(summary, indent=2))
    gmsh.finalize()


if __name__ == "__main__":
    main()
