"""Summarize one-step dual-time inner-convergence calibration runs."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
CASES = {
    "CFL 0.10, 100 iter": "history_npr20_urans_cal_inner100_00001.csv",
    "CFL 0.20, 200 iter": "history_npr20_urans_cal_inner200_00001.csv",
    "CFL 1.00, 100 iter": "history_npr20_urans_cal_cfl1_00001.csv",
    "CFL 1.00, 150 iter": "history_npr20_urans_cal_cfl1_i150_00001.csv",
}
RESIDUALS = ["rms[Rho]", "rms[RhoU]", "rms[RhoV]", "rms[RhoE]", "rms[k]", "rms[w]"]


def clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [column.strip().strip('"') for column in frame.columns]
    return frame


def main() -> None:
    records: list[dict[str, float | int | str]] = []
    histories: dict[str, pd.DataFrame] = {}

    for label, filename in CASES.items():
        frame = clean_columns(pd.read_csv(ROOT / filename))
        histories[label] = frame
        record: dict[str, float | int | str] = {
            "case": label,
            "history_file": filename,
            "inner_iterations": int(frame["Inner_Iter"].iloc[-1]) + 1,
        }
        for residual in RESIDUALS:
            short = residual.removeprefix("rms[").removesuffix("]")
            first = float(frame[residual].iloc[0])
            last = float(frame[residual].iloc[-1])
            record[f"{short}_initial_log10"] = first
            record[f"{short}_final_log10"] = last
            record[f"{short}_drop_decades"] = first - last
        records.append(record)

    summary = pd.DataFrame(records)
    summary.to_csv(ROOT / "inner_convergence_summary.csv", index=False)
    (ROOT / "inner_convergence_summary.json").write_text(
        json.dumps(records, indent=2), encoding="ascii"
    )

    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), sharex=True)
    plotted = ["rms[Rho]", "rms[RhoE]", "rms[k]", "rms[w]"]
    titles = ["Density", "Total energy", "Turbulent kinetic energy", "Specific dissipation"]
    for axis, residual, title in zip(axes.flat, plotted, titles):
        for label, frame in histories.items():
            axis.plot(frame["Inner_Iter"], frame[residual], label=label, linewidth=1.6)
        axis.set_title(title)
        axis.set_ylabel(r"$\log_{10}$ RMS residual")
        axis.grid(alpha=0.25)
    for axis in axes[-1]:
        axis.set_xlabel("Inner iteration")
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("NPR 20 URANS: inner convergence for one physical step")
    fig.tight_layout()
    fig.savefig(ROOT / "inner_convergence_calibration.png", dpi=180)
    plt.close(fig)

    columns = [
        "case",
        "inner_iterations",
        "Rho_drop_decades",
        "RhoE_drop_decades",
        "k_drop_decades",
        "w_drop_decades",
    ]
    print(summary[columns].to_string(index=False))


if __name__ == "__main__":
    main()
