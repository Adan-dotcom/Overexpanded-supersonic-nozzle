import csv
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

    def test_primary_vector_targets_are_frozen(self):
        provenance = json.loads(
            (CASE / "results" / "digitization_provenance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            provenance["article"]["pdf_sha256"],
            "f1d05035c7c39e2a589d827fd9461b2eaba0e763cd2e915a1f44cbd0649e1b73",
        )
        self.assertEqual(provenance["records"]["published_pressure_profiles"], 190)
        self.assertEqual(provenance["records"]["physical_separation_fig7a"], 31)
        self.assertEqual(provenance["records"]["incipient_pressure_fig7b"], 23)

        expected_counts = {
            "published_pressure_profiles.csv": 190,
            "physical_separation_fig7a.csv": 31,
            "incipient_pressure_fig7b.csv": 23,
        }
        for filename, expected in expected_counts.items():
            with (CASE / "results" / filename).open(newline="", encoding="utf-8") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), expected)

    def test_unreported_experimental_uncertainty_is_not_fabricated(self):
        targets = (
            ("published_pressure_profiles.csv", "experimental_uncertainty_pwall_over_pa"),
            ("physical_separation_fig7a.csv", "experimental_uncertainty_x_sep_over_rt"),
            ("incipient_pressure_fig7b.csv", "experimental_uncertainty_pinc_over_pa"),
        )
        for filename, field in targets:
            with (CASE / "results" / filename).open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertTrue(rows)
            self.assertTrue(all(row[field] == "" for row in rows))

    def test_nasa_msfc_campaign_is_prohibited_as_dlr_anchor(self):
        inventory = yaml.safe_load((CASE / "boundary_conditions.yaml").read_text(encoding="utf-8"))
        reason = inventory["prohibited_substitutions"]["nasa_msfc_par_figures_11_12"]
        self.assertEqual(reason, "different_hardware_fluid_and_facility")


if __name__ == "__main__":
    unittest.main()
