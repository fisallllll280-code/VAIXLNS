from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_engineering_drawing_job import validate_job  # noqa: E402


def valid_job() -> dict:
    return {
        "schema_version": "1.0.0",
        "job_id": "ED-BRACKET-001",
        "discipline": "mechanical",
        "jurisdiction": "ISO",
        "intent": "Produce a mounting bracket definition with an associated 2D drawing.",
        "units": {"length": "mm", "angle": "deg", "force": "N"},
        "coordinate_system": {"handedness": "right", "origin": "datum A", "axis_convention": "X right, Y up, Z out of plane"},
        "constraints": [
            {"id": "C-001", "type": "dimension", "description": "Overall length is 120 mm", "mandatory": True, "verification_state": "NOT_CHECKED"},
        ],
        "standards": [
            {"code": "ISO 128-1", "edition": "2020", "jurisdiction": "International", "source_uri": "https://www.iso.org/standard/65296.html", "selection_state": "SELECTED"},
        ],
        "geometry_backend": {"adapter": "opencascade", "version": "PINNED_BY_DEPLOYMENT", "capability_state": "NOT_CHECKED"},
        "deliverables": [
            {"format": "step", "purpose": "manufacturing_model", "required": True},
            {"format": "dxf", "purpose": "2d_drawing", "required": True},
        ],
        "validation_policy": {
            "require_independent_checker": True,
            "require_human_release": True,
            "block_on_unknown_standards": True,
            "independent_check_state": "NOT_RUN",
            "human_approval_state": "NOT_GRANTED",
            "simulation_required": True,
            "simulation_state": "NOT_RUN",
            "independent_check_evidence_ref": "",
            "human_approval_evidence_ref": "",
            "simulation_evidence_ref": "",
        },
    }


class EngineeringDrawingJobTests(unittest.TestCase):
    def test_valid_job_is_accepted_but_not_release_eligible(self):
        report = validate_job(valid_job())
        self.assertTrue(report["valid"])
        self.assertFalse(report["release_eligible"])
        self.assertIn("INDEPENDENT_CHECK_NOT_PASSED", report["release_blockers"])
        self.assertIn("MANDATORY_CONSTRAINT_NOT_PROVEN:C-001", report["release_blockers"])

    def test_units_must_be_explicit(self):
        job = valid_job()
        job["units"]["length"] = "unknown"
        report = validate_job(job)
        self.assertFalse(report["valid"])
        self.assertTrue(any("units.length" in item for item in report["errors"]))

    def test_duplicate_constraint_ids_are_rejected(self):
        job = valid_job()
        job["constraints"].append(dict(job["constraints"][0]))
        report = validate_job(job)
        self.assertFalse(report["valid"])
        self.assertTrue(any("duplicate constraint id" in item for item in report["errors"]))

    def test_http_standard_sources_are_rejected(self):
        job = valid_job()
        job["standards"][0]["source_uri"] = "http://example.test/code"
        report = validate_job(job)
        self.assertFalse(report["valid"])
        self.assertTrue(any("HTTPS source" in item for item in report["errors"]))

    def test_unconfirmed_standard_blocks_release(self):
        job = valid_job()
        job["standards"][0]["selection_state"] = "NEEDS_REVIEW"
        report = validate_job(job)
        self.assertTrue(report["valid"])
        self.assertFalse(report["release_eligible"])
        self.assertIn("STANDARD_SELECTION_UNCONFIRMED:ISO 128-1", report["release_blockers"])

    def test_missing_evidence_for_passed_constraint_is_rejected(self):
        job = valid_job()
        job["constraints"][0]["verification_state"] = "PASSED"
        report = validate_job(job)
        self.assertFalse(report["valid"])
        self.assertTrue(any("PASSED requires evidence_ref" in item for item in report["errors"]))

    def test_fully_proven_job_can_pass_release_gates(self):
        job = valid_job()
        job["constraints"][0]["verification_state"] = "PASSED"
        job["constraints"][0]["evidence_ref"] = "sha256:abc123"
        job["geometry_backend"]["capability_state"] = "VERIFIED"
        job["geometry_backend"]["capability_contract_ref"] = "capability-contract:v1"
        job["validation_policy"]["independent_check_state"] = "PASSED"
        job["validation_policy"]["independent_check_evidence_ref"] = "sha256:checker-proof"
        job["validation_policy"]["human_approval_state"] = "APPROVED"
        job["validation_policy"]["human_approval_evidence_ref"] = "approval-record:123"
        job["validation_policy"]["simulation_state"] = "PASSED"
        job["validation_policy"]["simulation_evidence_ref"] = "sha256:simulation-proof"
        report = validate_job(job)
        self.assertTrue(report["valid"])
        self.assertTrue(report["release_eligible"])
        self.assertEqual(report["release_blockers"], [])

    def test_unselected_backend_blocks_release(self):
        job = valid_job()
        job["geometry_backend"]["adapter"] = "not_selected"
        report = validate_job(job)
        self.assertTrue(report["valid"])
        self.assertFalse(report["release_eligible"])
        self.assertIn("GEOMETRY_BACKEND_NOT_SELECTED", report["release_blockers"])

    def test_untrusted_wrong_types_do_not_crash(self):
        job = valid_job()
        job["discipline"] = ["mechanical"]
        job["units"]["length"] = ["mm"]
        job["geometry_backend"]["adapter"] = ["opencascade"]
        job["deliverables"][0]["format"] = ["step"]
        report = validate_job(job)
        self.assertFalse(report["valid"])

    def test_failed_optional_constraint_still_blocks_release(self):
        job = valid_job()
        job["constraints"][0]["mandatory"] = False
        job["constraints"][0]["verification_state"] = "FAILED"
        report = validate_job(job)
        self.assertTrue(report["valid"])
        self.assertIn("CONSTRAINT_FAILED:C-001", report["release_blockers"])

    def test_not_applicable_standard_needs_rationale_and_can_be_confirmed(self):
        job = valid_job()
        job["standards"][0]["selection_state"] = "NOT_APPLICABLE_WITH_RATIONALE"
        report = validate_job(job)
        self.assertFalse(report["valid"])

    def test_not_applicable_constraint_requires_evidence(self):
        job = valid_job()
        job["constraints"][0]["verification_state"] = "NOT_APPLICABLE_WITH_EVIDENCE"
        report = validate_job(job)
        self.assertFalse(report["valid"])
        self.assertTrue(any("evidence_ref" in item for item in report["errors"]))

    def test_non_object_is_rejected(self):
        report = validate_job([])
        self.assertFalse(report["valid"])


if __name__ == "__main__":
    unittest.main()
