import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "npr20_hybrid_pilot"
STEPS = np.arange(120, 201, 10)


def load_json(path):
    return json.loads(path.read_text(encoding="ascii"))


def load_wall(path):
    return np.genfromtxt(path, delimiter=",", names=True)


diagnostics = [load_json(HERE / f"diagnostics_fine_t{step}.json") for step in STEPS]
pilot_diag = load_json(PILOT / "diagnostics_production_t100.json")

sep = 1e3 * np.array([item["persistent_separation_crossings_m"][0] for item in diagnostics])
shock = 1e3 * np.array([item["provisional_shock_pressure_rise_x_m"] for item in diagnostics])
reattach = 1e3 * np.array([item["persistent_reattachment_crossings_m"][0] for item in diagnostics])

pilot = load_wall(PILOT / "wall_processed_production_t100.csv")
fine = load_wall(HERE / "wall_processed_fine_t200.csv")

fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
ax = axes[0, 0]
ax.plot(STEPS, sep, "o-", label="Separation")
ax.plot(STEPS, shock, "s-", label="Shock pressure rise")
ax.axhline(1e3 * pilot_diag["persistent_separation_crossings_m"][0], color="C0", ls="--", alpha=0.6)
ax.axhline(1e3 * pilot_diag["provisional_shock_pressure_rise_x_m"], color="C1", ls="--", alpha=0.6)
ax.set(xlabel="Physical step", ylabel="x [mm]", title="Shock/separation location")
ax.grid(alpha=0.25)
ax.legend()

ax = axes[0, 1]
ax.plot(STEPS, reattach, "o-", color="C2")
ax.axhline(1e3 * pilot_diag["persistent_reattachment_crossings_m"][0], color="C2", ls="--", alpha=0.6)
ax.set(xlabel="Physical step", ylabel="x [mm]", title="Reattachment location")
ax.ticklabel_format(axis="y", style="plain", useOffset=False)
ax.grid(alpha=0.25)

mask_p = (pilot["x_m"] >= 0.105) & (pilot["x_m"] <= 0.12502)
mask_f = (fine["x_m"] >= 0.105) & (fine["x_m"] <= 0.12502)
ax = axes[1, 0]
ax.plot(1e3 * pilot["x_m"][mask_p], pilot["pressure_pa"][mask_p] / 1e6, label="Pilot, step 100")
ax.plot(1e3 * fine["x_m"][mask_f], fine["pressure_pa"][mask_f] / 1e6, label="Fine, step 200")
ax.set(xlabel="x [mm]", ylabel="Wall pressure [MPa]", title="Wall pressure near separation")
ax.grid(alpha=0.25)
ax.legend()

ax = axes[1, 1]
ax.plot(1e3 * pilot["x_m"][mask_p], pilot["tau_wall_pa"][mask_p] / 1e3, label="Pilot, step 100")
ax.plot(1e3 * fine["x_m"][mask_f], fine["tau_wall_pa"][mask_f] / 1e3, label="Fine, step 200")
ax.axhline(0, color="black", lw=0.8)
ax.set(xlabel="x [mm]", ylabel="Wall shear [kPa]", title="Signed wall shear")
ax.grid(alpha=0.25)
ax.legend()

fig.suptitle("NPR 20 fine-grid check: dt = 0.00625 microseconds", fontsize=14)
fig.savefig(HERE / "fine_grid_comparison.png", dpi=180)

summary = {
    "fine_steps": STEPS.tolist(),
    "separation_x_mm": sep.tolist(),
    "shock_x_mm": shock.tolist(),
    "reattachment_x_mm": reattach.tolist(),
    "fine_sep_drift_120_to_200_um": float(1e3 * (sep[-1] - sep[0])),
    "pilot_to_fine120_sep_delta_um": float(1e3 * (sep[0] - 1e3 * pilot_diag["persistent_separation_crossings_m"][0])),
    "pilot_to_fine200_sep_delta_um": float(1e3 * (sep[-1] - 1e3 * pilot_diag["persistent_separation_crossings_m"][0])),
    "fine_yplus_p95_at_200": diagnostics[-1]["yplus_p95"],
    "fine_yplus_max_at_200": diagnostics[-1]["yplus_max"],
    "label_accepted": False,
    "note": "Short grid/time-step sensitivity check; not a statistically stationary label or a three-grid GCI study.",
}
(HERE / "fine_grid_comparison.json").write_text(json.dumps(summary, indent=2), encoding="ascii")
print(json.dumps(summary, indent=2))
