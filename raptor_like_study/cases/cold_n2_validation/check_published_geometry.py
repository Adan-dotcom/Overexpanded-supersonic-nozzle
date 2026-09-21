"""Compare the reconstructed contour with published scalar DLR-PAR controls."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path


PUBLISHED = {
    "throat_radius_m": 0.010,
    "area_ratio": 30.0,
    "post_throat_arc_wall_angle_deg": 34.0,
    "exit_wall_angle_deg": 10.0,
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contour", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with args.contour.open(newline="", encoding="utf-8-sig") as stream:
        points = [
            (float(row["x_mm"]) * 1.0e-3, float(row["r_mm"]) * 1.0e-3)
            for row in csv.DictReader(stream)
        ]
    throat_index = min(range(len(points)), key=lambda index: points[index][1])
    divergent = points[throat_index:]
    segments = [
        ((r1 - r0) / (x1 - x0), (x0 + x1) / 2.0)
        for (x0, r0), (x1, r1) in zip(divergent, divergent[1:])
    ]
    maximum_slope, maximum_slope_x_m = max(segments)
    exit_slope, exit_segment_x_m = segments[-1]
    measured = {
        "throat_radius_m": points[throat_index][1],
        "area_ratio": (points[-1][1] / points[throat_index][1]) ** 2,
        "post_throat_arc_wall_angle_deg": math.degrees(math.atan(maximum_slope)),
        "exit_wall_angle_deg": math.degrees(math.atan(exit_slope)),
    }
    differences = {name: measured[name] - published for name, published in PUBLISHED.items()}
    checks = {
        "throat_radius_within_1e_9_m": abs(differences["throat_radius_m"]) <= 1.0e-9,
        "area_ratio_within_1e_3": abs(differences["area_ratio"]) <= 1.0e-3,
        "post_throat_angle_within_published_rounding_deg": abs(
            differences["post_throat_arc_wall_angle_deg"]
        ) <= 0.5,
        "exit_angle_within_published_rounding_deg": abs(differences["exit_wall_angle_deg"]) <= 0.5,
    }
    payload = {
        "comparison_scope": "published_scalar_controls_only_not_full_contour_certification",
        "primary_geometry_source": "Verma_and_Haidn_cold_gas_testing_same_DLR_nozzle",
        "published": PUBLISHED,
        "reconstructed_contour": measured,
        "reconstructed_minus_published": differences,
        "diagnostics": {
            "maximum_divergent_slope_segment_midpoint_x_m": maximum_slope_x_m,
            "exit_segment_midpoint_x_m": exit_segment_x_m,
        },
        "checks": checks,
        "scalar_controls_consistent": all(checks.values()),
        "full_contour_certified": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))
    if not payload["scalar_controls_consistent"]:
        raise SystemExit("Reconstructed contour failed a published scalar control.")


if __name__ == "__main__":
    main()

