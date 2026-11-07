import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from pcs001_validator import validate, digest

def valid_candidate():
    content={"artifact":"example","version":1}
    return {
      "state_id":"state-001","state_type":"artifact","schema_version":"pcs001.v1",
      "content":content,"content_digest":digest(content),"requested_status":"PROMOTED",
      "evidence":[{"evidence_id":"ev-1","content_digest":"a"*64,"issuer":"test","created_at":100,"scope":"artifact","verified":True}],
      "replay":{"input_refs":["input://1"],"input_digests":["b"*64],"runtime_version":"python-3.12","configuration_digest":"c"*64,"command":"python replay.py"},
      "verification":[{"verifier":"independent-ci","verifier_version":"1","result":"PASS","timestamp":101,"evidence_digest":"a"*64}],
      "provenance":{"source_digest":"d"*64,"producer":"ci","derivation":"build-1","parents":[]},
      "promotion":{"from_state":"VERIFIED","to_state":"PROMOTED","policy_id":"policy-1","policy_digest":"e"*64,"authorized_principal":"release-bot","approval_evidence":"approval-1","timestamp":102,"transition_digest":"f"*64,"authorized":True},
      "validity":{"expires_at":9999999999,"revoked":False}
    }

class PCS001Tests(unittest.TestCase):
    def test_complete_candidate_admitted(self):
        self.assertEqual(validate(valid_candidate(),now=200)["decision"],"ADMIT")
    def test_missing_evidence_denied(self):
        c=valid_candidate(); c["evidence"]=[]
        self.assertIn("DENY_EVIDENCE_MISSING",validate(c)["reasons"])
    def test_content_tampering_denied(self):
        c=valid_candidate(); c["content"]["version"]=2
        self.assertIn("DENY_INTEGRITY_MISMATCH",validate(c)["reasons"])
    def test_missing_replay_denied(self):
        c=valid_candidate(); c["replay"]={}
        self.assertIn("DENY_NOT_REPLAYABLE",validate(c)["reasons"])
    def test_failed_verification_denied(self):
        c=valid_candidate(); c["verification"][0]["result"]="FAIL"
        self.assertIn("DENY_VERIFICATION",validate(c)["reasons"])
    def test_missing_provenance_denied(self):
        c=valid_candidate(); c["provenance"]={}
        self.assertIn("DENY_PROVENANCE",validate(c)["reasons"])
    def test_unauthorized_promotion_denied(self):
        c=valid_candidate(); c["promotion"]["authorized"]=False
        self.assertIn("DENY_PROMOTION_AUTHORITY",validate(c)["reasons"])
    def test_revoked_evidence_state_denied(self):
        c=valid_candidate(); c["validity"]["revoked"]=True
        self.assertIn("DENY_STALE_OR_REVOKED",validate(c)["reasons"])
    def test_expired_candidate_denied(self):
        c=valid_candidate(); c["validity"]["expires_at"]=10
        self.assertIn("DENY_STALE_OR_REVOKED",validate(c,now=11)["reasons"])
    def test_missing_contract_field_denied(self):
        c=valid_candidate(); del c["replay"]
        self.assertEqual(validate(c)["decision"],"DENY")

if __name__=="__main__": unittest.main()
