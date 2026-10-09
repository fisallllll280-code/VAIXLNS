import json
import tempfile
import unittest
from pathlib import Path

from scripts.closed_workspaces import (
    MANIFEST_NAME,
    create_workspace,
    inspect_workspace,
    seal_workspace,
    verify_workspace,
)


class ClosedWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "closed"
        create_workspace(
            self.root, "mission-001", mission_id="MIS-001",
            source_revision="git:0123456789abcdef",
        )
        self.workspace = self.root / "mission-001"

    def tearDown(self):
        self.temp.cleanup()

    def test_created_workspace_defaults_closed(self):
        manifest = inspect_workspace(self.root, "mission-001")
        self.assertEqual(manifest["state"], "CREATED")
        self.assertEqual(manifest["isolation"]["network_access"], "DENY_BY_DEFAULT")
        self.assertFalse(manifest["isolation"]["production_credentials"])
        self.assertFalse(manifest["isolation"]["canonical_writes"])
        self.assertEqual(manifest["isolation"]["command_execution"], "DISABLED")
        self.assertEqual(manifest["authority_decision"], "PENDING")

    def test_seal_then_verify_is_deterministic(self):
        (self.workspace / "proposal.txt").write_text("candidate only\n", encoding="utf-8")
        first = seal_workspace(self.root, "mission-001")
        second = verify_workspace(self.root, "mission-001")
        self.assertEqual(first["state"], "SEALED")
        self.assertTrue(second["valid"])
        self.assertEqual(first["baseline_hash"], second["observed_hash"])

    def test_mutation_is_detected(self):
        (self.workspace / "proposal.txt").write_text("candidate only\n", encoding="utf-8")
        seal_workspace(self.root, "mission-001")
        (self.workspace / "proposal.txt").write_text("tampered\n", encoding="utf-8")
        result = verify_workspace(self.root, "mission-001")
        self.assertFalse(result["valid"])
        self.assertIn("FILE_DRIFT:proposal.txt", result["errors"])

    def test_added_file_is_detected(self):
        seal_workspace(self.root, "mission-001")
        (self.workspace / "unexpected.bin").write_bytes(b"x")
        result = verify_workspace(self.root, "mission-001")
        self.assertFalse(result["valid"])
        self.assertIn("FILE_DRIFT:unexpected.bin", result["errors"])

    def test_symlink_is_rejected_during_inventory(self):
        outside = Path(self.temp.name) / "outside.txt"
        outside.write_text("not part of workspace", encoding="utf-8")
        (self.workspace / "linked.txt").symlink_to(outside)
        with self.assertRaises(PermissionError):
            seal_workspace(self.root, "mission-001")

    def test_path_traversal_and_duplicate_creation_are_rejected(self):
        with self.assertRaises(ValueError):
            create_workspace(self.root, "../escape", mission_id="MIS", source_revision="rev")
        with self.assertRaises(FileExistsError):
            create_workspace(self.root, "mission-001", mission_id="MIS", source_revision="rev")

    def test_unsealed_workspace_does_not_verify(self):
        result = verify_workspace(self.root, "mission-001")
        self.assertFalse(result["valid"])
        self.assertEqual(result["state"], "UNSEALED")

    def test_manifest_identity_tampering_is_rejected(self):
        path = self.workspace / MANIFEST_NAME
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["workspace_id"] = "other"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ValueError):
            inspect_workspace(self.root, "mission-001")


if __name__ == "__main__":
    unittest.main()
