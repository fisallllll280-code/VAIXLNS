import json
import pathlib
import unittest
P=pathlib.Path(__file__).resolve().parents[1]/"registry/gov-sand/priority-roadmap.v1.json"
class TestRoadmap(unittest.TestCase):
    def test_unique_ordered_priorities(self):
        obj=json.loads(P.read_text(encoding="utf-8"))
        xs=obj["initiatives"]
        self.assertEqual(len(xs),len(set(x["id"] for x in xs)))
        self.assertEqual([x["priority"] for x in xs],list(range(1,len(xs)+1)))
    def test_evidence_and_next_action(self):
        for x in json.loads(P.read_text(encoding="utf-8"))["initiatives"]:
            self.assertTrue(x["evidence"] and x["next"] and x["owner"])
    def test_no_fake_integration(self):
        a=json.loads(P.read_text(encoding="utf-8"))["initiatives"]
        self.assertEqual(next(x for x in a if x["id"]=="P09")["status"],"BLOCKED")
        self.assertNotEqual(next(x for x in a if x["id"]=="P03")["status"],"APPROVED")
if __name__=="__main__": unittest.main()
