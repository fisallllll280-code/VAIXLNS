import unittest
from tools.gov_sand_application_router import build
class Tests(unittest.TestCase):
 def setUp(self):
  self.roadmap={"initiatives":[{"id":"P1","domain":"PERSONAL","name":"Debt","status":"ACTION_REQUIRED","next":"Bank"},{"id":"P2","domain":"MIL","name":"SAND","status":"DRAFT","next":"Review"}]}
  self.targets={"targets":[{"id":"EATIZAZ","name":"Eatizaz","areas":["MIL"],"url":"https://eatizaz.mod.gov.sa/homepage","channel":"OFFICIAL_PORTAL_MANUAL","prerequisites":["authorization"]}]}
 def test_personal_excluded(self):
  x=build(self.roadmap,self.targets);self.assertEqual(len(x["applications"]),1);self.assertEqual(x["applications"][0]["system_id"],"P2")
 def test_no_fake_submission(self):
  x=build(self.roadmap,self.targets);self.assertEqual(x["actual_submissions"],0);self.assertEqual(x["applications"][0]["submission_status"],"NOT_SUBMITTED")
 def test_disallow_unapproved_automation(self):
  self.targets["targets"][0]["channel"]="AUTO_SUBMIT"
  with self.assertRaises(AssertionError):build(self.roadmap,self.targets)
if __name__=="__main__":unittest.main()
