import csv
import json
import subprocess
import sys
import tempfile
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

    def test_provisional_ranges_keep_matched_pressure_explicitly_unavailable(self):
        inventory = yaml.safe_load((CASE / "boundary_conditions.yaml").read_text(encoding="utf-8"))
        missing = inventory["missing_required_values"]
        self.assertIsNone(missing["matched_experimental_ambient_pressure_Pa_per_run"])
        sensitivity = inventory["provisional_sensitivity"]
        self.assertEqual(sensitivity["stagnation_temperature_K"], [285.0, 295.0, 305.0])
        self.assertEqual(sensitivity["ambient_pressure_reference_Pa"], 100000.0)
        self.assertEqual(sensitivity["ambient_pressure_sensitivity_Pa"], [95000.0, 103000.0])
        self.assertEqual(sensitivity["stagnation_pressure_rule"], "P0_equals_NPR_times_Pa")
        self.assertEqual(inventory["published_targets"]["provisional_x_sep_uncertainty_rt"], 0.055)

    def test_mesh_family_geometry_evidence_is_not_flow_qualification(self):
        evidence = json.loads(
            (CASE / "mesh_family" / "results" / "mesh_family_summary.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(evidence["passes_geometry_gate"])
        self.assertEqual(
            [evidence["levels"][name]["cells"] for name in ("coarse", "medium", "fine")],
            [51840, 103680, 207360],
        )
        self.assertTrue(all(evidence["levels"][name]["blocks"] == 6 for name in evidence["levels"]))
        self.assertFalse(evidence["flow_was_solved"])
        self.assertFalse(evidence["wall_y_plus_evaluated"])
        self.assertFalse(evidence["physics_accepted"])
        self.assertFalse(evidence["training_eligible"])

    def test_screen_preprocessor_derives_p0_and_rejects_unapproved_t0(self):
        script = CASE / "flow_screen" / "prepare_run.py"
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            common = [
                sys.executable,
                str(script),
                "--pa-pa", "100000",
                "--npr", "30",
                "--wall", "adiabatic",
                "--turbulence-intensity", "0.01",
                "--length-scale-m", "0.001",
                "--mesh", "coarse",
                "--sweep", "startup",
                "--lua-output", str(output / "parameters.lua"),
                "--json-output", str(output / "parameters.json"),
            ]
            accepted = subprocess.run(
                [*common, "--t0-k", "295"], capture_output=True, text=True, check=False
            )
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            parameters = json.loads((output / "parameters.json").read_text())
            self.assertEqual(parameters["stagnation_pressure_Pa"], 3_000_000.0)
            rejected = subprocess.run(
                [*common, "--t0-k", "300"], capture_output=True, text=True, check=False
            )
            self.assertNotEqual(rejected.returncode, 0)

    def test_wall_postprocessor_uses_persistent_shear_crossing(self):
        script = CASE / "flow_screen" / "postprocess_wall.py"
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory)
            loads = artifact / "lmrsim" / "loads" / "0003"
            loads.mkdir(parents=True)
            (artifact / "run_parameters.json").write_text(
                json.dumps(
                    {
                        "ambient_pressure_Pa": 100000.0,
                        "NPR": 30.0,
                        "sweep_direction": "startup",
                    }
                )
            )
            header = (
                "pos.x pos.y pos.z n.x n.y n.z area cellWidthNormalToSurface outsign "
                "p rho T vel.x vel.y vel.z mu a Re y+ tau_wall.x tau_wall.y tau_wall.z "
                "q_total q_cond q_diff\n"
            )
            with (loads / "wall.dat").open("w", encoding="ascii") as stream:
                stream.write(header)
                shears = [2.0, 1.0, -1.0, -2.0, -2.0, -2.0, -2.0]
                for index, shear in enumerate(shears):
                    x = index * 0.001
                    p = 100000.0 + (50000.0 if index >= 4 else 0.0)
                    values = [
                        x, 0.01, 0.0, 0.0, 1.0, 0.0, 1e-6, 1e-5, 1,
                        p, 1.0, 295.0, 0.0, 0.0, 0.0, 1e-5, 300.0, 100.0, 1.0,
                        shear, 0.0, 0.0, 0.0, 0.0, 0.0,
                    ]
                    stream.write(" ".join(map(str, values)) + "\n")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--artifact-dir", str(artifact),
                    "--targets", str(CASE / "results" / "physical_separation_fig7a.csv"),
                    "--output", str(artifact / "metrics.json"),
                    "--profile-output", str(artifact / "profile.csv"),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            metrics = json.loads((artifact / "metrics.json").read_text())
            self.assertAlmostEqual(metrics["x_sep_m"], 0.0015)
            self.assertAlmostEqual(metrics["shock_x_m"], 0.0035)
            self.assertFalse(metrics["physics_accepted"])

    def test_failed_screen_decision_stays_out_of_training(self):
        decision = json.loads(
            (CASE / "results" / "screen_campaign_summary.json").read_text(encoding="utf-8")
        )
        self.assertEqual(decision["decision"], "NO_GO")
        self.assertEqual(len(decision["attempts"]), 2)
        self.assertTrue(all(not run["normal_solver_exit"] for run in decision["attempts"]))
        self.assertFalse(decision["sensitivity_quantified"])
        self.assertFalse(decision["physics_accepted"])
        self.assertFalse(decision["training_eligible"])

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
