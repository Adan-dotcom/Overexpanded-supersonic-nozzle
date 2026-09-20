#!/usr/bin/env python3
"""Sample accepted CFD wall-pressure profiles onto a fixed sensor grid."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

from train_sensor_models import parse_boolean


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SENSOR_X = np.linspace(0.002, 0.124, 128)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=HERE / "case_registry.csv")
    parser.add_argument("--output", type=Path, default=HERE / "accepted_sensor_dataset.csv")
    parser.add_argument("--allow-provisional", action="store_true")
    args = parser.parse_args()

    registry = pd.read_csv(args.registry, keep_default_na=False)
    if args.allow_provisional:
        eligible = parse_boolean(registry["physics_accepted"], "physics_accepted") | parse_boolean(
            registry["provisional"], "provisional"
        )
    else:
        eligible = parse_boolean(registry["physics_accepted"], "physics_accepted")
    registry = registry[eligible].copy()
    registry = registry[registry["profile_csv"].astype(str).str.strip() != ""]
    if registry.empty:
        raise SystemExit("No eligible CFD wall profiles; final sensor dataset was not created.")

    rows = []
    for _, case in registry.iterrows():
        profile_path = Path(case["profile_csv"])
        if not profile_path.is_absolute():
            profile_path = ROOT / profile_path
        profile = pd.read_csv(profile_path).sort_values("x_m")
        if not {"x_m", "pressure_pa"}.issubset(profile.columns):
            raise SystemExit(f"{profile_path} must contain x_m and pressure_pa")
        if SENSOR_X[0] < profile["x_m"].min() or SENSOR_X[-1] > profile["x_m"].max():
            raise SystemExit(f"{profile_path} does not cover the fixed sensor grid")
        pressure = PchipInterpolator(profile["x_m"], profile["pressure_pa"])(SENSOR_X)
        row = {
            "case_id": case["case_id"],
            "geometry_id": case["geometry_id"],
            "pc_pa": float(case["pc_pa"]),
            "t0_k": float(case["t0_k"]),
            "pa_pa": float(case["pa_pa"]),
            "of_ratio": float(case["of_ratio"]),
            "separated": int(str(case["separated"]).strip().lower() in ("true", "1", "yes")),
            "x_sep_m": float(case["x_sep_m"]) if str(case["x_sep_m"]).strip() else np.nan,
            "physics_accepted": bool(parse_boolean(pd.Series([case["physics_accepted"]]), "physics_accepted").iloc[0]),
            "provisional": bool(parse_boolean(pd.Series([case["provisional"]]), "provisional").iloc[0]),
        }
        row.update({f"p_s{index:03d}": value for index, value in enumerate(pressure)})
        rows.append(row)
    pd.DataFrame(rows).to_csv(args.output, index=False)
    np.savetxt(HERE / "sensor_candidate_x_m.csv", SENSOR_X, delimiter=",", header="x_m", comments="")
    print(f"Wrote {args.output} with {len(rows)} CFD cases and {len(SENSOR_X)} candidate stations")


if __name__ == "__main__":
    main()
