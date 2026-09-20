import csv
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parent
WALL_VTK = ROOT / "wall.vtk"
FLOW_VTK = ROOT / "flow.vtk"
THROAT_X = 0.0
NOZZLE_EXIT_X = 0.2


def read_legacy_vtk(path: Path) -> tuple[list[tuple[float, float, float]], dict[str, list]]:
    tokens = path.read_text(encoding="ascii").split()
    points_index = tokens.index("POINTS")
    n_points = int(tokens[points_index + 1])
    start = points_index + 3
    coordinates = [
        tuple(float(value) for value in tokens[i : i + 3])
        for i in range(start, start + 3 * n_points, 3)
    ]

    arrays: dict[str, list] = {}
    i = 0
    while i < len(tokens):
        if tokens[i] == "SCALARS" and i + 5 < len(tokens):
            name = tokens[i + 1]
            components = int(tokens[i + 3])
            data_start = i + 6
            values = [float(value) for value in tokens[data_start : data_start + n_points * components]]
            arrays[name] = values if components == 1 else [
                tuple(values[j : j + components])
                for j in range(0, len(values), components)
            ]
            i = data_start + n_points * components
            continue
        if tokens[i] == "VECTORS" and i + 2 < len(tokens):
            name = tokens[i + 1]
            data_start = i + 3
            values = [float(value) for value in tokens[data_start : data_start + 3 * n_points]]
            arrays[name] = [tuple(values[j : j + 3]) for j in range(0, len(values), 3)]
            i = data_start + 3 * n_points
            continue
        i += 1
    return coordinates, arrays


def interpolate_zero(left: dict[str, float], right: dict[str, float]) -> float:
    fraction = -left["cf_t"] / (right["cf_t"] - left["cf_t"])
    return left["x"] + fraction * (right["x"] - left["x"])


def wall_analysis() -> tuple[list[dict[str, float]], list[float], list[float]]:
    points, arrays = read_legacy_vtk(WALL_VTK)
    skin_friction = arrays["Skin_Friction_Coefficient"]
    pressure = arrays["Pressure"]
    y_plus = arrays["Y_Plus"]
    rows = [
        {
            "x": point[0],
            "r": point[1],
            "cfx": cf[0],
            "cfr": cf[1],
            "pressure": p,
            "yplus": yp,
        }
        for point, cf, p, yp in zip(points, skin_friction, pressure, y_plus)
    ]
    rows.sort(key=lambda row: row["x"])

    for i, row in enumerate(rows):
        left = rows[max(0, i - 1)]
        right = rows[min(len(rows) - 1, i + 1)]
        slope = (right["r"] - left["r"]) / max(right["x"] - left["x"], 1e-30)
        tangent_norm = math.sqrt(1.0 + slope * slope)
        row["cf_t"] = (row["cfx"] + slope * row["cfr"]) / tangent_norm

    divergent = [row for row in rows if THROAT_X <= row["x"] <= NOZZLE_EXIT_X]
    separations: list[float] = []
    reattachments: list[float] = []
    for left, right in zip(divergent, divergent[1:]):
        if left["cf_t"] > 0.0 and right["cf_t"] <= 0.0:
            separations.append(interpolate_zero(left, right))
        if left["cf_t"] < 0.0 and right["cf_t"] >= 0.0:
            reattachments.append(interpolate_zero(left, right))
    return divergent, separations, reattachments


def centerline_analysis() -> tuple[list[dict[str, float]], dict[str, float], dict[str, float]]:
    points, arrays = read_legacy_vtk(FLOW_VTK)
    mach = arrays["Mach"]
    pressure = arrays["Pressure"]
    rows = [
        {"x": point[0], "r": point[1], "mach": m, "pressure": p}
        for point, m, p in zip(points, mach, pressure)
    ]
    min_radius_by_x: dict[float, dict[str, float]] = {}
    for row in rows:
        key = round(row["x"], 10)
        if key not in min_radius_by_x or row["r"] < min_radius_by_x[key]["r"]:
            min_radius_by_x[key] = row
    centerline = sorted(min_radius_by_x.values(), key=lambda row: row["x"])
    divergent = [row for row in centerline if THROAT_X <= row["x"] <= NOZZLE_EXIT_X]

    shock = {"x": float("nan"), "gradient": 0.0}
    for left, right in zip(divergent, divergent[1:]):
        gradient = (right["pressure"] - left["pressure"]) / (right["x"] - left["x"])
        if gradient > shock["gradient"]:
            shock = {"x": 0.5 * (left["x"] + right["x"]), "gradient": gradient}
    max_index = max(range(len(mach)), key=mach.__getitem__)
    global_max = {
        "mach": mach[max_index],
        "x": points[max_index][0],
        "r": points[max_index][1],
    }
    return centerline, shock, global_max


def nearest(rows: list[dict[str, float]], x: float) -> dict[str, float]:
    return min(rows, key=lambda row: abs(row["x"] - x))


def main() -> None:
    wall, separations, reattachments = wall_analysis()
    centerline, shock, global_max = centerline_analysis()
    y_plus = sorted(abs(row["yplus"]) for row in wall if math.isfinite(row["yplus"]))
    max_mach = max(row["mach"] for row in centerline)
    throat = nearest(centerline, THROAT_X)
    exit_state = nearest(centerline, NOZZLE_EXIT_X)
    domain_outlet = max(centerline, key=lambda row: row["x"])

    print(f"Global max Mach: {global_max['mach']:.4f} at x={global_max['x']:.8f} m, r={global_max['r']:.8f} m")
    print(f"Centerline max Mach: {max_mach:.4f}")
    print(f"Centerline throat Mach: {throat['mach']:.4f}")
    print(f"Centerline exit Mach / pressure: {exit_state['mach']:.4f} / {exit_state['pressure']:.2f} Pa")
    print(
        "Domain outlet x / Mach / pressure: "
        f"{domain_outlet['x']:.4f} m / {domain_outlet['mach']:.4f} / "
        f"{domain_outlet['pressure']:.2f} Pa"
    )
    print(f"Strongest centerline pressure rise x: {shock['x']:.8f} m")
    print(f"Wall Cf_t range: {min(r['cf_t'] for r in wall):.6e} to {max(r['cf_t'] for r in wall):.6e}")
    print(f"Wall y+ median/max: {y_plus[len(y_plus) // 2]:.3f} / {max(y_plus):.3f}")
    print("Separation x [m]: " + (", ".join(f"{x:.8f}" for x in separations) or "none"))
    print("Reattachment x [m]: " + (", ".join(f"{x:.8f}" for x in reattachments) or "none"))

    output_path = ROOT / "wall_cf_processed.csv"
    with output_path.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=("x", "r", "cf_t", "pressure", "yplus"))
        writer.writeheader()
        writer.writerows({key: row[key] for key in writer.fieldnames} for row in wall)
    print(f"Processed wall data: {output_path}")


if __name__ == "__main__":
    main()
