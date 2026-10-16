import base64, json, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vx_capability_gateway import CapabilityDenied, GitHubReadOnlyConnector, build_capability_index, write_index_atomic, sha256_bytes
class Response:
    status = 200
    def __init__(self, body): self.body = body
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n=-1): return self.body[:n]
class CapabilitySliceTests(unittest.TestCase):
    def setUp(self):
        self.identity = {"authenticated": True, "subject": "test:ci", "scopes": ["github.read_file"]}
        self.registry = {"github.read_file": {"status": "ADMITTED", "mode": "read_only"}}
        payload = {"type": "file", "sha": "blob123", "content": base64.b64encode(b"hello").decode()}
        self.connector = GitHubReadOnlyConnector(token="test-token", opener=lambda req, timeout: Response(json.dumps(payload).encode()))
    def invoke(self, **kwargs):
        args = {"identity": self.identity, "registered_tools": self.registry, "repository": "owner/repo", "path": "README.md"}
        args.update(kwargs); return self.connector.invoke(**args)
    def test_read_connector_returns_content_and_digest(self):
        result = self.invoke()
        self.assertEqual(result["content"], "hello"); self.assertEqual(result["content_sha256"], sha256_bytes(b"hello"))
        self.assertTrue(result["read_only"])
    def test_missing_identity_denied(self):
        with self.assertRaisesRegex(CapabilityDenied, "IDENTITY_REQUIRED"): self.invoke(identity={})
    def test_missing_scope_denied(self):
        with self.assertRaisesRegex(CapabilityDenied, "SCOPE_DENIED"): self.invoke(identity={**self.identity, "scopes": []})
    def test_unregistered_tool_denied(self):
        with self.assertRaisesRegex(CapabilityDenied, "TOOL_NOT_REGISTERED"): self.invoke(registered_tools={})
    def test_path_traversal_denied(self):
        with self.assertRaisesRegex(CapabilityDenied, "INVALID_PATH"): self.invoke(path="../secrets")
    def test_index_detects_content_change_and_records_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root / "agent.py"; source.write_text("x=1\n")
            first = build_capability_index(root, repo_id="owner/repo", source_ref="abc")
            source.write_text("x=2\n"); second = build_capability_index(root, repo_id="owner/repo", source_ref="def")
            self.assertNotEqual(first["files"][0]["sha256"], second["files"][0]["sha256"])
            self.assertEqual(first["files"][0]["source"]["ref"], "abc")
    def test_atomic_write_replaces_index_without_temp_residue(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "index.json"; write_index_atomic({"file_count": 1, "files": []}, target)
            write_index_atomic({"file_count": 2, "files": []}, target)
            self.assertEqual(json.loads(target.read_text())["file_count"], 2)
            self.assertEqual(list(Path(directory).glob("*.tmp")), [])
if __name__ == "__main__": unittest.main()
