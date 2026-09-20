import csv
import math
from pathlib import Path

from generate_mesh import R_THROAT, X_EXIT, X_THROAT, wall_radius


ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "seed_template.csv"
OUTPUT = ROOT / "restart_seed.csv"

GAMMA = 1.4
GAS_CONSTANT = 287.058
P0 = 2_000_000.0
T0 = 600.0
BACK_PRESSURE = 75_000.0


def area_mach(mach: float) -> float:
    term = 2.0 / (GAMMA + 1.0) * (1.0 + 0.5 * (GAMMA - 1.0) * mach**2)
    return term ** ((GAMMA + 1.0) / (2.0 * (GAMMA - 1.0))) / mach


def mach_from_area(area_ratio: float, supersonic: bool) -> float:
    lo, hi = ((1.0, 12.0) if supersonic else (1.0e-5, 1.0))
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


def normal_shock(mach_1: float) -> tuple[float, float]:
    mach_2 = math.sqrt(
        (1.0 + 0.5 * (GAMMA - 1.0) * mach_1**2)
        / (GAMMA * mach_1**2 - 0.5 * (GAMMA - 1.0))
    )
    total_pressure_ratio = (
        ((GAMMA + 1.0) * mach_1**2 / ((GAMMA - 1.0) * mach_1**2 + 2.0))
        ** (GAMMA / (GAMMA - 1.0))
        * ((GAMMA + 1.0) / (2.0 * GAMMA * mach_1**2 - (GAMMA - 1.0)))
        ** (1.0 / (GAMMA - 1.0))
    )
    return mach_2, total_pressure_ratio


def exit_pressure_for_shock(mach_1: float) -> float:
    shock_area = area_mach(mach_1)
    mach_2, p02_p01 = normal_shock(mach_1)
    downstream_astar = shock_area / area_mach(mach_2)
    exit_area = (wall_radius(X_EXIT) / R_THROAT) ** 2
    mach_exit = mach_from_area(exit_area / downstream_astar, supersonic=False)
    return P0 * p02_p01 / (
        1.0 + 0.5 * (GAMMA - 1.0) * mach_exit**2
    ) ** (GAMMA / (GAMMA - 1.0))


def shock_state() -> tuple[float, float, float]:
    lo, hi = 1.01, mach_from_area((wall_radius(X_EXIT) / R_THROAT) ** 2, True)
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if exit_pressure_for_shock(mid) > BACK_PRESSURE:
            lo = mid
        else:
            hi = mid
    mach_1 = 0.5 * (lo + hi)
    shock_area = area_mach(mach_1)
    x_lo, x_hi = X_THROAT, X_EXIT
    for _ in range(100):
        x_mid = 0.5 * (x_lo + x_hi)
        local_area = (wall_radius(x_mid) / R_THROAT) ** 2
        if local_area < shock_area:
            x_lo = x_mid
        else:
            x_hi = x_mid
    return mach_1, 0.5 * (x_lo + x_hi), shock_area


def main() -> None:
    mach_1, shock_x, shock_area = shock_state()
    mach_2, p02_p01 = normal_shock(mach_1)
    downstream_astar = shock_area / area_mach(mach_2)

    with TEMPLATE.open(newline="", encoding="ascii") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        fieldnames = reader.fieldnames

    for row in rows:
        x = float(row["x"])
        local_area = (wall_radius(x) / R_THROAT) ** 2
        if x < X_THROAT:
            mach = mach_from_area(local_area, supersonic=False)
            local_p0 = P0
        elif x < shock_x:
            mach = mach_from_area(local_area, supersonic=True)
            local_p0 = P0
        else:
            mach = mach_from_area(local_area / downstream_astar, supersonic=False)
            local_p0 = P0 * p02_p01

        temperature = T0 / (1.0 + 0.5 * (GAMMA - 1.0) * mach**2)
        pressure = local_p0 / (
            1.0 + 0.5 * (GAMMA - 1.0) * mach**2
        ) ** (GAMMA / (GAMMA - 1.0))
        density = pressure / (GAS_CONSTANT * temperature)
        velocity = mach * math.sqrt(GAMMA * GAS_CONSTANT * temperature)
        momentum = density * velocity
        energy = pressure / (GAMMA - 1.0) + 0.5 * density * velocity**2

        row["Density"] = f"{density:.15e}"
        row["Momentum_x"] = f"{momentum:.15e}"
        row["Momentum_y"] = "0.000000000000000e+00"
        row["Energy"] = f"{energy:.15e}"

    with OUTPUT.open("w", newline="", encoding="ascii") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Shock seed: x={shock_x:.8f} m, M1={mach_1:.4f}, M2={mach_2:.4f}")
    print(f"Predicted exit pressure: {exit_pressure_for_shock(mach_1):.2f} Pa")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
