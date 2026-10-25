import hashlib
import tempfile
import unittest
from pathlib import Path
from tools.vx_omega_genesis import inventory

class GenesisInventoryTests(unittest.TestCase):
    def test_deterministic_hash(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "index.md").write_bytes(b"omega")
            a = inventory(root, ["index.md"])
            b = inventory(root, ["index.md"])
            self.assertEqual(a, b)
            self.assertEqual(a["records"][0]["sha256"], hashlib.sha256(b"omega").hexdigest())
            self.assertFalse(a["claims"]["verified"])

    def test_missing_is_not_missing_claim(self):
        with tempfile.TemporaryDirectory() as d:
            result = inventory(Path(d), ["old-index.md"])
            self.assertEqual(result["exceptions"][0]["error"], "NOT_OBSERVED")
            self.assertFalse(result["claims"]["historical_complete"])

    def test_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            result = inventory(Path(d), ["../escape"])
            self.assertEqual(result["exceptions"][0]["error"], "OUTSIDE_ROOT")

    def test_no_file_mutation(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "project.genome"
            p.write_bytes(b"protected")
            inventory(root, ["project.genome"])
            self.assertEqual(p.read_bytes(), b"protected")

if __name__ == "__main__":
    unittest.main()
