import json
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases" / "cold_n2_validation"


class ColdN2SourceAuditTests(unittest.TestCase):
    def test_scalar_geometry_crosscheck_is_partial_not_certification(self):
        evidence = json.loads(
            (CASE / "results" / "geometry_source_crosscheck.json").read_text(encoding="utf-8")
        )
        self.assertTrue(evidence["scalar_controls_consistent"])
        self.assertFalse(evidence["full_contour_certified"])

    def test_missing_absolute_conditions_remain_null(self):
        inventory = yaml.safe_load((CASE / "boundary_conditions.yaml").read_text(encoding="utf-8"))
        missing = inventory["missing_required_values"]
        self.assertIsNone(missing["stagnation_temperature_K"])
        self.assertIsNone(missing["ambient_pressure_Pa_per_run"])
        self.assertIsNone(missing["digitized_wall_pressure_profiles"])

    def test_nasa_msfc_campaign_is_prohibited_as_dlr_anchor(self):
        inventory = yaml.safe_load((CASE / "boundary_conditions.yaml").read_text(encoding="utf-8"))
        reason = inventory["prohibited_substitutions"]["nasa_msfc_par_figures_11_12"]
        self.assertEqual(reason, "different_hardware_fluid_and_facility")


if __name__ == "__main__":
    unittest.main()
