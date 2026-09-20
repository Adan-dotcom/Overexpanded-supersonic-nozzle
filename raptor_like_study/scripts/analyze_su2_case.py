import argparse
import csv
import json
import math
from pathlib import Path


def read_vtk(path):
    tokens = path.read_text(encoding="ascii").split()
    p = tokens.index("POINTS")
    n = int(tokens[p + 1])
    points = [tuple(map(float, tokens[i:i + 3])) for i in range(p + 3, p + 3 * n, 3)]
    arrays = {}
    i = 0
    while i < len(tokens):
        if tokens[i] == "SCALARS":
            name, comps = tokens[i + 1], int(tokens[i + 3])
            start = i + 6
            vals = list(map(float, tokens[start:start + n * comps]))
            arrays[name] = vals if comps == 1 else [tuple(vals[j:j + comps]) for j in range(0, len(vals), comps)]
            i = start + n * comps
        elif tokens[i] == "VECTORS":
            name, start = tokens[i + 1], i + 3
            vals = list(map(float, tokens[start:start + 3 * n]))
            arrays[name] = [tuple(vals[j:j + 3]) for j in range(0, len(vals), 3)]
            i = start + 3 * n
        else:
            i += 1
    return points, arrays


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case-id", default="case_0001")
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[1] / "cases" / "su2" / args.case_id
    points, a = read_vtk(root / "wall.vtk")
    cf = a["Skin_Friction_Coefficient"]
    pressure = a["Pressure"]
    yp = a["Y_Plus"]
    rows = []
    for point, vec, p, y in zip(points, cf, pressure, yp):
        rows.append({"x": point[0], "r": point[1], "cfx": vec[0], "cfr": vec[1], "pressure_pa": p, "yplus": y})
    rows.sort(key=lambda r: r["x"])
    for i, row in enumerate(rows):
        left, right = rows[max(0, i - 1)], rows[min(len(rows) - 1, i + 1)]
        slope = (right["r"] - left["r"]) / max(right["x"] - left["x"], 1e-30)
        row["cf_t"] = (row["cfx"] + slope * row["cfr"]) / math.sqrt(1 + slope * slope)
    div = [r for r in rows if 0 <= r["x"] <= max(r["x"] for r in rows)]
    sep, reattach = [], []
    for left, right in zip(div, div[1:]):
        if left["x"] < 0 or right["x"] < 0:
            continue
        if left["cf_t"] > 0 >= right["cf_t"]:
            sep.append(left["x"] - left["cf_t"] * (right["x"] - left["x"]) / (right["cf_t"] - left["cf_t"]))
        if left["cf_t"] < 0 <= right["cf_t"]:
            reattach.append(left["x"] - left["cf_t"] * (right["x"] - left["x"]) / (right["cf_t"] - left["cf_t"]))
    with (root / "wall_processed.csv").open("w", newline="", encoding="ascii") as f:
        writer = csv.DictWriter(f, fieldnames=("x", "r", "cf_t", "pressure_pa", "yplus"))
        writer.writeheader()
        writer.writerows({k: row[k] for k in writer.fieldnames} for row in rows)
    result = {"case_id": args.case_id, "x_sep_m": sep[0] if sep else None, "x_reattach_m": reattach[0] if reattach else None,
              "cf_min": min(r["cf_t"] for r in rows), "cf_max": max(r["cf_t"] for r in rows),
              "yplus_median": sorted(r["yplus"] for r in rows)[len(rows) // 2], "yplus_max": max(r["yplus"] for r in rows)}
    (root / "separation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
