import json
import pathlib
import unittest
from tools.validate_gov_global_index import validate
P=pathlib.Path(__file__).resolve().parents[1]/"registry/gov-sand/global-systems.v1.json"
class IndexTests(unittest.TestCase):
    def test_registry_valid(self):
        self.assertGreater(validate(json.loads(P.read_text(encoding="utf-8"))),0)
    def test_fake_verified_rejected(self):
        d=json.loads(P.read_text(encoding="utf-8"))
        d["systems"][0]["status"]="VERIFIED"
        with self.assertRaises(AssertionError):validate(d)
    def test_duplicate_rejected(self):
        d=json.loads(P.read_text(encoding="utf-8"))
        d["systems"].append(dict(d["systems"][0]))
        with self.assertRaises(AssertionError):validate(d)
if __name__=="__main__":unittest.main()
