import copy, json, unittest
from pathlib import Path
from tools.validate_omega_2718_hm1 import validate
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"registry/omega/omega-2718-hm1-closure.v1.json").read_text(encoding="utf-8"))
class HM1Tests(unittest.TestCase):
    def test_manifest_passes_fail_closed_validation(self): self.assertEqual(validate(MANIFEST), [])
    def test_canonical_source_cannot_be_mutable(self):
        m=copy.deepcopy(MANIFEST); m["canonical_source"]["mutation"]="ALLOWED"; self.assertIn("CANONICAL_SOURCE_NOT_READ_ONLY",validate(m))
    def test_layer_omission_is_rejected(self):
        m=copy.deepcopy(MANIFEST); m["layers"].pop(); self.assertIn("LAYER_SET_OR_ORDER_INVALID",validate(m))
    def test_unconfigured_policy_has_no_fake_threshold(self):
        m=copy.deepcopy(MANIFEST); m["ratification_policy"]["approval_threshold"]=0.8; self.assertIn("UNCONFIGURED_THRESHOLD_MUST_BE_NULL",validate(m))
    def test_unverified_roots_cannot_be_injected(self):
        m=copy.deepcopy(MANIFEST); m["trust_roots"]=[{"root_id":"ROOT-001"}]; self.assertIn("TRUST_ROOTS_REQUIRE_EXTERNAL_CRYPTOGRAPHIC_VALIDATION",validate(m))
    def test_closed_state_cannot_be_claimed_without_external_verifier(self):
        m=copy.deepcopy(MANIFEST); m["closure_state"]="CLOSED_VERIFIED"; self.assertIn("CLOSED_REQUIRES_EXTERNAL_EVIDENCE_VERIFIER_NOT_IMPLEMENTED",validate(m))
    def test_acceptance_gates_are_complete(self):
        m=copy.deepcopy(MANIFEST); m["acceptance_gates"].pop(); self.assertIn("ACCEPTANCE_GATE_SET_MISMATCH",validate(m))
    def test_verified_requires_closed_evidence(self):
        m=copy.deepcopy(MANIFEST); m["state"]="VERIFIED"; self.assertIn("VERIFIED_STATE_WITHOUT_CLOSED_EVIDENCE",validate(m))
if __name__=="__main__": unittest.main()
