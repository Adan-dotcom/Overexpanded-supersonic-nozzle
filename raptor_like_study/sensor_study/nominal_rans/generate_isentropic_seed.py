import csv
import math
from pathlib import Path

from scipy.interpolate import PchipInterpolator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEMPLATE = HERE / "seed_template.csv"
OUTPUT = HERE / "restart_isentropic.csv"
GEOMETRY = ROOT / "DLR_PAR_full_contour.csv"

GAMMA = 1.1982940938
GAS_CONSTANT = 390.5997546790
P0 = 5_200_000.0
T0 = 3485.33
R_THROAT = 0.010


def area_mach(mach):
    term = 2.0 / (GAMMA + 1.0) * (1.0 + 0.5 * (GAMMA - 1.0) * mach * mach)
    return term ** ((GAMMA + 1.0) / (2.0 * (GAMMA - 1.0))) / mach


def mach_from_area(area_ratio, supersonic):
    lo, hi = ((1.0, 12.0) if supersonic else (1.0e-6, 1.0))
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if supersonic:
            if area_mach(mid) < area_ratio:
                lo = mid
            else:
                hi = mid
        elif area_mach(mid) > area_ratio:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def main():
    with GEOMETRY.open(newline="", encoding="ascii") as stream:
        geometry = list(csv.DictReader(stream))
    gx = [float(row["x_mm"]) * 1e-3 for row in geometry]
    gr = [float(row["r_mm"]) * 1e-3 for row in geometry]
    radius = PchipInterpolator(gx, gr)

    with TEMPLATE.open(newline="", encoding="ascii") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        fields = reader.fieldnames
    for row in rows:
        x = float(row["x"])
        local_area = max((float(radius(x)) / R_THROAT) ** 2, 1.0)
        mach = mach_from_area(local_area, supersonic=x >= 0.0)
        factor = 1.0 + 0.5 * (GAMMA - 1.0) * mach * mach
        temperature = T0 / factor
        pressure = P0 / factor ** (GAMMA / (GAMMA - 1.0))
        density = pressure / (GAS_CONSTANT * temperature)
        velocity = mach * math.sqrt(GAMMA * GAS_CONSTANT * temperature)
        row["Density"] = f"{density:.15e}"
        row["Momentum_x"] = f"{density * velocity:.15e}"
        row["Momentum_y"] = "0.000000000000000e+00"
        row["Energy"] = f"{pressure / (GAMMA - 1.0) + 0.5 * density * velocity**2:.15e}"
    with OUTPUT.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    exit_area = (gr[-1] / R_THROAT) ** 2
    exit_mach = mach_from_area(exit_area, True)
    exit_factor = 1.0 + 0.5 * (GAMMA - 1.0) * exit_mach**2
    exit_pressure = P0 / exit_factor ** (GAMMA / (GAMMA - 1.0))
    print(f"Wrote {OUTPUT}")
    print(f"Ideal exit: M={exit_mach:.4f}, p={exit_pressure:.1f} Pa")


if __name__ == "__main__":
    main()
