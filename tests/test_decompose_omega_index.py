import json
import tempfile
import unittest
from pathlib import Path

from scripts.decompose_omega_index import decompose


class OmegaIndexDecompositionTests(unittest.TestCase):
    def test_decomposes_records_and_reports_dangling_evidence_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "known.md").write_text("proof", encoding="utf-8")
            source = {
                "index_id": "Ω.000",
                "status": "CANONICAL",
                "golden_source": "project.genome::v1.0.0",
                "authority_anchor": "Ω0_GENESIS_CORE",
                "records": [
                    {"id": "VX", "type": "SYSTEM", "role": "RUNTIME",
                     "lifecycle_state": "EVOLVING", "epistemic_state": "PARTIAL",
                     "canonical_owner": "VAIXLNS", "evidence_refs": ["known.md", "missing.md"]},
                    {"id": "VX", "type": "SYSTEM", "role": "RUNTIME",
                     "lifecycle_state": "EVOLVING", "epistemic_state": "PARTIAL",
                     "canonical_owner": "VAIXLNS", "evidence_refs": ["known.md"]}
                ]
            }
            index_path = root / "index.json"
            original = json.dumps(source, ensure_ascii=False, indent=2)
            index_path.write_text(original, encoding="utf-8")
            report = decompose(index_path, root)
            self.assertEqual(report["summary"]["record_count"], 2)
            self.assertEqual(report["summary"]["duplicate_id_count"], 1)
            self.assertEqual(report["summary"]["evidence_reference_count"], 3)
            self.assertTrue(any(x["code"] == "DUPLICATE_ID" for x in report["findings"]))
            self.assertTrue(any(x["code"] == "EVIDENCE_FILE_NOT_FOUND_IN_CHECKOUT" for x in report["findings"]))
            self.assertEqual(index_path.read_text(encoding="utf-8"), original)

    def test_empty_records_are_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            index_path = root / "index.json"
            index_path.write_text(json.dumps({"index_id": "Ω.000", "records": []}), encoding="utf-8")
            report = decompose(index_path, root)
            self.assertEqual(report["summary"]["record_count"], 0)
            self.assertEqual(report["summary"]["edge_count"], 0)


if __name__ == "__main__":
    unittest.main()
