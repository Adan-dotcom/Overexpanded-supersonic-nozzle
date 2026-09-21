"""Fail closed when an equilibrium-products LUT misses project tolerances."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ERROR_LIMITS_PERCENT = {
    "temperature_error": {"p99_percent": 0.25, "max_percent": 1.0},
    "pressure_error": {"p99_percent": 0.25, "max_percent": 1.0},
    "equilibrium_sound_speed_squared_error": {"p99_percent": 0.5, "max_percent": 2.0},
}


def assess(validation: dict) -> dict:
    checks = {}
    for quantity, limits in ERROR_LIMITS_PERCENT.items():
        metrics = validation.get(quantity, {})
        for metric, limit in limits.items():
            value = metrics.get(metric)
            name = f"{quantity}.{metric}"
            checks[name] = {
                "value_percent": value,
                "maximum_percent": limit,
                "pass": value is not None and value <= limit,
            }

    nonpositive = validation.get("nonpositive_sound_speed_squared_points")
    outside = validation.get("points_outside_reference_thermo_range")
    checks["positive_sound_speed_squared"] = {
        "value": nonpositive,
        "pass": nonpositive == 0,
    }
    checks["inside_reference_thermo_range"] = {
        "value": outside,
        "pass": outside == 0,
    }

    interpolation_passed = all(check["pass"] for check in checks.values())
    return {
        "table": validation.get("table"),
        "interpolation_passed": interpolation_passed,
        "qoi_convergence_required_separately": True,
        "production_ready": False,
        "production_ready_reason": (
            "A passing interpolation audit is necessary but not sufficient; x_sep must also "
            "converge across LUT resolutions and the products/air model must be valid."
        ),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("validation", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    validation = json.loads(args.validation.read_text(encoding="utf-8"))
    result = assess(validation)
    output = args.output or args.validation.with_name(args.validation.stem + ".quality.json")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["interpolation_passed"] else 2)


if __name__ == "__main__":
    main()
