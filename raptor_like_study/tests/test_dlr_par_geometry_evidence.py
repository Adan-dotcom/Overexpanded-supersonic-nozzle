import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "raptor_like_study" / "cases" / "dlr_par_geometry" / "results"


class DlrParGeometryEvidenceTests(unittest.TestCase):
    def test_contour_evidence_matches_tracked_source(self):
        audit = json.loads((RESULTS / "contour_audit.json").read_text(encoding="utf-8"))
        source_bytes = (ROOT / "DLR_PAR_full_contour.csv").read_bytes()
        canonical_bytes = source_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        source_digest = hashlib.sha256(canonical_bytes).hexdigest()
        self.assertEqual(audit["source_sha256"], source_digest)
        self.assertEqual(audit["sha256_line_ending_policy"], "canonical_lf")
        self.assertTrue(audit["checks_pass"])
        self.assertEqual(audit["row_count"], 385)

    def test_geometry_screen_never_claims_flow_or_training_eligibility(self):
        metrics = json.loads((RESULTS / "grid_quality.json").read_text(encoding="utf-8"))
        self.assertTrue(metrics["all_checks_pass"])
        self.assertFalse(metrics["flow_was_solved"])
        self.assertFalse(metrics["wall_y_plus_evaluated"])
        self.assertFalse(metrics["physics_accepted"])
        self.assertFalse(metrics["training_eligible"])


if __name__ == "__main__":
    unittest.main()
