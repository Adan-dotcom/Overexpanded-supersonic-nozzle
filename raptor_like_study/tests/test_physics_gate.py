import unittest

from scripts.evaluate_physics_gate import evaluate


def passing_metrics(case_family="hot_methalox_application"):
    metrics = {
        "case_id": "test",
        "case_family": case_family,
        "solver_exit_success": True,
        "finite_values_everywhere": True,
        "species_mass_fraction_closure_passed": True,
        "energy_conservation_audit_passed": True,
        "nonpositive_density_pressure_temperature_points": 0,
        "relative_mass_imbalance": 0.001,
        "relative_total_energy_flux_imbalance": 0.002,
        "inner_residual_drop_decades": 3.0,
        "wall_y_plus_p95": 0.5,
        "wall_y_plus_max": 1.0,
        "separation_persistence_m": 0.002,
        "flow_through_times_before_sampling": 4.0,
        "x_sep_final_window_drift_m": 0.00005,
        "medium_fine_x_sep_difference_m": 0.0002,
        "energy_audit_uses_total_enthalpy": True,
        "energy_reference_method_validated": True,
        "gas_model_temperature_range_validated": True,
        "six_rank_execution": True,
        "vtk_export_present": True,
        "wall_thermal_model_justified": True,
        "turbulence_model_sensitivity_completed": True,
        "experimental_anchor_validated": True,
        "ambient_is_air": True,
        "exhaust_composition_is_methalox_products": True,
        "products_air_mixing_validated": True,
        "chemistry_regime_justified": True,
        "thermochemistry_reference_validated": True,
        "transport_properties_validated": True,
        "chemistry_sensitivity_completed": True,
    }
    if case_family == "cold_n2_validation":
        metrics["working_fluid_matches_experiment"] = True
    return metrics


class PhysicsGateTests(unittest.TestCase):
    def test_hot_production_can_pass_only_with_every_requirement(self):
        result = evaluate(passing_metrics(), "production")
        self.assertTrue(result["physics_accepted"])

    def test_fake_products_ambient_fails_closed(self):
        metrics = passing_metrics()
        metrics["ambient_is_air"] = False
        result = evaluate(metrics, "production")
        self.assertFalse(result["physics_accepted"])
        self.assertIn("ambient_is_air", result["failed_model_checks"])

    def test_missing_energy_method_fails_closed(self):
        metrics = passing_metrics()
        del metrics["energy_audit_uses_total_enthalpy"]
        result = evaluate(metrics, "production")
        self.assertFalse(result["physics_accepted"])

    def test_screen_never_becomes_training_data(self):
        result = evaluate(passing_metrics(), "screen")
        self.assertTrue(result["screening_survivor"])
        self.assertFalse(result["physics_accepted"])
        self.assertFalse(result["training_eligible"])

    def test_products_air_benchmark_does_not_require_nozzle_wall_metrics(self):
        metrics = passing_metrics("products_air_benchmark")
        for key in (
            "inner_residual_drop_decades",
            "wall_y_plus_p95",
            "wall_y_plus_max",
            "separation_persistence_m",
            "flow_through_times_before_sampling",
            "x_sep_final_window_drift_m",
            "medium_fine_x_sep_difference_m",
        ):
            metrics.pop(key)
        result = evaluate(metrics, "screen")
        self.assertTrue(result["screening_survivor"])
        self.assertFalse(result["training_eligible"])

    def test_products_air_benchmark_does_not_claim_chemistry_sensitivity(self):
        metrics = passing_metrics("products_air_benchmark")
        metrics["chemistry_sensitivity_completed"] = False
        result = evaluate(metrics, "screen")
        self.assertTrue(result["screening_survivor"])
        self.assertFalse(result["physics_accepted"])

    def test_products_air_benchmark_requires_vtk_and_six_ranks(self):
        for required in ("vtk_export_present", "six_rank_execution"):
            metrics = passing_metrics("products_air_benchmark")
            metrics[required] = False
            result = evaluate(metrics, "screen")
            self.assertFalse(result["screening_survivor"])
            self.assertIn(required, result["failed_model_checks"])


if __name__ == "__main__":
    unittest.main()
