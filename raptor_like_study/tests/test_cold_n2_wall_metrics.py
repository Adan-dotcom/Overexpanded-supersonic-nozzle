import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from cases.cold_n2_external_screen.audit_external import (
    persistent_separation,
    pressure_shock,
    solver_log,
)


def sample(x, tau, pressure=100_000.0):
    return {
        "x_m": x,
        "tau_tangent_Pa": tau,
        "pressure_Pa": pressure,
        "y_plus": 0.5,
        "cell_width_normal_m": 5.0e-8,
    }


class ColdN2WallMetricsTests(unittest.TestCase):
    def test_persistent_shear_crossing_is_interpolated(self):
        samples = [
            sample(0.003, 5.0),
            sample(0.004, 4.0),
            sample(0.005, 3.0),
            sample(0.006, 2.0),
            sample(0.007, -1.0),
            sample(0.008, -2.0),
            sample(0.009, -3.0),
            sample(0.010, -4.0),
        ]
        x_sep, usable = persistent_separation(
            samples,
            throat_exclusion_m=0.002,
            lip_exclusion_m=0.002,
            persistence_points=2,
            tau_zero_tolerance_pa=1.0e-6,
        )
        self.assertEqual(len(usable), 8)
        self.assertAlmostEqual(x_sep, 0.0066666666667)

    def test_lip_crossing_is_excluded(self):
        samples = [
            sample(0.118, 4.0),
            sample(0.119, 3.0),
            sample(0.120, 2.0),
            sample(0.121, 1.0),
            sample(0.1235, -1.0),
            sample(0.1240, -2.0),
        ]
        x_sep, _ = persistent_separation(
            samples,
            throat_exclusion_m=0.002,
            lip_exclusion_m=0.002,
            persistence_points=2,
            tau_zero_tolerance_pa=1.0e-6,
        )
        self.assertIsNone(x_sep)

    def test_shock_uses_pressure_gradient_independently(self):
        samples = [
            sample(0.010, 2.0, 100_000.0),
            sample(0.011, 1.0, 101_000.0),
            sample(0.012, -1.0, 110_000.0),
            sample(0.013, -2.0, 111_000.0),
        ]
        x_shock, gradient = pressure_shock(samples)
        self.assertEqual(x_shock, 0.012)
        self.assertGreater(gradient, 0.0)

    def test_steady_normal_stop_does_not_require_final_time(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "solver.log"
            path.write_text(
                "STOP-REASON: relative-global-residual-target\n"
                "FINAL-STEP: 1421\n",
                encoding="ascii",
            )
            result = solver_log(path)
        self.assertTrue(result["normal_stop_recorded"])
        self.assertEqual(result["final_step"], 1421)
        self.assertIsNone(result["final_time_s"])

    def test_exit_without_stop_reason_is_not_normal(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "solver.log"
            path.write_text("FINAL-STEP: 2000\n", encoding="ascii")
            result = solver_log(path)
        self.assertFalse(result["normal_stop_recorded"])


if __name__ == "__main__":
    unittest.main()
