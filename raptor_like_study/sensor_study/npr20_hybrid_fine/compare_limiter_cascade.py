import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
T0 = 3485.33

CASES = {
    "Baseline": {
        "diagnostics": "diagnostics_fine_t200.json",
        "wall": "wall_processed_fine_t200.csv",
        "volume": "flow_npr20_fine_bdf2_140_to200_i10_00200.vtk",
        "runtime_s": None,
    },
    "A: Venkat K=.001": {
        "diagnostics": "diagnostics_fine_A_t250.json",
        "wall": "wall_processed_fine_A_t250.csv",
        "volume": "flow_npr20_fine_A_k0001_00250.vtk",
        "runtime_s": 1350.46,
    },
    "B: Barth-Jespersen": {
        "diagnostics": "diagnostics_fine_B_t250.json",
        "wall": "wall_processed_fine_B_t250.csv",
        "volume": "flow_npr20_fine_B_barth_00250.vtk",
        "runtime_s": 1352.56,
    },
    "C: K=.001, CFL=.25, i30": {
        "diagnostics": "diagnostics_fine_C_t250.json",
        "wall": "wall_processed_fine_C_t250.csv",
        "volume": "flow_npr20_fine_C_k0001_cfl025_i30_00250.vtk",
        "runtime_s": 3511.84,
    },
}


def vtk_scalar_max(path, scalar):
    with path.open("r", encoding="ascii") as stream:
        for line in stream:
            fields = line.split()
            if len(fields) >= 2 and fields[0] == "SCALARS" and fields[1] == scalar:
                stream.readline()
                return float(np.max(np.fromstring(stream.readline(), sep=" ")))
    raise ValueError(f"Scalar {scalar!r} not found in {path}")


for name, case in CASES.items():
    case["diagnostics_data"] = json.loads((HERE / case["diagnostics"]).read_text(encoding="ascii"))
    case["wall_data"] = np.genfromtxt(HERE / case["wall"], delimiter=",", names=True)
    case["tmax_k"] = vtk_scalar_max(HERE / case["volume"], "Temperature")

labels = list(CASES)
tmax = np.array([CASES[name]["tmax_k"] for name in labels])
sep = 1e3 * np.array(
    [CASES[name]["diagnostics_data"]["persistent_separation_crossings_m"][0] for name in labels]
)

fig, axes = plt.subplots(2, 2, figsize=(13, 8), constrained_layout=True)
colors = ["0.45", "C0", "C1", "C2"]

ax = axes[0, 0]
ax.bar(labels, tmax, color=colors)
ax.axhline(T0, color="black", ls="--", label=f"T0 = {T0:.0f} K")
ax.set(ylabel="Maximum static temperature [K]", title="Thermal boundedness")
ax.tick_params(axis="x", rotation=15)
ax.legend()
ax.grid(axis="y", alpha=0.25)

ax = axes[0, 1]
ax.bar(labels, sep, color=colors)
ax.set(ylabel="Separation x [mm]", title="Persistent wall-shear crossing")
ax.set_ylim(float(np.min(sep) - 0.02), float(np.max(sep) + 0.02))
ax.tick_params(axis="x", rotation=15)
ax.ticklabel_format(axis="y", style="plain", useOffset=False)
ax.grid(axis="y", alpha=0.25)

for name, color in zip(labels, colors):
    wall = CASES[name]["wall_data"]
    mask = (wall["x_m"] >= 0.116) & (wall["x_m"] <= 0.122)
    axes[1, 0].plot(1e3 * wall["x_m"][mask], wall["pressure_pa"][mask] / 1e6, label=name, color=color)
    axes[1, 1].plot(1e3 * wall["x_m"][mask], wall["tau_wall_pa"][mask] / 1e3, label=name, color=color)

axes[1, 0].set(xlabel="x [mm]", ylabel="Wall pressure [MPa]", title="Shock pressure profile")
axes[1, 1].set(xlabel="x [mm]", ylabel="Signed wall shear [kPa]", title="Separation profile")
axes[1, 1].axhline(0, color="black", lw=0.8)
for ax in axes[1]:
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8)

fig.suptitle("Limiter and pseudo-CFL cascade, common restart at step 200", fontsize=14)
fig.savefig(HERE / "limiter_cascade_comparison.png", dpi=180)

summary = {}
for name in labels:
    diagnostics = CASES[name]["diagnostics_data"]
    summary[name] = {
        "tmax_k": CASES[name]["tmax_k"],
        "temperature_overshoot_above_t0_k": CASES[name]["tmax_k"] - T0,
        "separation_x_mm": 1e3 * diagnostics["persistent_separation_crossings_m"][0],
        "shock_x_mm": 1e3 * diagnostics["provisional_shock_pressure_rise_x_m"],
        "reattachment_x_mm": 1e3 * diagnostics["persistent_reattachment_crossings_m"][0],
        "wall_shear_min_kpa": diagnostics["wall_shear_min_pa"] / 1e3,
        "yplus_p95": diagnostics["yplus_p95"],
        "runtime_s": CASES[name]["runtime_s"],
    }

trend_steps = list(range(210, 251, 10))
summary["A_temperature_trend"] = {
    "steps": trend_steps,
    "tmax_k": [
        vtk_scalar_max(HERE / f"flow_npr20_fine_A_k0001_{step:05d}.vtk", "Temperature")
        for step in trend_steps
    ],
}

summary["decision"] = {
    "A_passed": False,
    "B_passed": False,
    "C_passed": False,
    "label_accepted": False,
    "reason": "All three branches retain Tmax well above T0; A and B are nearly identical, and C costs 2.6x without improving Tmax.",
}
(HERE / "limiter_cascade_comparison.json").write_text(json.dumps(summary, indent=2), encoding="ascii")
print(json.dumps(summary, indent=2))
