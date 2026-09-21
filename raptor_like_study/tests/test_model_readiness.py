import unittest

from scripts.check_model_readiness import check_readiness


STATUS = {
    "tracks": {
        "cold": {
            "software_screening_enabled": True,
            "production_enabled": False,
            "blockers": ["missing_experiment"],
        }
    }
}


class ModelReadinessTests(unittest.TestCase):
    def test_screen_can_be_enabled_without_enabling_production(self):
        ready, blockers = check_readiness(STATUS, "cold", "screen")
        self.assertTrue(ready)
        self.assertEqual(blockers, [])

    def test_production_fails_closed_and_reports_blocker(self):
        ready, blockers = check_readiness(STATUS, "cold", "production")
        self.assertFalse(ready)
        self.assertEqual(blockers, ["missing_experiment"])

    def test_unknown_track_fails_closed(self):
        ready, blockers = check_readiness(STATUS, "missing", "screen")
        self.assertFalse(ready)
        self.assertEqual(blockers, ["unknown_track:missing"])


if __name__ == "__main__":
    unittest.main()
