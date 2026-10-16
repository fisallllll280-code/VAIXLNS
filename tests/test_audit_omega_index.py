import json
import tempfile
import unittest
from pathlib import Path

from scripts.audit_omega_index import audit


class OmegaIndexAuditTests(unittest.TestCase):
    def test_reports_duplicate_ids_and_missing_evidence_without_mutating_index(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "evidence.md").write_text("evidence", encoding="utf-8")
            index_path = root / "omega.json"
            original = {
                "index_id": "Ω.000",
                "status": "CANONICAL",
                "records": [
                    {"id": "VX", "type": "SYSTEM", "lifecycle_state": "ACTIVE",
                     "epistemic_state": "PARTIAL", "evidence_refs": ["evidence.md", "missing.md"]},
                    {"id": "VX", "type": "SYSTEM", "lifecycle_state": "ACTIVE",
                     "epistemic_state": "PARTIAL", "evidence_refs": []}
                ]
            }
            encoded = json.dumps(original, ensure_ascii=False, indent=2)
            index_path.write_text(encoded, encoding="utf-8")

            report = audit(index_path, root)

            self.assertEqual(report["record_count"], 2)
            self.assertEqual(report["duplicate_ids"], ["VX"])
            self.assertEqual(report["missing_evidence_files"][0]["ref"], "missing.md")
            self.assertEqual(report["integrity_gate"], "FAIL")
            self.assertEqual(index_path.read_text(encoding="utf-8"), encoded)

    def test_detects_unknown_parent_and_unsafe_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            index_path = root / "omega.json"
            index_path.write_text(json.dumps({
                "index_id": "Ω.000",
                "records": [{
                    "id": "VX", "type": "SYSTEM", "lifecycle_state": "ACTIVE",
                    "epistemic_state": "PARTIAL", "parent": "NOT_REGISTERED",
                    "evidence_refs": ["../outside.md"]
                }]
            }), encoding="utf-8")

            report = audit(index_path, root)

            self.assertEqual(report["unknown_parent_refs"][0]["parent"], "NOT_REGISTERED")
            self.assertEqual(report["unsafe_evidence_refs"][0]["ref"], "../outside.md")
            self.assertEqual(report["integrity_gate"], "FAIL")


if __name__ == "__main__":
    unittest.main()
