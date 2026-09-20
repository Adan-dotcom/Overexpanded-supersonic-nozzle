import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


def main():
    p = argparse.ArgumentParser()
    p.add_argument("run", help="e.g. runs/euler_coarse")
    a = p.parse_args()
    root = Path(a.run)
    with (root / "history.csv").open(newline="", encoding="ascii") as f:
        reader = csv.reader(f)
        raw = list(reader)
    headers = [h.strip().strip('"') for h in raw[0]]
    history = [dict(zip(headers, [v.strip() for v in row])) for row in raw[1:]]
    plt.figure()
    plt.semilogy([int(r["Inner_Iter"]) for r in history], [10 ** float(r['rms[Rho]']) for r in history])
    plt.xlabel("Iteration")
    plt.ylabel("RMS density residual")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(root / "convergence.png", dpi=160)
    tokens = (root / "wall.vtk").read_text(encoding="ascii").split()
    point_at = tokens.index("POINTS")
    n = int(tokens[point_at + 1])
    points = [tuple(map(float, tokens[i:i + 3])) for i in range(point_at + 3, point_at + 3 + 3 * n, 3)]
    pressure_at = tokens.index("Pressure")
    pstart = pressure_at + 5
    pressure = list(map(float, tokens[pstart:pstart + n]))
    x = [point[0] for point in points]
    plt.figure()
    plt.plot(x, pressure)
    plt.xlabel("x [m]")
    plt.ylabel("Wall pressure [Pa]")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(root / "wall_pressure.png", dpi=160)
    print(f"Wrote {root / 'convergence.png'} and {root / 'wall_pressure.png'}")


if __name__ == "__main__":
    main()
