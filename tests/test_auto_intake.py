"""Integration-safe tests for repository source intake."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "auto_intake.py"
spec = importlib.util.spec_from_file_location("auto_intake", MODULE)
auto_intake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_intake)

class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.inbox = self.root / "intake" / "inbox"
        self.inbox.mkdir(parents=True)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, content):
        path = self.inbox / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def test_index_identity_preserved(self):
        self.put("فهرس-النظام.md", "سجل".encode("utf-8"))
        rows, objects = auto_intake.plan(self.root, self.inbox)
        self.assertEqual(rows[0]["category"], "INDEX")
        self.assertEqual(rows[0]["target_repository"], "VAIXLNS")
        self.assertEqual(rows[0]["review_state"], "PROPOSED_NOT_ADMITTED")
        self.assertTrue(rows[0]["target_path"].startswith("docs/indexes/intake/"))

    def test_research_routes_to_nexent(self):
        self.put("research-note.txt", b"test")
        rows, _ = auto_intake.plan(self.root, self.inbox)
        self.assertEqual(rows[0]["target_repository"], "NEXENT")

    def test_runtime_routes_to_vx(self):
        self.put("VX-runtime-engine.rs", b"pub fn x() {}")
        rows, _ = auto_intake.plan(self.root, self.inbox)
        self.assertEqual(rows[0]["target_repository"], "VX-runtime")

    def test_secret_and_link_blocked(self):
        self.put("model-config.json", b'{"api_key":"REALLY_SECRET_VALUE_1234"}')
        self.put("file.lnk", b"link")
        rows, objects = auto_intake.plan(self.root, self.inbox)
        self.assertTrue(all(row["decision"] == "BLOCKED" for row in rows))
        self.assertEqual(objects, {})

    def test_deduplicates_byte_objects_not_source_records(self):
        self.put("a.md", b"same")
        self.put("b.md", b"same")
        rows, objects = auto_intake.plan(self.root, self.inbox)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(objects), 1)

    def test_roundtrip_exact_binary_and_manifest(self):
        raw = b"\x00\x01\xfe"
        self.put("archive-data.zip", raw)
        rows, objects = auto_intake.plan(self.root, self.inbox)
        output = self.root / "build"
        auto_intake.write_bundle(output, rows, objects, include_payloads=True)
        self.assertEqual((output / rows[0]["library_object"]).read_bytes(), raw)
        self.assertEqual((output / "proposals" / rows[0]["target_repository"] / rows[0]["target_path"]).read_bytes(), raw)
        self.assertTrue(json.loads((output / "routing-manifest.v1.json").read_text())["no_canonical_promotion"])

    def test_oversize_is_held(self):
        self.put("oversized.md", b"abcdef")
        rows, objects = auto_intake.plan(self.root, self.inbox, max_bytes=4)
        self.assertEqual(rows[0]["decision"], "HELD")
        self.assertFalse(objects)

    def test_symlink_never_followed(self):
        target = self.root / "secret.md"
        target.write_text("hidden")
        (self.inbox / "link.md").symlink_to(target)
        rows, objects = auto_intake.plan(self.root, self.inbox)
        self.assertEqual(rows[0]["reason"], "SYMLINK")
        self.assertEqual(objects, {})

if __name__ == "__main__":
    unittest.main()
