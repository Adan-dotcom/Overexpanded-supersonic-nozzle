#!/usr/bin/env python3
"""Collect compact startup/stage audits and preserve the screen classification."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for audit in sorted(args.root.glob("stage*/audit.json")):
        payload = json.loads(audit.read_text(encoding="ascii"))
        rows.append(
            {
                "case": audit.parent.name,
                "solver_stop": payload["solver"],
                "finite_positive": payload["finite_pressure_density_temperature"]
                and payload["nonpositive_pressure_density_temperature_points"] == 0,
                "vtk": payload["vtk_export_present"],
                "wall_loads": payload["wall_load_export_present"],
                "x_sep_m": payload["x_sep_m"],
                "x_shock_m": payload["x_shock_m"],
                "y_plus_max": payload["y_plus_max"],
                "physics_accepted": payload["physics_accepted"],
                "training_eligible": payload["training_eligible"],
            }
        )
    payload = {
        "case_family": "cold_n2_external_screen",
        "classification": "provisional_external_plume_numerical_screen_not_validation",
        "runs": rows,
        "all_runs_normal_and_positive": all(
            row["solver_stop"]["normal_stop_recorded"]
            and row["solver_stop"]["stop_reason"] == "maximum-time"
            and not row["solver_stop"]["nonphysical_error_text_present"]
            and row["finite_positive"]
            and row["vtk"]
            and row["wall_loads"]
            for row in rows
        ),
        "physics_accepted": False,
        "training_eligible": False,
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
