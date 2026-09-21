"""Apply fail-closed numerical and physical qualification gates to a CFD case."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


BASE_LIMITS = {
    "relative_mass_imbalance": ("max", 0.005),
    "relative_total_energy_flux_imbalance": ("max", 0.01),
}

NOZZLE_SCREEN_LIMITS = {
    **BASE_LIMITS,
    "inner_residual_drop_decades": ("min", 2.0),
    "wall_y_plus_p95": ("max", 1.0),
    "wall_y_plus_max": ("max", 2.0),
}

PRODUCTION_LIMITS = {
    **NOZZLE_SCREEN_LIMITS,
    "separation_persistence_m": ("min", 0.001),
    "flow_through_times_before_sampling": ("min", 3.0),
    "x_sep_final_window_drift_m": ("max", 0.0001),
    "medium_fine_x_sep_difference_m": ("max", 0.0003),
}

NUMERICAL_BOOLEAN_REQUIRED = (
    "solver_exit_success",
    "finite_values_everywhere",
    "species_mass_fraction_closure_passed",
    "energy_conservation_audit_passed",
)

ZERO_REQUIRED = ("nonpositive_density_pressure_temperature_points",)

COMMON_MODEL_REQUIREMENTS = (
    "energy_audit_uses_total_enthalpy",
    "energy_reference_method_validated",
    "gas_model_temperature_range_validated",
)

PRODUCTION_MODEL_REQUIREMENTS = (
    "wall_thermal_model_justified",
    "turbulence_model_sensitivity_completed",
    "experimental_anchor_validated",
)

HOT_METHALOX_REQUIREMENTS = (
    "ambient_is_air",
    "exhaust_composition_is_methalox_products",
    "products_air_mixing_validated",
    "chemistry_regime_justified",
    "thermochemistry_reference_validated",
    "transport_properties_validated",
    "chemistry_sensitivity_completed",
)

COLD_N2_REQUIREMENTS = ("working_fluid_matches_experiment",)


def boolean_checks(metrics: dict, names: tuple[str, ...]) -> dict:
    return {
        name: {"value": metrics.get(name), "pass": metrics.get(name) is True}
        for name in names
    }


def evaluate(metrics: dict, stage: str) -> dict:
    if stage not in {"screen", "production"}:
        raise ValueError(f"Unsupported stage: {stage}")

    numerical_checks = boolean_checks(metrics, NUMERICAL_BOOLEAN_REQUIRED)
    for name in ZERO_REQUIRED:
        value = metrics.get(name)
        numerical_checks[name] = {"value": value, "pass": value == 0}

    case_family = metrics.get("case_family")
    if case_family == "products_air_benchmark":
        limits = BASE_LIMITS
    else:
        limits = NOZZLE_SCREEN_LIMITS if stage == "screen" else PRODUCTION_LIMITS
    for name, (comparison, limit) in limits.items():
        value = metrics.get(name)
        passed = value is not None and (
            value <= limit if comparison == "max" else value >= limit
        )
        numerical_checks[name] = {
            "value": value,
            "criterion": f"{comparison} {limit}",
            "pass": passed,
        }

    family_valid = case_family in {
        "products_air_benchmark",
        "cold_n2_validation",
        "hot_methalox_application",
    }
    model_checks = {
        "recognized_case_family": {"value": case_family, "pass": family_valid},
        **boolean_checks(metrics, COMMON_MODEL_REQUIREMENTS),
    }
    if case_family == "cold_n2_validation":
        model_checks.update(boolean_checks(metrics, COLD_N2_REQUIREMENTS))
    elif case_family in {"products_air_benchmark", "hot_methalox_application"}:
        model_checks.update(boolean_checks(metrics, HOT_METHALOX_REQUIREMENTS))

    if stage == "production":
        model_checks.update(boolean_checks(metrics, PRODUCTION_MODEL_REQUIREMENTS))

    numerical_pass = all(item["pass"] for item in numerical_checks.values())
    model_pass = all(item["pass"] for item in model_checks.values())
    physics_accepted = stage == "production" and numerical_pass and model_pass

    failed_numerical = [name for name, item in numerical_checks.items() if not item["pass"]]
    failed_model = [name for name, item in model_checks.items() if not item["pass"]]
    return {
        "case_id": metrics.get("case_id", "unknown"),
        "case_family": case_family,
        "stage": stage,
        "numerical_checks_pass": numerical_pass,
        "model_checks_pass": model_pass,
        "all_checks_pass": numerical_pass and model_pass,
        "physics_accepted": physics_accepted,
        "training_eligible": physics_accepted,
        "screening_survivor": numerical_pass and model_pass if stage == "screen" else None,
        "failed_numerical_checks": failed_numerical,
        "failed_model_checks": failed_model,
        "checks": {"numerical": numerical_checks, "model": model_checks},
        "policy_note": (
            "Static temperature below inlet T0 is not used as a reacting-flow energy gate. "
            "Energy qualification must use total enthalpy with a validated reference method."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metrics", type=Path)
    parser.add_argument("--stage", choices=("screen", "production"), required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    metrics = json.loads(args.metrics.read_text(encoding="utf-8"))
    payload = evaluate(metrics, args.stage)
    output = args.output or args.metrics.with_name(args.metrics.stem + ".acceptance.json")
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="ascii")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
