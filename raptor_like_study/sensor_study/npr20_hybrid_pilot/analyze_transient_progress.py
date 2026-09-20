"""Plot provisional shock/separation motion and dual-time residual reduction."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent
DT_S = 2.5e-7


def clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [column.strip().strip('"') for column in frame.columns]
    return frame


def diagnostic_rows() -> pd.DataFrame:
    paths = [ROOT / "diagnostics_bdf2_muscl_k001_t8.json"]
    paths.extend(sorted(ROOT.glob("diagnostics_production_t*.json")))
    rows = []
    for path in paths:
        data = json.loads(path.read_text(encoding="ascii"))
        separation = data["persistent_separation_crossings_m"]
        reattachment = data["persistent_reattachment_crossings_m"]
        rows.append(
            {
                "iteration": data["iteration"],
                "time_us": data["iteration"] * DT_S * 1e6,
                "shock_x_mm": data["provisional_shock_pressure_rise_x_m"] * 1e3,
                "separation_x_mm": separation[0] * 1e3 if separation else np.nan,
                "reattachment_x_mm": reattachment[0] * 1e3 if reattachment else np.nan,
                "bubble_length_mm": (
                    (reattachment[0] - separation[0]) * 1e3
                    if separation and reattachment
                    else np.nan
                ),
                "wall_shear_min_pa": data["wall_shear_min_pa"],
                "label_accepted": data["label_accepted"],
            }
        )
    return pd.DataFrame(rows).sort_values("iteration")


def residual_rows() -> pd.DataFrame:
    rows = []
    paths = [
        ROOT / "history_npr20_bdf2_production_00009.csv",
        ROOT / "history_npr20_bdf2_to100_00029.csv",
        ROOT / "history_npr20_bdf2_cal_t86_cfl05_k0005_i100_00086.csv",
        ROOT / "history_npr20_bdf2_stable_to100_00087.csv",
    ]
    for path in paths:
        frame = clean_columns(pd.read_csv(path))
        for time_iter, group in frame.groupby("Time_Iter", sort=True):
            rows.append(
                {
                    "iteration": int(time_iter),
                    "inner_iterations": len(group),
                    "history_file": path.name,
                    "rho_drop_decades": float(group["rms[Rho]"].iloc[0] - group["rms[Rho]"].iloc[-1]),
                    "energy_drop_decades": float(group["rms[RhoE]"].iloc[0] - group["rms[RhoE]"].iloc[-1]),
                    "tke_drop_decades": float(group["rms[k]"].iloc[0] - group["rms[k]"].iloc[-1]),
                    "omega_drop_decades": float(group["rms[w]"].iloc[0] - group["rms[w]"].iloc[-1]),
                }
            )
    return pd.DataFrame(rows).sort_values("iteration").drop_duplicates("iteration", keep="last")


def main() -> None:
    diagnostics = diagnostic_rows()
    residuals = residual_rows()
    diagnostics.to_csv(ROOT / "transient_feature_progress.csv", index=False)
    residuals.to_csv(ROOT / "production_inner_residual_drops.csv", index=False)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7.5), sharex=False)
    axis = axes[0]
    axis.plot(diagnostics["time_us"], diagnostics["shock_x_mm"], "o-", label="Shock pressure rise")
    axis.plot(diagnostics["time_us"], diagnostics["separation_x_mm"], "s-", label="Separation")
    axis.plot(diagnostics["time_us"], diagnostics["reattachment_x_mm"], "^-", label="Reattachment")
    axis.set_ylabel("Axial position after throat [mm]")
    axis.set_title("NPR 20 provisional feature motion")
    axis.grid(alpha=0.25)
    axis.legend()

    axis = axes[1]
    axis.plot(residuals["iteration"], residuals["rho_drop_decades"], "o-", label="Density")
    axis.plot(residuals["iteration"], residuals["energy_drop_decades"], "s-", label="Total energy")
    axis.axhline(2.0, color="black", linewidth=1, linestyle="--", label="2-decade target")
    axis.set_xlabel("Physical time iteration")
    axis.set_ylabel("Residual reduction [decades]")
    axis.set_title("Inner convergence per physical step")
    axis.grid(alpha=0.25)
    axis.legend()

    fig.tight_layout()
    fig.savefig(ROOT / "transient_progress.png", dpi=180)
    plt.close(fig)

    print(diagnostics.to_string(index=False))
    print("\nMinimum residual drops:")
    print(residuals[["rho_drop_decades", "energy_drop_decades"]].min().to_string())


if __name__ == "__main__":
    main()
