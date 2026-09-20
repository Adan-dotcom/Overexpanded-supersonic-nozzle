import csv
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "nominal_rans"))
from analyze_nominal import (  # noqa: E402
    EXIT_X,
    GAMMA,
    PERSISTENCE_M,
    R_GAS,
    THROAT_X,
    persistent_crossings,
    read_vtk,
)


DT_US = 0.025
BASE_ITERATION = 100
BASE_TIME_US = 25.0
P_REF = 260000.0
T_REF = 300.0
MACH_REF = 0.001


def iteration_from_name(path):
    match = re.search(r"_(\d{5})\.vtk$", path.name)
    if not match:
        raise ValueError(f"No iteration suffix in {path.name}")
    return int(match.group(1))


def analyze_wall(path):
    points, arrays = read_vtk(path)
    order = np.argsort(points[:, 0])
    x = points[order, 0]
    r = points[order, 1]
    pressure = arrays["Pressure"][order]
    yplus = arrays["Y_Plus"][order]
    cf_vec = arrays["Skin_Friction_Coefficient"][order]
    drdx = np.gradient(r, x)
    cf_t = (cf_vec[:, 0] + drdx * cf_vec[:, 1]) / np.sqrt(1.0 + drdx**2)
    rho_ref = P_REF / (R_GAS * T_REF)
    velocity_ref = MACH_REF * np.sqrt(GAMMA * R_GAS * T_REF)
    tau = cf_t * 0.5 * rho_ref * velocity_ref**2
    mask = (x >= THROAT_X) & (x <= EXIT_X)
    xd, pd, taud = x[mask], pressure[mask], tau[mask]
    separation, reattachment = persistent_crossings(xd, taud)
    candidates = np.flatnonzero(xd >= 0.01)
    shock_index = int(candidates[np.argmax(np.gradient(pd, xd)[candidates])])
    iteration = iteration_from_name(path)
    return {
        "iteration": iteration,
        "time_us": BASE_TIME_US + (iteration - BASE_ITERATION) * DT_US,
        "separation_x_mm": 1e3 * separation[0] if separation else None,
        "reattachment_x_mm": 1e3 * reattachment[0] if reattachment else None,
        "shock_x_mm": 1e3 * xd[shock_index],
        "wall_shear_min_kpa": float(np.min(taud) / 1e3),
        "wall_pressure_max_bar": float(np.max(pd) / 1e5),
        "yplus_p95": float(np.percentile(yplus[mask], 95)),
    }


production_paths = sorted(HERE.glob("wall_npr20_production_cfl2_i30_from520_[0-9][0-9][0-9][0-9][0-9].vtk"))
paths = production_paths or sorted(HERE.glob("wall_npr20_relax_SLAU2_dt025_[0-9][0-9][0-9][0-9][0-9].vtk"))
if not paths:
    raise SystemExit("No relaxation wall checkpoints found.")
records = [analyze_wall(path) for path in paths]

numeric_fields = list(records[0])
with (HERE / "relaxation_feature_history.csv").open("w", newline="", encoding="ascii") as stream:
    writer = csv.DictWriter(stream, fieldnames=numeric_fields)
    writer.writeheader()
    writer.writerows(records)

window = records[-min(10, len(records)) :]
valid_sep = [row["separation_x_mm"] for row in window if row["separation_x_mm"] is not None]
convergence = {
    "checkpoint_count": len(records),
    "last_iteration": records[-1]["iteration"],
    "last_time_us": records[-1]["time_us"],
    "last_features": records[-1],
    "last_10_checkpoint_span": {
        "physical_time_us": window[-1]["time_us"] - window[0]["time_us"],
        "separation_x_range_mm": max(valid_sep) - min(valid_sep) if valid_sep else None,
        "shock_x_range_mm": max(row["shock_x_mm"] for row in window) - min(row["shock_x_mm"] for row in window),
        "wall_shear_min_range_kpa": max(row["wall_shear_min_kpa"] for row in window)
        - min(row["wall_shear_min_kpa"] for row in window),
    },
    "criteria": {
        "window_checkpoint_count": 10,
        "separation_x_range_mm_max": 0.05,
        "shock_x_range_mm_max": 0.20,
    },
}
span = convergence["last_10_checkpoint_span"]
convergence["feature_plateau"] = bool(
    len(window) == 10
    and span["separation_x_range_mm"] is not None
    and span["separation_x_range_mm"] <= 0.05
    and span["shock_x_range_mm"] <= 0.20
)
(HERE / "relaxation_convergence.json").write_text(json.dumps(convergence, indent=2) + "\n", encoding="ascii")

time = np.array([row["time_us"] for row in records])
separation = np.array([np.nan if row["separation_x_mm"] is None else row["separation_x_mm"] for row in records])
shock = np.array([row["shock_x_mm"] for row in records])
shear = np.array([row["wall_shear_min_kpa"] for row in records])
fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
axes[0].plot(time, separation, "o-", ms=3, label="separation")
axes[0].plot(time, shock, "o-", ms=3, label="maximum wall pressure gradient")
axes[0].set(ylabel="Axial position [mm]")
axes[0].legend()
axes[1].plot(time, shear, "o-", ms=3)
axes[1].set(xlabel="Physical time [microseconds]", ylabel="Minimum wall shear [kPa]")
for axis in axes:
    axis.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(HERE / "relaxation_feature_history.png", dpi=180)
print(json.dumps(convergence, indent=2))
