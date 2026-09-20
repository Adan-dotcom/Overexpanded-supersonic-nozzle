import argparse
import csv
import json
from pathlib import Path

import gmsh


HERE = Path(__file__).resolve().parent
CONTOUR = HERE.parent.parent / "DLR_PAR_full_contour.csv"

PROFILES = {
    "pilot": {
        "h_nozzle": 5.0e-4,
        "h_shock": 2.5e-4,
        "h_plume": 1.0e-3,
        "h_far": 2.0e-2,
        "h1": 2.0e-6,
        "bl_thickness": 1.0e-3,
        "bl_ratio": 1.15,
    },
    "medium": {
        "h_nozzle": 1.5e-4,
        "h_shock": 7.5e-5,
        "h_plume": 3.0e-4,
        "h_far": 1.0e-2,
        "h1": 5.0e-7,
        "bl_thickness": 1.5e-3,
        "bl_ratio": 1.079,
    },
}


def read_contour(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    return [(float(row["x_mm"]) * 1e-3, float(row["r_mm"]) * 1e-3) for row in rows]


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
    parser = argparse.ArgumentParser(description="Mesh the DLR-PAR nozzle plus a downstream ambient domain.")
    parser.add_argument("--profile", choices=PROFILES, default="pilot")
    parser.add_argument("--corner-treatment", choices=("trimmed", "fan"), default="trimmed")
    args = parser.parse_args()
    settings = PROFILES[args.profile]
    contour = read_contour(CONTOUR)
    x_inlet, r_inlet = contour[0]
    x_exit, r_exit = contour[-1]
    exit_diameter = 2.0 * r_exit
    x_far = x_exit + 10.0 * exit_diameter
    r_far = 5.0 * exit_diameter
    output_name = args.profile if args.corner_treatment == "trimmed" else f"{args.profile}_fan"
    output_dir = HERE / output_name
    output_dir.mkdir(parents=True, exist_ok=True)

    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    gmsh.model.add(f"dlr_par_ambient_{args.profile}")

    wall_points = [gmsh.model.geo.addPoint(x, r, 0.0) for x, r in contour]
    bl_start = next(i for i, (x, _) in enumerate(contour) if x >= x_inlet + 1.0e-3)
    bl_end = max(i for i, (x, _) in enumerate(contour) if x <= x_exit - 5.0e-4)
    p_inlet_axis = gmsh.model.geo.addPoint(x_inlet, 0.0, 0.0)
    p_far_axis = gmsh.model.geo.addPoint(x_far, 0.0, 0.0)
    p_far_top = gmsh.model.geo.addPoint(x_far, r_far, 0.0)
    p_exit_top = gmsh.model.geo.addPoint(x_exit, r_far, 0.0)

    axis = gmsh.model.geo.addLine(p_inlet_axis, p_far_axis)
    far_outlet = gmsh.model.geo.addLine(p_far_axis, p_far_top)
    far_top = gmsh.model.geo.addLine(p_far_top, p_exit_top)
    ambient_inlet = gmsh.model.geo.addLine(p_exit_top, wall_points[-1])
    if args.corner_treatment == "fan":
        wall_bl = gmsh.model.geo.addSpline(list(reversed(wall_points)))
        wall_curves = [wall_bl]
        bl_range = [x_inlet, x_exit]
    else:
        wall_exit_cap = gmsh.model.geo.addSpline(list(reversed(wall_points[bl_end:])))
        wall_bl = gmsh.model.geo.addSpline(list(reversed(wall_points[bl_start:bl_end + 1])))
        wall_inlet_cap = gmsh.model.geo.addSpline(list(reversed(wall_points[:bl_start + 1])))
        wall_curves = [wall_exit_cap, wall_bl, wall_inlet_cap]
        bl_range = [contour[bl_start][0], contour[bl_end][0]]
    inlet = gmsh.model.geo.addLine(wall_points[0], p_inlet_axis)
    loop = gmsh.model.geo.addCurveLoop(
        [axis, far_outlet, far_top, ambient_inlet, *wall_curves, inlet]
    )
    surface = gmsh.model.geo.addPlaneSurface([loop])
    gmsh.model.geo.synchronize()

    for dim, entities, name in (
        (1, wall_curves, "WALL"),
        (1, [inlet], "INLET"),
        (1, [axis], "AXIS"),
        (1, [far_outlet, far_top, ambient_inlet], "FARFIELD"),
        (2, [surface], "FLUID"),
    ):
        physical = gmsh.model.addPhysicalGroup(dim, entities)
        gmsh.model.setPhysicalName(dim, physical, name)

    distance = gmsh.model.mesh.field.add("Distance")
    gmsh.model.mesh.field.setNumbers(distance, "CurvesList", wall_curves)
    gmsh.model.mesh.field.setNumber(distance, "Sampling", 1200)
    wall_threshold = gmsh.model.mesh.field.add("Threshold")
    gmsh.model.mesh.field.setNumber(wall_threshold, "InField", distance)
    gmsh.model.mesh.field.setNumber(wall_threshold, "SizeMin", settings["h_shock"])
    gmsh.model.mesh.field.setNumber(wall_threshold, "SizeMax", settings["h_far"])
    gmsh.model.mesh.field.setNumber(wall_threshold, "DistMin", 2.0e-3)
    gmsh.model.mesh.field.setNumber(wall_threshold, "DistMax", 15.0e-3)

    nozzle_box = add_box(
        settings["h_nozzle"], settings["h_far"], x_inlet - 1e-6, x_exit, 0.0, r_exit + 0.01
    )
    shock_box = add_box(
        settings["h_shock"], settings["h_far"], 0.08, x_exit + 0.02, 0.0, r_exit + 0.02
    )
    plume_box = add_box(
        settings["h_plume"], settings["h_far"], x_exit, x_exit + 3.0 * exit_diameter, 0.0, 1.5 * exit_diameter
    )
    background = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(
        background, "FieldsList", [wall_threshold, nozzle_box, shock_box, plume_box]
    )
    gmsh.model.mesh.field.setAsBackgroundMesh(background)

    boundary_layer = gmsh.model.mesh.field.add("BoundaryLayer")
    gmsh.model.mesh.field.setNumbers(boundary_layer, "CurvesList", [wall_bl])
    gmsh.model.mesh.field.setNumber(boundary_layer, "Size", settings["h1"])
    gmsh.model.mesh.field.setNumber(boundary_layer, "Ratio", settings["bl_ratio"])
    gmsh.model.mesh.field.setNumber(boundary_layer, "Thickness", settings["bl_thickness"])
    gmsh.model.mesh.field.setNumber(boundary_layer, "Quads", 1)
    if args.corner_treatment == "fan":
        gmsh.option.setNumber("Mesh.BoundaryLayerFanElements", 12)
        gmsh.model.mesh.field.setNumbers(
            boundary_layer, "FanPointsList", [wall_points[0], wall_points[-1]]
        )
    gmsh.model.mesh.field.setAsBoundaryLayer(boundary_layer)

    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MinimumCirclePoints", 20)
    gmsh.model.mesh.generate(2)

    element_types, element_tags, _ = gmsh.model.mesh.getElements(2, surface)
    element_counts = {
        gmsh.model.mesh.getElementProperties(element_type)[0]: len(tags)
        for element_type, tags in zip(element_types, element_tags)
    }
    all_2d_tags = [tag for tags in element_tags for tag in tags]
    qualities = gmsh.model.mesh.getElementQualities(all_2d_tags, "minSJ")
    node_tags, _, _ = gmsh.model.mesh.getNodes()

    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.Binary", 0)
    gmsh.write(str(output_dir / "dlr_par_ambient.msh"))
    gmsh.write(str(output_dir / "dlr_par_ambient.su2"))
    summary = {
        "profile": args.profile,
        "corner_treatment": args.corner_treatment,
        "purpose": "topology validation" if args.profile == "pilot" else "grid-convergence candidate",
        "contour_file": str(CONTOUR),
        "x_far_m": x_far,
        "r_far_m": r_far,
        "exit_diameter_m": exit_diameter,
        "downstream_extent_exit_diameters": 10.0,
        "radial_extent_exit_diameters": 5.0,
        "settings": settings,
        "boundary_layer_x_range_m": bl_range,
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
