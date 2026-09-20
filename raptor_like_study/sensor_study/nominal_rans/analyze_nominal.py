import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
PC = 5.2e6
P_REF = 52000.0
T_REF = 3485.33
MACH_REF = 0.01
GAMMA = 1.1982940938
R_GAS = 390.5997546790
THROAT_X = 0.0
EXIT_X = 0.12502
PERSISTENCE_M = 1.0e-3


def read_vtk(path):
    tokens = path.read_text(encoding="ascii").split()
    p = tokens.index("POINTS")
    n = int(tokens[p + 1])
    start = p + 3
    points = np.array(tokens[start:start + 3 * n], dtype=float).reshape(n, 3)
    arrays = {}
    i = 0
    while i < len(tokens):
        if tokens[i] == "SCALARS" and i + 5 < len(tokens):
            name = tokens[i + 1]
            components = int(tokens[i + 3])
            first = i + 6
            values = np.array(tokens[first:first + n * components], dtype=float)
            arrays[name] = values if components == 1 else values.reshape(n, components)
            i = first + n * components
        elif tokens[i] == "VECTORS" and i + 3 < len(tokens):
            name = tokens[i + 1]
            first = i + 3
            arrays[name] = np.array(tokens[first:first + 3 * n], dtype=float).reshape(n, 3)
            i = first + 3 * n
        else:
            i += 1
    return points, arrays


def persistent_crossings(x, cf):
    separations = []
    reattachments = []
    for i in range(len(x) - 1):
        if x[i + 1] < THROAT_X or x[i] > EXIT_X:
            continue
        denominator = cf[i + 1] - cf[i]
        if denominator == 0:
            continue
        crossing = x[i] - cf[i] * (x[i + 1] - x[i]) / denominator
        downstream = (x >= crossing) & (x <= crossing + PERSISTENCE_M)
        upstream = (x <= crossing) & (x >= crossing - PERSISTENCE_M)
        if cf[i] > 0 >= cf[i + 1] and downstream.sum() >= 3 and np.mean(cf[downstream] < 0) >= 0.8:
            separations.append(float(crossing))
        if cf[i] < 0 <= cf[i + 1] and upstream.sum() >= 3 and np.mean(cf[upstream] < 0) >= 0.8:
            reattachments.append(float(crossing))
    return separations, reattachments


def parse_args():
    parser = argparse.ArgumentParser(description="Post-process an SU2 nozzle wall solution.")
    parser.add_argument("--wall", default="wall_coarse_npr100.vtk")
    parser.add_argument("--tag", default="1000")
    parser.add_argument("--iteration", type=int, default=1000)
    parser.add_argument("--npr", type=float, default=100.0)
    parser.add_argument("--output-dir", default=str(HERE))
    parser.add_argument("--p-ref", type=float, default=P_REF)
    parser.add_argument("--t-ref", type=float, default=T_REF)
    parser.add_argument("--mach-ref", type=float, default=MACH_REF)
    parser.add_argument("--shock-search-min", type=float, default=0.01)
    parser.add_argument("--converged", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    wall = Path(args.wall)
    if not wall.is_absolute():
        wall = HERE / wall
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    points, arrays = read_vtk(wall)
    order = np.argsort(points[:, 0])
    x = points[order, 0]
    r = points[order, 1]
    pressure = arrays["Pressure"][order]
    yplus = arrays["Y_Plus"][order]
    cf_vec = arrays["Skin_Friction_Coefficient"][order]
    drdx = np.gradient(r, x)
    cf_t = (cf_vec[:, 0] + drdx * cf_vec[:, 1]) / np.sqrt(1.0 + drdx * drdx)
    rho_ref = args.p_ref / (R_GAS * args.t_ref)
    velocity_ref = args.mach_ref * np.sqrt(GAMMA * R_GAS * args.t_ref)
    dynamic_pressure_ref = 0.5 * rho_ref * velocity_ref**2
    tau_wall = cf_t * dynamic_pressure_ref
    mask = (x >= THROAT_X) & (x <= EXIT_X)
    xd, cfd, pd, taud = x[mask], cf_t[mask], pressure[mask], tau_wall[mask]
    sep, reattach = persistent_crossings(xd, taud)
    dpdx = np.gradient(pd, xd)
    shock_candidates = np.flatnonzero(xd >= args.shock_search_min)
    shock_i = int(shock_candidates[np.argmax(dpdx[shock_candidates])])
    result = {
        "source_wall_file": wall.name,
        "iteration": args.iteration,
        "converged": args.converged,
        "label_accepted": args.converged,
        "persistent_separation_crossings_m": sep,
        "persistent_reattachment_crossings_m": reattach,
        "provisional_shock_pressure_rise_x_m": float(xd[shock_i]),
        "su2_cf_reference_dynamic_pressure_pa": float(dynamic_pressure_ref),
        "wall_shear_min_pa": float(taud.min()),
        "wall_shear_max_pa": float(taud.max()),
        "yplus_median": float(np.median(yplus[mask])),
        "yplus_p95": float(np.percentile(yplus[mask], 95)),
        "yplus_max": float(yplus[mask].max()),
        "wall_pressure_min_pa": float(pd.min()),
        "wall_pressure_max_pa": float(pd.max()),
    }
    (output_dir / f"diagnostics_{args.tag}.json").write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    with (output_dir / f"wall_processed_{args.tag}.csv").open("w", newline="", encoding="ascii") as stream:
        writer = csv.writer(stream)
        writer.writerow(("x_m", "r_m", "pressure_pa", "pressure_over_pc", "tau_wall_pa", "su2_cf_t", "yplus"))
        writer.writerows(zip(x, r, pressure, pressure / PC, tau_wall, cf_t, yplus))

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    axes[0].plot(xd * 1e3, pd / 1e5)
    axes[0].set_ylabel("Wall pressure [bar]")
    axes[1].plot(xd * 1e3, taud)
    axes[1].axhline(0.0, color="black", lw=0.8)
    axes[1].set_ylabel("Wall shear [Pa]")
    axes[2].semilogy(xd * 1e3, np.maximum(yplus[mask], 1e-12))
    axes[2].axhline(1.0, color="black", lw=0.8)
    axes[2].set(xlabel="x after throat [mm]", ylabel="y+")
    for ax in axes:
        ax.grid(True, alpha=0.25)
    status = "converged" if args.converged else "provisional, not converged"
    fig.suptitle(f"NPR {args.npr:g} {args.tag}: {status}")
    fig.tight_layout()
    fig.savefig(output_dir / f"wall_diagnostics_{args.tag}.png", dpi=180)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
