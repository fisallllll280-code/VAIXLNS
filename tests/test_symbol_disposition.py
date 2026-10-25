from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.validate_symbol_disposition import (
    DISPOSITION, SYMBOLS, git_blob_sha, validate,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


class SymbolDispositionGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.manifest = json.loads((REPO_ROOT / DISPOSITION).read_text(encoding="utf-8"))
        self.symbols = json.loads((REPO_ROOT / SYMBOLS).read_text(encoding="utf-8"))
        evidence_path = "docs/indexes/REPOSITORY_DECISION_REGISTER_V1.md"
        full_path = self.root / evidence_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("# Immutable fixture\n", encoding="utf-8")
        digest = git_blob_sha(full_path.read_bytes())
        for record in self.manifest["records"]:
            for item in record["evidence"]:
                item["blob_sha"] = digest
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        for path, payload in ((DISPOSITION, self.manifest), (SYMBOLS, self.symbols)):
            full = self.root / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_manifest_review_passes_without_deleting(self):
        report = validate(self.root)
        self.assertEqual(report["audit_status"], "PASS", report)
        self.assertEqual(report["source_deletions_performed"], 0)
        self.assertEqual(report["active_projection_excluded"], [])
        self.assertEqual(report["disposition_candidates"], 3)
        self.assertEqual(report["symbols_proposed"], 7)

    def test_no_unapproved_exclusion(self):
        self.manifest["records"][0]["active_projection_excluded"] = True
        self.save()
        report = validate(self.root)
        self.assertIn("EXCLUSION_WITHOUT_PROOF_GATES:Ω.DISPOSITION.0001", report["errors"])

    def test_source_deletion_claim_is_rejected(self):
        self.manifest["records"][0]["source_deleted"] = True
        self.save()
        self.assertTrue(any("NO_SOURCE_DELETION_ALLOWED" in e
                            for e in validate(self.root)["errors"]))

    def test_evidence_must_match_pinned_blob(self):
        self.manifest["records"][0]["evidence"][0]["blob_sha"] = "0" * 40
        self.save()
        self.assertTrue(any("EVIDENCE_BLOB_MISMATCH" in e
                            for e in validate(self.root)["errors"]))

    def test_protected_source_blocked_even_with_approval(self):
        r = self.manifest["records"][0]
        r.update({
            "target_type": "repository_file",
            "target_locator": "registry/omega/omega-000-master-index.json",
            "active_projection_excluded": True,
            "state": "RETIRED_APPROVED",
            "dependency_audit": "PASS",
            "unique_knowledge_recovered": True,
            "reviewed_decision": {"reviewer": "example", "approval_ref": "EXAMPLE-ONLY", "date": "2026-10-25"},
            "rollback_snapshot": {"source_ref": "EXAMPLE-ONLY", "sha256": "a" * 64},
        })
        self.save()
        self.assertTrue(any("PROTECTED_SOURCE_CANNOT_BE_EXCLUDED" in e
                            for e in validate(self.root)["errors"]))

    def test_visual_verified_does_not_grant_authority(self):
        for entry in self.symbols["entries"]:
            if entry["role"] == "evidence.verified":
                entry["action_authority"] = "NONE"
        self.save()
        self.assertTrue(any("UNSAFE_VERIFIED_SYMBOL" in e
                            for e in validate(self.root)["errors"]))

    def test_duplicate_symbol_id_is_rejected(self):
        self.symbols["entries"].append(copy.deepcopy(self.symbols["entries"][0]))
        self.save()
        self.assertTrue(any("INVALID_OR_DUPLICATE_SYMBOL_ID" in e
                            for e in validate(self.root)["errors"]))


if __name__ == "__main__":
    unittest.main()
