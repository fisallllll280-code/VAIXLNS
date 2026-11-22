import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from stage_intake_review import stage

class StagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.inbox = self.root / "intake/inbox"
        self.inbox.mkdir(parents=True)
    def tearDown(self):
        self.tmp.cleanup()
    def put(self, name, data):
        path = self.inbox / name
        path.write_bytes(data)
        return path
    def test_exact_text_staged(self):
        self.put("index-current.md", b"ABC")
        output = stage(self.root, self.inbox)
        self.assertEqual(output["review_materialized"], 1)
        self.assertEqual(len(list((self.root / "docs/indexes/intake").glob("*"))), 1)
    def test_binary_held(self):
        self.put("index-scan.pdf", b"%PDF-1.7")
        output = stage(self.root, self.inbox)
        self.assertEqual(output["review_materialized"], 0)
        self.assertFalse((self.root / "library/objects").exists())
    def test_cross_repo_not_written(self):
        self.put("research-notes.md", b"notes")
        output = stage(self.root, self.inbox)
        self.assertEqual(output["held_or_external"], 1)
        self.assertFalse((self.root / "library/objects").exists())
    def test_secret_not_written(self):
        self.put("model.json", b'{"api_key":"REAL_SECRET_VALUE_1234"}')
        output = stage(self.root, self.inbox)
        self.assertEqual(output["review_materialized"], 0)
        self.assertFalse((self.root / "library/objects").exists())

if __name__ == "__main__":
    unittest.main()
