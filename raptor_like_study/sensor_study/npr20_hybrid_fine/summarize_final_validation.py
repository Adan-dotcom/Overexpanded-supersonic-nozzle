import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / "npr20_hybrid_pilot"
T0_K = 3485.33


def load_json(path):
    return json.loads(path.read_text(encoding="ascii"))


def load_csv(path):
    with path.open(newline="", encoding="ascii") as stream:
        rows = list(csv.DictReader(stream))
    return {
        key: np.array([float(row[key]) if row[key] else np.nan for row in rows])
        for key in rows[0]
    }


pilot = load_json(PILOT / "diagnostics_production_t5613.json")
pilot_convergence = load_json(PILOT / "relaxation_convergence.json")
pilot_temp = load_json(PILOT / "temperature_production_t5613.json")
fine_iterations = [5620, 5630, 5640, 5650, 5660, 5665]
fine = [load_json(HERE / f"diagnostics_final_fine_t{iteration}.json") for iteration in fine_iterations]
fine_temp = load_json(HERE / "temperature_final_fine_t5665.json")

pilot_xsep_mm = 1e3 * pilot["persistent_separation_crossings_m"][0]
fine_xsep_mm = [1e3 * case["persistent_separation_crossings_m"][0] for case in fine]
fine_mesh_delta_mm = fine_xsep_mm[-1] - pilot_xsep_mm
fine_time_drift_mm = fine_xsep_mm[-1] - fine_xsep_mm[0]

summary = {
    "selected_numerics": {
        "flux": "SLAU2",
        "physical_time_step_ns": 6.25,
        "pseudo_cfl": 2.0,
        "inner_iterations": 30,
        "spatial_reconstruction": "MUSCL",
        "limiter": "VENKATAKRISHNAN_WANG",
        "venkat_coefficient": 0.001,
        "turbulence": "SST-2003m with Sarkar compressibility correction",
    },
    "pilot_final": {
        "iteration": 5613,
        "physical_time_us": 162.825,
        "separation_x_mm": pilot_xsep_mm,
        "last_window_separation_range_mm": pilot_convergence["last_10_checkpoint_span"]["separation_x_range_mm"],
        "yplus_p95": pilot["yplus_p95"],
        "yplus_max": pilot["yplus_max"],
    },
    "fine_final": {
        "iteration": fine_iterations[-1],
        "separation_x_mm": fine_xsep_mm[-1],
        "separation_change_from_first_fine_checkpoint_mm": fine_time_drift_mm,
        "separation_change_from_pilot_mm": fine_mesh_delta_mm,
        "yplus_p95": fine[-1]["yplus_p95"],
        "yplus_max": fine[-1]["yplus_max"],
    },
    "thermal_gate": {
        "inlet_total_temperature_k": T0_K,
        "pilot_max_local_total_temperature_k": pilot_temp["local_total_temperature_max"]["value_k"],
        "fine_max_local_total_temperature_k": fine_temp["local_total_temperature_max"]["value_k"],
        "fine_overshoot_percent": 100.0
        * (fine_temp["local_total_temperature_max"]["value_k"] / T0_K - 1.0),
        "passed": fine_temp["local_total_temperature_max"]["value_k"] <= 1.01 * T0_K,
    },
    "acceptance": {
        "pilot_temporal_plateau_passed": pilot_convergence["last_10_checkpoint_span"]["separation_x_range_mm"] <= 0.05,
        "fine_short_window_drift_passed": abs(fine_time_drift_mm) <= 0.05,
        "pilot_to_fine_grid_delta_passed": abs(fine_mesh_delta_mm) <= 0.05,
        "fine_wall_resolution_passed": fine[-1]["yplus_max"] <= 1.0,
        "separation_label_numerically_accepted": False,
        "paper_physics_accepted": False,
    },
}
numeric_checks = summary["acceptance"]
numeric_checks["separation_label_numerically_accepted"] = all(
    numeric_checks[key]
    for key in (
        "pilot_temporal_plateau_passed",
        "fine_short_window_drift_passed",
        "pilot_to_fine_grid_delta_passed",
        "fine_wall_resolution_passed",
    )
)
numeric_checks["paper_physics_accepted"] = bool(
    numeric_checks["separation_label_numerically_accepted"] and summary["thermal_gate"]["passed"]
)
(HERE / "final_validation_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")

history = load_csv(PILOT / "relaxation_feature_history.csv")
pilot_wall = load_csv(PILOT / "wall_processed_production_t5613.csv")
fine_wall = load_csv(HERE / "wall_processed_final_fine_t5665.csv")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes[0, 0].plot(history["time_us"], history["separation_x_mm"], lw=1.2)
axes[0, 0].set(xlabel="Physical time [microseconds]", ylabel="First separation x [mm]", title="Pilot relaxation")
last = history["time_us"] >= history["time_us"].max() - 5.0
axes[0, 1].plot(history["time_us"][last], history["separation_x_mm"][last], "o-", ms=3, label="pilot")
fine_time_us = 162.825 + (np.array(fine_iterations) - 5613) * 0.00625
axes[0, 1].plot(fine_time_us, fine_xsep_mm, "s-", ms=4, label="fine")
axes[0, 1].set(xlabel="Physical time [microseconds]", ylabel="First separation x [mm]", title="Final plateau and fine transfer")
axes[0, 1].legend()

for data, label in ((pilot_wall, "pilot"), (fine_wall, "fine")):
    mask = (data["x_m"] >= 0.02) & (data["x_m"] <= 0.12502)
    axes[1, 0].plot(1e3 * data["x_m"][mask], data["pressure_pa"][mask] / 1e5, label=label)
    axes[1, 1].plot(1e3 * data["x_m"][mask], data["tau_wall_pa"][mask] / 1e3, label=label)
axes[1, 0].set(xlabel="x after throat [mm]", ylabel="Wall pressure [bar]", title="Grid comparison")
axes[1, 1].set(xlabel="x after throat [mm]", ylabel="Wall shear [kPa]", title="Grid comparison")
axes[1, 1].axhline(0.0, color="black", lw=0.8)
axes[1, 0].legend()
axes[1, 1].legend()
for axis in axes.ravel():
    axis.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(HERE / "final_validation_summary.png", dpi=180)
print(json.dumps(summary, indent=2))
