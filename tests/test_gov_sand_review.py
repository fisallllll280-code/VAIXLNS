import unittest
from tools.gov_sand_review import review
class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.data=[{"id":"P1","name":"Demo","status":"DRAFT","evidence":"doc.md","next":"Test","owner":"QA","priority":1}]
    def test_explanation(self):
        r=review(self.data)
        self.assertFalse(r["official_approval"])
        self.assertIn("doc.md",r["cases"][0]["explanation_ar"])
    def test_duplicate_rejected(self):
        with self.assertRaises(ValueError):review(self.data+self.data)
    def test_fake_approval_rejected(self):
        self.data[0]["status"]="APPROVED"
        with self.assertRaises(ValueError):review(self.data)
    def test_missing_evidence_rejected(self):
        self.data[0]["evidence"]=""
        with self.assertRaises(ValueError):review(self.data)
if __name__=="__main__":unittest.main()
