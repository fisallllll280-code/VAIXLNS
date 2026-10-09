from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_zero_loss_index import ARTIFACT_NAMES, IndexBuildError, build_index, build_payloads, validate_transition, verify_artifacts

REPO_ROOT = Path(__file__).resolve().parents[1]
TAXONOMY_PATH = REPO_ROOT / "registry/indexes/zero-loss-index-taxonomy.v1.json"


class ZeroLossIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        (self.root / "registry/indexes").mkdir(parents=True)
        (self.root / "registry/indexes/zero-loss-index-taxonomy.v1.json").write_bytes(TAXONOMY_PATH.read_bytes())
        (self.root / "docs/innovation").mkdir(parents=True)
        (self.root / "registry/omega").mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def write_fixture_sources(self):
        (self.root / "docs/innovation/INNOVATION_MASTER_INDEX.md").write_text(
            "# Innovation Index\n"
            "Legacy ID: 0001\n"
            "1. ARC-X — Evidence Reconstruction Engine\n"
            "2. Novel Capability Router\n"
            "[Schema](../../schemas/demo.schema.json)\n",
            encoding="utf-8",
        )
        (self.root / "schemas").mkdir()
        (self.root / "schemas/demo.schema.json").write_text(
            json.dumps({
                "schema_version": "1.0",
                "records": [{
                    "canonical_id": "DEMO.001",
                    "legacy_id": "0001",
                    "name": "Demonstration Entity",
                    "type": "CAPABILITY",
                    "status": "IMPLEMENTED",
                    "capabilities": ["source_coverage"],
                    "lineage": ["SOURCE-CLAIM"],
                }]
            }, indent=2),
            encoding="utf-8",
        )
        (self.root / "image.bin").write_bytes(b"\x00\xff\x10opaque-binary")

    def test_build_creates_all_28_views_and_source_hashes(self):
        self.write_fixture_sources()
        out = self.root / "build/zero-loss-index"
        report = build_index(self.root, out, legacy_start=1, legacy_end=4)
        self.assertEqual(report["state"], "PASS")
        index = json.loads((out / ARTIFACT_NAMES["index"]).read_text(encoding="utf-8"))
        source_index = json.loads((out / ARTIFACT_NAMES["sources"]).read_text(encoding="utf-8"))
        coverage = json.loads((out / ARTIFACT_NAMES["coverage"]).read_text(encoding="utf-8"))
        self.assertEqual(len(index["indexes"]), 28)
        self.assertEqual(index["source_count"], len(source_index["sources"]))
        self.assertTrue(all(len(source["sha256"]) == 64 for source in source_index["sources"]))
        self.assertEqual(coverage["legacy_id_coverage"]["fabricated_missing_records"], 0)
        self.assertEqual(coverage["canonical_promotions_performed"], 0)
        self.assertGreater(coverage["atomic_records_created"], 0)

    def test_unobserved_legacy_ids_are_gap_ranges_not_fake_records(self):
        self.write_fixture_sources()
        out = self.root / "build/zero-loss-index"
        build_index(self.root, out, legacy_start=1, legacy_end=4)
        coverage = json.loads((out / ARTIFACT_NAMES["coverage"]).read_text(encoding="utf-8"))
        records = [json.loads(line) for line in (out / ARTIFACT_NAMES["records"]).read_text(encoding="utf-8").splitlines()]
        ledger = coverage["legacy_id_coverage"]
        self.assertEqual(ledger["observed_explicit_ids"], ["0001"])
        self.assertEqual(ledger["unresolved_candidate_gap_ranges"], [{"start": "0002", "end": "0004"}])
        self.assertFalse(any(record.get("legacy_id") in {"0002", "0003", "0004"} for record in records))

    def test_every_record_has_source_lineage_and_digests(self):
        self.write_fixture_sources()
        out = self.root / "build/zero-loss-index"
        build_index(self.root, out, legacy_start=1, legacy_end=4)
        source_index = json.loads((out / ARTIFACT_NAMES["sources"]).read_text(encoding="utf-8"))
        source_ids = {source["source_id"] for source in source_index["sources"]}
        records = [json.loads(line) for line in (out / ARTIFACT_NAMES["records"]).read_text(encoding="utf-8").splitlines()]
        self.assertTrue(records)
        for record in records:
            self.assertIn(record["source_id"], source_ids)
            self.assertIn(record["source_id"], record["lineage"])
            self.assertEqual(len(record["source_sha256"]), 64)
            self.assertIn(record["ingestion_state"], {"SOURCE", "ATOMIC", "UNRESOLVED"})
            self.assertNotIn(record["status"], {"CANONICAL", "IMPLEMENTED", "VERIFIED"})

    def test_cross_references_are_direct_and_not_dependency_claims(self):
        self.write_fixture_sources()
        out = self.root / "build/zero-loss-index"
        build_index(self.root, out, legacy_start=1, legacy_end=4)
        payload = json.loads((out / ARTIFACT_NAMES["cross_references"]).read_text(encoding="utf-8"))
        found = [item for item in payload["references"] if item["to_path"] == "schemas/demo.schema.json"]
        self.assertTrue(found)
        self.assertTrue(all(item["classification_status"] == "DIRECT_TEXT_REFERENCE_NOT_DEPENDENCY" for item in found))
        self.assertTrue(all(item["relationship"] == "SOURCE_PATH_REFERENCE" for item in found))

    def test_json_round_trip_index_is_hash_verified(self):
        self.write_fixture_sources()
        out = self.root / "build/zero-loss-index"
        first = build_index(self.root, out, legacy_start=1, legacy_end=4)
        second = verify_artifacts(self.root, out)
        self.assertEqual(first, second)
        index_path = out / ARTIFACT_NAMES["index"]
        index_path.write_text(index_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaisesRegex(IndexBuildError, "GENERATED_ARTIFACT_DIGEST_MISMATCH"):
            verify_artifacts(self.root, out)

    def test_untrusted_transition_cannot_promote_to_canonical_or_implemented(self):
        record = {
            "source_id": "SRC-" + "a" * 24,
            "source_sha256": "a" * 64,
            "source_location": {"path": "legacy.md"},
            "lineage": ["SRC-" + "a" * 24],
            "canonical_id": None,
            "implementation": [],
            "tests": [],
            "evidence": [],
            "proof": [],
        }
        with self.assertRaisesRegex(ValueError, "CANONICAL_REQUIRES_SOURCE_GROUNDED_CANONICAL_ID"):
            validate_transition(record, "CANONICAL", authority_evidence="issue/1")
        record["canonical_id"] = "CANON.001"
        with self.assertRaisesRegex(ValueError, "CANONICAL_ADMISSION_REQUIRES_SEPARATE_AUTHORIZED_GATE"):
            validate_transition(record, "CANONICAL", authority_evidence="approved-decision/1")
        with self.assertRaisesRegex(ValueError, "IMPLEMENTED_REQUIRES_IMPLEMENTATION_TEST_AND_EVIDENCE"):
            validate_transition(record, "IMPLEMENTED", authority_evidence="approved-decision/1")

    def test_missing_taxonomy_fails_closed(self):
        with tempfile.TemporaryDirectory() as empty:
            with self.assertRaisesRegex(IndexBuildError, "TAXONOMY_MISSING"):
                build_payloads(Path(empty), Path(empty) / "out")

    def test_rebuild_is_deterministic_for_identical_source_tree(self):
        self.write_fixture_sources()
        out = self.root / "build/zero-loss-index"
        build_index(self.root, out, legacy_start=1, legacy_end=4)
        first = {name: (out / name).read_bytes() for name in ARTIFACT_NAMES.values()}
        build_index(self.root, out, legacy_start=1, legacy_end=4)
        second = {name: (out / name).read_bytes() for name in ARTIFACT_NAMES.values()}
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
