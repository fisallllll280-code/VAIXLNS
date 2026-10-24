import pathlib
import tempfile
import unittest
from scripts.omega_library_audit import inventory

class TestLibraryAudit(unittest.TestCase):
    def test_inventory_and_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            (root/"requirements.txt").write_text("pytest==8.0.0\n")
            (root/"test_example.py").write_text("def test_ok(): pass\n")
            (root/".github"/"workflows").mkdir(parents=True)
            (root/".github"/"workflows"/"ci.yml").write_text("name: CI\n")
            result=inventory(root)
            self.assertEqual([len(result[k]) for k in ("manifests","tests","workflows")],[1,1,1])
            self.assertEqual(result["status"],"INVENTORY_ONLY")
            self.assertFalse(result["execution_performed"])
            self.assertEqual(len(result["manifests"][0]["sha256"]),64)
    def test_excludes_vendor(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=pathlib.Path(tmp)
            (root/"node_modules").mkdir()
            (root/"node_modules"/"package.json").write_text("{}")
            self.assertEqual(inventory(root)["manifests"],[])
if __name__=="__main__":unittest.main()
