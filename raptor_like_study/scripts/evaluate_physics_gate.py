import argparse
import json
from pathlib import Path


LIMITS = {
    "relative_mass_imbalance": ("max", 0.005),
    "relative_total_energy_flux_imbalance": ("max", 0.01),
    "local_total_enthalpy_overshoot_fraction": ("max", 0.01),
    "inner_residual_drop_decades": ("min", 2.0),
    "wall_y_plus_p95": ("max", 1.0),
    "wall_y_plus_max": ("max", 2.0),
    "separation_persistence_m": ("min", 0.001),
    "flow_through_times_before_sampling": ("min", 3.0),
    "x_sep_final_window_drift_m": ("max", 0.0001),
    "medium_fine_x_sep_difference_m": ("max", 0.0003),
}

BOOLEAN_REQUIRED = {
    "solver_exit_success": True,
    "finite_values_everywhere": True,
}

ZERO_REQUIRED = (
    "nonpositive_density_pressure_temperature_points",
    "lut_out_of_domain_points",
)


def main():
    parser = argparse.ArgumentParser(description="Apply the project physics gate to one CFD case.")
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--stage", choices=("screen", "production"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    checks = {}

    for name, expected in BOOLEAN_REQUIRED.items():
        checks[name] = {"value": metrics.get(name), "pass": metrics.get(name) is expected}
    for name in ZERO_REQUIRED:
        value = metrics.get(name)
        checks[name] = {"value": value, "pass": value == 0}
    for name, (comparison, limit) in LIMITS.items():
        value = metrics.get(name)
        passed = value is not None and ((value <= limit) if comparison == "max" else (value >= limit))
        checks[name] = {"value": value, "criterion": f"{comparison} {limit}", "pass": passed}

    numerical_pass = all(item["pass"] for item in checks.values())
    physics_accepted = numerical_pass and args.stage == "production"
    payload = {
        "case_id": metrics.get("case_id", args.metrics.stem),
        "stage": args.stage,
        "all_checks_pass": numerical_pass,
        "physics_accepted": physics_accepted,
        "training_eligible": physics_accepted,
        "screening_survivor": numerical_pass if args.stage == "screen" else None,
        "failed_checks": [name for name, item in checks.items() if not item["pass"]],
        "checks": checks,
    }
    output = args.output or args.metrics.with_name(args.metrics.stem + ".acceptance.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
