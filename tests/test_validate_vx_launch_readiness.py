import copy
import json
import unittest
from pathlib import Path
from scripts.validate_vx_launch_readiness import inspect
BASE=json.loads(Path("registry/vx-launch-readiness.v1.json").read_text(encoding="utf-8"))
class ReadinessTests(unittest.TestCase):
    def check(self,change,expected):
        x=copy.deepcopy(BASE);change(x)
        self.assertIn(expected,inspect(x)["errors"])
    def test_baseline(self):
        x=inspect(BASE);self.assertEqual(x["status"],"HOLD");self.assertFalse(x["release_allowed"]);self.assertEqual(len(x["outstanding"]),10)
    def test_cost(self):self.check(lambda x:x["release_policy"].update(max_external_spend_sar=1),"ZERO_SPEND_REQUIRED")
    def test_unknown_cost(self):self.check(lambda x:x["release_policy"].update(max_external_spend_sar=None),"ZERO_SPEND_REQUIRED")
    def test_auto_publish(self):self.check(lambda x:x["release_policy"].update(auto_publish_allowed=True),"POLICY_AUTO_PUBLISH_ALLOWED")
    def test_main_merge(self):self.check(lambda x:x["release_policy"].update(main_merge_allowed=True),"POLICY_MAIN_MERGE_ALLOWED")
    def test_protected(self):self.check(lambda x:x["release_policy"].update(protected_files=[]),"PROTECTED_SOURCES")
    def test_model(self):self.check(lambda x:x["models"][0].update(admission="READY"),"UNVERIFIED_MODEL_PROMOTED:OpenAI")
    def test_market(self):self.check(lambda x:x["markets"][0].update(status="PUBLISHED"),"RELEASE_NEEDS_INDEPENDENT_APPROVAL:owned-web")
    def test_unknown_market(self):self.check(lambda x:x["markets"][0].update(id="not-a-market"),"UNKNOWN_MARKET")
    def test_duplicate_market(self):self.check(lambda x:x["markets"].append(copy.deepcopy(x["markets"][0])),"DUPLICATE_MARKET")
    def test_gate_absent(self):self.check(lambda x:x["gates"].pop("human_approval"),"GATE_SCHEMA")
    def test_no_self_approval(self):
        x=copy.deepcopy(BASE);x["gates"]={k:True for k in x["gates"]}
        self.assertEqual(inspect(x)["status"],"INDEPENDENT_APPROVAL_REQUIRED");self.assertFalse(inspect(x)["release_allowed"])
if __name__=="__main__":unittest.main()
