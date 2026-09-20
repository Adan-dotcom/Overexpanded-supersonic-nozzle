#!/usr/bin/env python3
"""Merge the corrected NASA-CEA DOE into the case registry as planned work."""

from __future__ import annotations

import csv
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REGISTRY = HERE / "case_registry.csv"
CEA = ROOT / "cases" / "cea" / "physical_cea_summary.csv"
FIELDS = (
    "case_id", "campaign", "geometry_id", "pc_pa", "t0_k", "pa_pa", "of_ratio",
    "numerically_accepted", "physics_accepted", "provisional", "profile_csv",
    "separated", "x_sep_m", "exclusion_reason",
)


def main() -> None:
    with REGISTRY.open(newline="", encoding="ascii") as stream:
        existing = list(csv.DictReader(stream))
    by_id = {row["case_id"]: row for row in existing}
    with CEA.open(newline="", encoding="ascii") as stream:
        for source in csv.DictReader(stream):
            by_id[source["case_id"]] = {
                "case_id": source["case_id"],
                "campaign": source["campaign"],
                "geometry_id": source["geometry_id"],
                "pc_pa": source["pc_pa"],
                "t0_k": source["t0_k"],
                "pa_pa": source["pa_pa"],
                "of_ratio": source["of_ratio"],
                "numerically_accepted": "false",
                "physics_accepted": "false",
                "provisional": "false",
                "profile_csv": "",
                "separated": "",
                "x_sep_m": "",
                "exclusion_reason": "planned_CFD_not_run",
            }
    with REGISTRY.open("w", newline="", encoding="ascii") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(by_id.values())
    planned = sum(row["exclusion_reason"] == "planned_CFD_not_run" for row in by_id.values())
    print(f"Wrote {REGISTRY}: {len(by_id)} total rows, {planned} planned physical CFD cases")


if __name__ == "__main__":
    main()
