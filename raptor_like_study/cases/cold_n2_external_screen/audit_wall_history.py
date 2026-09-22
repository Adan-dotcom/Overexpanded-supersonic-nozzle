#!/usr/bin/env python3
"""Export wall-metric history without assigning a stationarity tolerance."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

try:
    from .audit_external import (
        finite_max_with_location,
        nozzle_wall_samples,
        persistent_separation,
        pressure_shock,
        read_wall_load_snapshot,
    )
except ImportError:  # Direct script execution from the case directory.
    from audit_external import (
        finite_max_with_location,
        nozzle_wall_samples,
        persistent_separation,
        pressure_shock,
        read_wall_load_snapshot,
    )


def load_metadata(path: Path) -> list[dict[str, float | int | str]]:
    rows: list[dict[str, float | int | str]] = []
    with path.open(encoding="ascii") as stream:
        header = stream.readline().split()
        if header != ["loads_index", "sim_time", "step"]:
            raise ValueError(f"unexpected loads metadata header: {header}")
        for line in stream:
            values = line.split()
            if values:
                rows.append(
                    {
                        "loads_index": values[0],
                        "sim_time_s": float(values[1]),
                        "step": int(values[2]),
                    }
                )
    return rows


def finite_pressure_summary(samples: list[dict[str, float]]) -> dict[str, float | None]:
    values = np.asarray(
        [sample["pressure_Pa"] for sample in samples if math.isfinite(sample["pressure_Pa"])],
        dtype=float,
    )
    if not values.size:
        return {"min": None, "mean": None, "max": None}
    return {
        "min": float(np.min(values)),
        "mean": float(np.mean(values)),
        "max": float(np.max(values)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--throat-exclusion-m", type=float, default=0.002)
    parser.add_argument("--lip-exclusion-m", type=float, default=0.002)
    parser.add_argument("--persistence-points", type=int, default=4)
    parser.add_argument("--tau-zero-tolerance-pa", type=float, default=1.0e-6)
    args = parser.parse_args()

    root = args.artifact_dir.resolve()
    loads_root = root / "lmrsim" / "loads"
    history: list[dict[str, float | int | str | None]] = []
    previous_detector: list[dict[str, float]] | None = None
    previous_sep: float | None = None
    previous_shock: float | None = None
    for metadata in load_metadata(loads_root / "loads-metadata"):
        snapshot = loads_root / str(metadata["loads_index"])
        if not snapshot.is_dir():
            continue
        nozzle = nozzle_wall_samples(read_wall_load_snapshot(snapshot))
        x_sep, detector = persistent_separation(
            nozzle,
            throat_exclusion_m=args.throat_exclusion_m,
            lip_exclusion_m=args.lip_exclusion_m,
            persistence_points=args.persistence_points,
            tau_zero_tolerance_pa=args.tau_zero_tolerance_pa,
        )
        x_shock, shock_gradient = pressure_shock(detector)
        pressure = finite_pressure_summary(detector)
        max_pressure_change = None
        relative_pressure_change = None
        if previous_detector is not None and len(previous_detector) == len(detector):
            previous_x = np.asarray([sample["x_m"] for sample in previous_detector])
            current_x = np.asarray([sample["x_m"] for sample in detector])
            if np.allclose(previous_x, current_x, rtol=0.0, atol=1.0e-12):
                previous_p = np.asarray([sample["pressure_Pa"] for sample in previous_detector])
                current_p = np.asarray([sample["pressure_Pa"] for sample in detector])
                max_pressure_change = float(np.max(np.abs(current_p - previous_p)))
                scale = float(np.max(np.abs(current_p)))
                relative_pressure_change = max_pressure_change / scale if scale > 0.0 else None
        row = {
            **metadata,
            "x_sep_m": x_sep,
            "delta_x_sep_m": (
                x_sep - previous_sep if x_sep is not None and previous_sep is not None else None
            ),
            "x_shock_m": x_shock,
            "delta_x_shock_m": (
                x_shock - previous_shock
                if x_shock is not None and previous_shock is not None
                else None
            ),
            "shock_max_dpdx_Pa_per_m": shock_gradient,
            "y_plus_max": finite_max_with_location(nozzle, "y_plus")["max"],
            "wall_pressure_min_Pa": pressure["min"],
            "wall_pressure_mean_Pa": pressure["mean"],
            "wall_pressure_max_Pa": pressure["max"],
            "max_abs_wall_pressure_change_Pa": max_pressure_change,
            "relative_max_wall_pressure_change": relative_pressure_change,
        }
        history.append(row)
        previous_detector = detector
        previous_sep = x_sep
        previous_shock = x_shock

    args.output_json.write_text(
        json.dumps(
            {
                "case_family": "cold_n2_external_screen",
                "artifact_dir": str(root),
                "history": history,
                "stationarity_assessed": False,
                "stationarity_reason": "no stationarity tolerance has been authorized",
                "physics_accepted": False,
                "training_eligible": False,
            },
            indent=2,
        )
        + "\n",
        encoding="ascii",
    )
    if history:
        with args.output_csv.open("w", newline="", encoding="ascii") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(history[0]))
            writer.writeheader()
            writer.writerows(history)
    print(f"wall history records: {len(history)}")


if __name__ == "__main__":
    main()
