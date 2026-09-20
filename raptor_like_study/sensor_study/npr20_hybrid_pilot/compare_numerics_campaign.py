import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve().parent


def load_json(name):
    return json.loads((HERE / name).read_text(encoding="ascii"))


def load_wall(name):
    with (HERE / name).open(newline="", encoding="ascii") as stream:
        rows = list(csv.DictReader(stream))
    return {key: np.array([float(row[key]) for row in rows]) for key in rows[0]}


flux_specs = [
    ("HLLC", False),
    ("SLAU2", False),
    ("AUSMPLUSUP2", True),
]
dt_specs = [
    ("6.25 ns", "00625", 152, 6.25),
    ("12.5 ns", "0125", 126, 12.5),
    ("25 ns", "025", 113, 25.0),
]

summary = {"flux_screen": [], "time_step_screen": []}
for flux, failed in flux_specs:
    wall = load_json(f"diagnostics_flux_{flux}_t152.json")
    temp = load_json(f"temperature_flux_{flux}_t152.json")
    summary["flux_screen"].append(
        {
            "flux": flux,
            "numerically_failed": failed,
            "separation_x_mm": 1e3 * wall["persistent_separation_crossings_m"][0],
            "shock_x_mm": 1e3 * wall["provisional_shock_pressure_rise_x_m"],
            "static_temperature_max_k": temp["static_temperature_max"]["value_k"],
            "local_total_temperature_max_k": temp["local_total_temperature_max"]["value_k"],
            "inside_nozzle_static_temperature_max_k": temp["spatial_split"]["inside_nozzle_static_temperature_max_k"],
        }
    )

for label, tag, iteration, dt_ns in dt_specs:
    wall = load_json(f"diagnostics_dt{tag}_t{iteration}.json")
    temp = load_json(f"temperature_dt{tag}_t{iteration}.json")
    summary["time_step_screen"].append(
        {
            "label": label,
            "dt_ns": dt_ns,
            "iteration": iteration,
            "separation_x_mm": 1e3 * wall["persistent_separation_crossings_m"][0],
            "reattachment_x_mm": 1e3 * wall["persistent_reattachment_crossings_m"][0],
            "shock_x_mm": 1e3 * wall["provisional_shock_pressure_rise_x_m"],
            "wall_shear_min_kpa": wall["wall_shear_min_pa"] / 1e3,
            "static_temperature_max_k": temp["static_temperature_max"]["value_k"],
            "local_total_temperature_max_k": temp["local_total_temperature_max"]["value_k"],
            "inside_nozzle_static_temperature_max_k": temp["spatial_split"]["inside_nozzle_static_temperature_max_k"],
        }
    )

reference = summary["time_step_screen"][0]
for case in summary["time_step_screen"]:
    case["separation_delta_from_6p25ns_mm"] = case["separation_x_mm"] - reference["separation_x_mm"]
    case["static_temperature_delta_from_6p25ns_percent"] = 100.0 * (
        case["static_temperature_max_k"] / reference["static_temperature_max_k"] - 1.0
    )

summary["selection"] = {
    "flux": "SLAU2",
    "dt_ns": 25.0,
    "rationale": (
        "SLAU2 matches HLLC for the separation label while avoiding HLLC's known shock-anomaly risk. "
        "AUSMPLUSUP2 failed its inner residual solve. At 25 ns, x_sep differs by less than 0.03 mm "
        "and global Tmax by less than 0.01 percent from the 6.25 ns reference over the matched interval."
    ),
}
(HERE / "numerics_campaign_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="ascii")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
for label, tag, iteration, _ in dt_specs:
    data = load_wall(f"wall_processed_dt{tag}_t{iteration}.csv")
    mask = (data["x_m"] >= 0.105) & (data["x_m"] <= 0.12502)
    axes[0, 0].plot(1e3 * data["x_m"][mask], data["pressure_pa"][mask] / 1e5, label=label)
    axes[1, 0].plot(1e3 * data["x_m"][mask], data["tau_wall_pa"][mask] / 1e3, label=label)

dt = np.array([case["dt_ns"] for case in summary["time_step_screen"]])
xsep = np.array([case["separation_x_mm"] for case in summary["time_step_screen"]])
tmax = np.array([case["static_temperature_max_k"] for case in summary["time_step_screen"]])
axes[0, 1].plot(dt, xsep, "o-")
axes[1, 1].plot(dt, tmax, "o-")

axes[0, 0].set(ylabel="Wall pressure [bar]", title="Matched-time wall pressure")
axes[1, 0].set(xlabel="x after throat [mm]", ylabel="Wall shear [kPa]", title="Matched-time wall shear")
axes[0, 1].set(xlabel="Physical time step [ns]", ylabel="Separation x [mm]", title="Separation sensitivity")
axes[1, 1].set(xlabel="Physical time step [ns]", ylabel="Global Tmax [K]", title="Temperature sensitivity")
axes[1, 0].axhline(0.0, color="black", lw=0.8)
axes[0, 0].legend()
for ax in axes.ravel():
    ax.grid(True, alpha=0.25)
fig.tight_layout()
fig.savefig(HERE / "numerics_campaign_comparison.png", dpi=180)
print(json.dumps(summary["selection"], indent=2))
