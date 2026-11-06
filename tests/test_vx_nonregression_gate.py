import unittest

from scripts.vx_nonregression_gate import evaluate_nonregression


class VXNonRegressionGateTests(unittest.TestCase):
    def setUp(self):
        self.baseline = {
            "revision": "a" * 40,
            "metrics": {
                "success_rate": {"value": 0.90, "direction": "higher"},
                "latency_ms": {"value": 120, "direction": "lower"},
            },
        }
        self.candidate = {
            "revision": "b" * 40,
            "metrics": {
                "success_rate": {"value": 0.93, "direction": "higher"},
                "latency_ms": {"value": 110, "direction": "lower"},
            },
        }

    def test_improvement_is_review_only_not_automatic_promotion(self):
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "ELIGIBLE_FOR_REVIEW")
        self.assertFalse(report["promotion_authorized"])
        self.assertFalse(report["deployment_performed"])

    def test_any_capability_regression_rejects_candidate(self):
        self.candidate["metrics"]["success_rate"]["value"] = 0.89
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "REJECTED_REGRESSION")
        self.assertIn("REGRESSED", {x["result"] for x in report["comparisons"]})

    def test_lower_is_better_metric_direction(self):
        self.candidate["metrics"]["latency_ms"]["value"] = 125
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "REJECTED_REGRESSION")

    def test_no_improvement_is_not_promoted(self):
        self.candidate["metrics"] = {
            key: dict(value) for key, value in self.baseline["metrics"].items()
        }
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "NO_MEASURED_IMPROVEMENT")
        self.assertFalse(report["promotion_authorized"])

    def test_missing_metric_fails_closed(self):
        del self.candidate["metrics"]["latency_ms"]
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "BLOCKED")
        self.assertIn("METRIC_SET_MISMATCH", report["blockers"])

    def test_invalid_or_missing_values_fail_closed(self):
        self.candidate["metrics"]["success_rate"]["value"] = float("nan")
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "BLOCKED")
        self.assertIn("INVALID_METRIC_VALUE:success_rate", report["blockers"])

    def test_metric_direction_cannot_change(self):
        self.candidate["metrics"]["success_rate"]["direction"] = "lower"
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "BLOCKED")
        self.assertIn("INVALID_OR_CHANGED_METRIC_DIRECTION:success_rate", report["blockers"])

    def test_invalid_revision_fails_closed(self):
        self.candidate["revision"] = "not-a-commit"
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(report["state"], "BLOCKED")
        self.assertIn("INVALID_CANDIDATE_REVISION", report["blockers"])

    def test_same_revision_fails_closed(self):
        self.candidate["revision"] = self.baseline["revision"]
        report = evaluate_nonregression(self.baseline, self.candidate)
        self.assertIn("BASELINE_AND_CANDIDATE_REVISION_IDENTICAL", report["blockers"])

    def test_report_digest_is_deterministic(self):
        first = evaluate_nonregression(self.baseline, self.candidate)
        second = evaluate_nonregression(self.baseline, self.candidate)
        self.assertEqual(first["report_sha256"], second["report_sha256"])


if __name__ == "__main__":
    unittest.main()
