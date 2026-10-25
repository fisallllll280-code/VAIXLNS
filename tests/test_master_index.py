import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.build_master_index import (
    MasterIndexError, build_master_index, build_records, verify_snapshot,
)

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    return {
        "schema": "VAIXLNS.MasterIndexCapture.v1", "observed_at": "2026-10-25T00:00:00Z",
        "repositories": [{"repository": "owner/NEXENT", "visibility": "public"},
                         {"repository": "owner/NEXNET", "visibility": "public"}],
        "coverage": {key: {"state": "PARTIAL", "reason": "fixture scope"}
                     for key in ("repositories", "trees", "branches", "pull_requests")},
        "trees": [{"repository": "owner/NEXENT", "commit": "a" * 40, "tree_sha": "b" * 40,
                   "truncated": False, "entries": [{"path": "docs/a.md", "type": "blob", "mode": "100644", "sha": "c" * 40}]}],
        "branches": [{"repository": "owner/NEXENT", "name": "main", "commit": "a" * 40}],
        "pull_requests": [{"repository": "owner/NEXENT", "number": 1, "title": "fixture", "state": "open",
                           "head_commit": "a" * 40, "base_commit": "b" * 40}],
    }


class MasterIndexTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.capture = self.root / "capture.json"
        self.out = self.root / "out"
        self.data = fixture()
        self.write()

    def tearDown(self):
        self.tmp.cleanup()

    def write(self):
        self.capture.write_text(json.dumps(self.data))

    def build(self):
        return build_master_index(self.capture, self.out)

    def test_deterministic_rebuild_and_git_hash_semantics(self):
        first = self.build()
        self.assertEqual(first, self.build())
        rows = [json.loads(line) for line in (self.out / first["snapshot_id"] / "records.jsonl").read_text().splitlines()]
        file = next(r for r in rows if r["kind"] == "FILE")
        self.assertIsNone(file["metadata"]["content_sha256"])
        self.assertEqual(file["metadata"]["git_object_digest"]["algorithm"], "git-sha1")
        self.assertEqual(first["coverage"], "PARTIAL")

    def test_history_is_retained_and_identities_not_merged(self):
        first = self.build()
        self.data["observed_at"] = "2026-10-26T00:00:00Z"
        self.data["branches"][0]["commit"] = "d" * 40
        self.write()
        second = self.build()
        self.assertNotEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual(len(list(self.out.iterdir())), 2)
        self.assertEqual(second["counts"]["REPOSITORY"], 2)
        self.assertEqual(second["identity_merges"], 0)
        self.assertEqual(verify_snapshot(self.out / first["snapshot_id"]), first)

    def test_tampering_is_detected(self):
        result = self.build()
        folder = self.out / result["snapshot_id"]
        (folder / "records.jsonl").write_text("{}\n")
        with self.assertRaisesRegex(MasterIndexError, "ARTIFACT_DIGEST"):
            verify_snapshot(folder)
        with self.assertRaisesRegex(MasterIndexError, "IMMUTABLE_SNAPSHOT_CONFLICT"):
            self.build()

    def test_manifest_tampering_detected(self):
        result = self.build()
        folder = self.out / result["snapshot_id"]
        (folder / "manifest.json").write_text("{}")
        with self.assertRaisesRegex(MasterIndexError, "MANIFEST_DIGEST"):
            verify_snapshot(folder)

    def test_truncated_or_floating_tree_is_rejected(self):
        for key, value in (("truncated", True), ("commit", "main")):
            data = fixture()
            data["trees"][0][key] = value
            with self.subTest(key=key), self.assertRaises(MasterIndexError):
                build_records(data)

    def test_unsafe_paths_and_modes_rejected(self):
        for path in ("../secret", "/tmp/secret", "x/../secret", "a\\b", "./a", "."):
            data = fixture()
            data["trees"][0]["entries"][0]["path"] = path
            with self.subTest(path=path), self.assertRaises(MasterIndexError):
                build_records(data)
        data = fixture()
        data["trees"][0]["entries"][0]["mode"] = "160000"
        with self.assertRaises(MasterIndexError):
            build_records(data)

    def test_duplicate_records_rejected(self):
        for key in ("repositories", "trees", "branches", "pull_requests"):
            data = fixture()
            data[key].append(copy.deepcopy(data[key][0]))
            with self.subTest(key=key), self.assertRaisesRegex(MasterIndexError, "DUPLICATE"):
                build_records(data)

    def test_unknown_repository_rejected(self):
        self.data["branches"][0]["repository"] = "other/repo"
        with self.assertRaisesRegex(MasterIndexError, "INVALID_BRANCH"):
            build_records(self.data)

    def test_private_metadata_not_published(self):
        self.data["repositories"][0]["visibility"] = "private"
        with self.assertRaisesRegex(MasterIndexError, "RESTRICTED_METADATA"):
            build_records(self.data)

    def test_global_complete_claim_rejected(self):
        self.data["coverage"]["repositories"]["state"] = "COMPLETE"
        with self.assertRaisesRegex(MasterIndexError, "COVERAGE"):
            build_records(self.data)

    def test_existing_zero_loss_extractor_is_reused_without_promotion(self):
        checkout = self.root / "checkout"
        taxonomy = checkout / "registry/indexes/zero-loss-index-taxonomy.v1.json"
        taxonomy.parent.mkdir(parents=True)
        taxonomy.write_bytes((ROOT / "registry/indexes/zero-loss-index-taxonomy.v1.json").read_bytes())
        (checkout / "innovation.md").write_text("# Innovation\nLegacy ID: 0001\n- Proposal only\n")
        result = build_master_index(self.capture, self.out, root=checkout)
        folder = self.out / result["snapshot_id"]
        manifest = json.loads((folder / "manifest.json").read_bytes())
        self.assertEqual(manifest["semantic_extraction"], "ZERO_LOSS_28_VIEWS")
        self.assertGreater(result["counts"]["SEMANTIC_RECORD"], 0)
        self.assertEqual(result["canonical_promotions"], 0)
        self.assertEqual(len(json.loads((folder / "zero-loss-index.v1.json").read_bytes())["indexes"]), 28)

    def test_real_capture_counts(self):
        data = json.loads((ROOT / "registry/indexes/master-index-capture.2026-10-25.v1.json").read_bytes())
        rows = build_records(data)
        self.assertEqual(sum(r["kind"] == "FILE" for r in rows), 430)
        self.assertEqual(sum(r["kind"] == "DIRECTORY" for r in rows), 73)
        self.assertEqual(sum(r["kind"] == "BRANCH" for r in rows), 199)
        self.assertTrue(all(r["adoption_status"] == "UNVERIFIED" for r in rows))


if __name__ == "__main__":
    unittest.main()
