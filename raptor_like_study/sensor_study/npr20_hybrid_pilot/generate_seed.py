import csv
import math
from pathlib import Path

from scipy.interpolate import PchipInterpolator


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MESH = ROOT / "raptor_like_study" / "ambient_mesh" / "hybrid_pilot" / "dlr_par_hybrid.su2"
GEOMETRY = ROOT / "DLR_PAR_full_contour.csv"
OUTPUT = HERE / "restart_npr20_seed.csv"

GAMMA = 1.1982940938
GAS_CONSTANT = 390.5997546790
P0 = 5_200_000.0
T0 = 3485.33
P_AMBIENT = 260_000.0
T_AMBIENT = 300.0
MACH_AMBIENT = 0.001
R_THROAT = 0.010
MU_REF = 1.0707e-4
T_REF = 3312.09
SUTHERLAND = 683.0362
TURBULENCE_INTENSITY = 0.01
TURB2LAM_RATIO = 10.0


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


def primitive_from_mach(mach):
    factor = 1.0 + 0.5 * (GAMMA - 1.0) * mach * mach
    temperature = T0 / factor
    pressure = P0 / factor ** (GAMMA / (GAMMA - 1.0))
    velocity = mach * math.sqrt(GAMMA * GAS_CONSTANT * temperature)
    return pressure, temperature, velocity


def conservative(pressure, temperature, velocity):
    density = pressure / (GAS_CONSTANT * temperature)
    momentum = density * velocity
    energy = pressure / (GAMMA - 1.0) + 0.5 * density * velocity**2
    viscosity = MU_REF * (temperature / T_REF) ** 1.5 * (T_REF + SUTHERLAND) / (temperature + SUTHERLAND)
    tke = max(1.5 * (TURBULENCE_INTENSITY * velocity) ** 2, 1.0e-10)
    omega = max(density * tke / (TURB2LAM_RATIO * viscosity), 1.0e-6)
    return density, momentum, energy, tke, omega


def read_mesh_points(path):
    with path.open(encoding="ascii") as stream:
        while True:
            line = stream.readline()
            if not line:
                raise RuntimeError("NPOIN not found in SU2 mesh")
            if line.startswith("NPOIN="):
                count = int(line.split("=", 1)[1])
                break
        points = []
        for _ in range(count):
            values = stream.readline().split()
            points.append((int(values[2]), float(values[0]), float(values[1])))
    return points


def main():
    with GEOMETRY.open(newline="", encoding="utf-8-sig") as stream:
        geometry = list(csv.DictReader(stream))
    gx = [float(row["x_mm"]) * 1e-3 for row in geometry]
    gr = [float(row["r_mm"]) * 1e-3 for row in geometry]
    radius = PchipInterpolator(gx, gr)
    x_exit, r_exit = gx[-1], gr[-1]

    exit_mach = mach_from_area((r_exit / R_THROAT) ** 2, True)
    exit_primitive = primitive_from_mach(exit_mach)
    ambient_velocity = MACH_AMBIENT * math.sqrt(GAMMA * GAS_CONSTANT * T_AMBIENT)
    ambient_primitive = (P_AMBIENT, T_AMBIENT, ambient_velocity)
    points = read_mesh_points(MESH)

    with OUTPUT.open("w", newline="", encoding="ascii") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ("PointID", "x", "y", "Density", "Momentum_x", "Momentum_y", "Energy", "Turb_Kin_Energy", "Omega")
        )
        for point_id, x, y in points:
            # Mesh-wall coordinates and the reconstructed spline differ by a
            # few nanometres; 0.1 um remains below the 1 um first wall cell.
            inside_nozzle = x <= x_exit + 1.0e-12 and y <= float(radius(min(x, x_exit))) + 1.0e-7
            initial_jet = x > x_exit and x <= x_exit + 3.0 * (2.0 * r_exit) and y <= r_exit
            if inside_nozzle:
                area_ratio = max((float(radius(x)) / R_THROAT) ** 2, 1.0)
                primitive = primitive_from_mach(mach_from_area(area_ratio, x >= 0.0))
            elif initial_jet:
                primitive = exit_primitive
            else:
                primitive = ambient_primitive
            density, momentum, energy, tke, omega = conservative(*primitive)
            writer.writerow(
                (
                    point_id,
                    f"{x:.15e}",
                    f"{y:.15e}",
                    f"{density:.15e}",
                    f"{momentum:.15e}",
                    "0.000000000000000e+00",
                    f"{energy:.15e}",
                    f"{tke:.15e}",
                    f"{omega:.15e}",
                )
            )
    print(f"Wrote {OUTPUT} with {len(points)} points")
    print(f"Ideal exit seed: M={exit_mach:.4f}, p={exit_primitive[0]:.1f} Pa, ambient={P_AMBIENT:.1f} Pa")


if __name__ == "__main__":
    main()
