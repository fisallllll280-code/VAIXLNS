import unittest
from tools.omega_core_innovation import Capability, Evidence, PermitRequest, fuse, govern

class OmegaCoreTests(unittest.TestCase):
    def test_gap_partition(self):
        c=Capability("cap-1",frozenset({"a","b","c"}),frozenset({"a","b"}),frozenset({"a"}))
        self.assertEqual(c.gaps(), {"unavailable":["c"],"unverified":["b"]})

    def test_cannot_verify_absent(self):
        with self.assertRaises(ValueError):
            Capability("cap",frozenset({"a"}),frozenset(),frozenset({"a"}))

    def test_copy_does_not_inflate(self):
        e=Evidence("e1","source-A","hash1","claim",True,True)
        copy=Evidence("e2","source-A","hash1","claim",True,True,("e1",))
        self.assertEqual(fuse("claim",(e,))["support_count"],fuse("claim",(e,copy))["support_count"])

    def test_two_independent_origins(self):
        a=Evidence("a","source-A","h1","c",True,True)
        b=Evidence("b","source-B","h2","c",True,True)
        self.assertEqual(fuse("c",(a,b))["support_count"],2)

    def test_unverified_summary_not_support(self):
        original=Evidence("a","source-A","h1","c",True,False)
        summary=Evidence("b","source-A","h2","c",True,False,("a",))
        self.assertEqual(fuse("c",(original,summary))["support_count"],0)

    def test_missing_dependency_is_rejected(self):
        e=Evidence("e","root","h","c",True,True,("missing",))
        self.assertEqual(fuse("c",(e,))["support_count"],0)

    def test_experiment_requires_isolation(self):
        r=PermitRequest("cap","production","policy","EXPERIMENT",False,"claim")
        self.assertEqual(govern(r,{},policy_approved=True)["decision"],"REJECT")

    def test_production_requires_tests(self):
        r=PermitRequest("cap","production","policy","PRODUCTION",False,"claim")
        self.assertEqual(govern(r,{"claim":"claim","support_count":1},policy_approved=True)["decision"],"HOLD")

    def test_no_claim_mismatch(self):
        r=PermitRequest("cap","production","policy","PRODUCTION",True,"actual")
        self.assertEqual(govern(r,{"claim":"other","support_count":1},policy_approved=True)["decision"],"HOLD")

    def test_gate_does_not_issue_unsigned_production_approval(self):
        r=PermitRequest("cap","production","policy","PRODUCTION",True,"claim")
        self.assertEqual(govern(r,{"claim":"claim","support_count":1},policy_approved=True)["decision"],"ELIGIBLE_FOR_SIGNED_PERMIT")

if __name__ == "__main__":
    unittest.main()
