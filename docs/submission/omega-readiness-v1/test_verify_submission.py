"""Offline tests of submission document verifier; no runtime test results inferred."""
import csv
import tempfile
import unittest
from pathlib import Path
from verify_submission import check, REQUIRED

class SubmissionVerifierTests(unittest.TestCase):
    def make_fixture(self, directory: Path, status="PROPOSED"):
        for name in REQUIRED:
            if not name.endswith(".csv"):
                (directory / name).write_text("fixture\n", encoding="utf-8")
        claim_columns = ["claim_id","claim","source_repository","source_commit",
                         "implementation_path","test_id","evidence_uri","independent_reviewer","status","blocker"]
        with (directory/"CLAIM_PROOF_REGISTER.csv").open("w", encoding="utf-8", newline="") as f:
            w=csv.DictWriter(f,fieldnames=claim_columns)
            w.writeheader()
            w.writerow({"claim_id":"C1","claim":"test", "status":status,
                        "source_commit":"UNKNOWN","test_id":"NOT_MAPPED",
                        "evidence_uri":"UNAVAILABLE","independent_reviewer":"UNASSIGNED"})
        comp_columns=["control_id","domain","applicability","requirement_source",
                      "control_evidence","owner","state","gap","next_action"]
        with (directory/"COMPLIANCE_MATRIX.csv").open("w", encoding="utf-8", newline="") as f:
            w=csv.DictWriter(f,fieldnames=comp_columns)
            w.writeheader()
            w.writerow({"control_id":"CMP1","domain":"test"})

    def test_proposed_claim_can_be_document_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.make_fixture(p)
            actual=check(p)
            self.assertEqual(actual["document_validation"],"PASS")
            self.assertEqual(actual["submission_decision"],"HOLD")

    def test_false_verified_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.make_fixture(p,status="VERIFIED")
            actual=check(p)
            self.assertTrue(any("UNSUPPORTED_VERIFIED" in x for x in actual["findings"]))

    def test_missing_file_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);self.make_fixture(p)
            (p/"README.md").unlink()
            self.assertEqual(check(p)["document_validation"],"FAIL")

if __name__=="__main__":
    unittest.main()
