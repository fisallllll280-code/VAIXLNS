import copy, hashlib, unittest
from scripts.gedf_research_pipeline import compile_capsule, validate_capsule

def capsule():
    a="Abstract describes a reproducible numerical method and stability limits."
    b="Independent benchmark evaluates error, convergence, and runtime."
    return {"schema":"vaixl.gedf.research-capsule.v1","mission_id":"MISSION-001",
      "research_question":"How can numerical solvers be selected and independently validated?",
      "domains":["mathematics","computation","software","physics","security"],
      "sources":[
       {"source_id":"SRC-01","url":"https://example.org/paper","source_type":"PAPER","evidence_level":"ABSTRACT_ONLY","captured_text":a,"captured_text_sha256":hashlib.sha256(a.encode()).hexdigest(),"retrieved_at_utc":"2026-10-16T00:00:00Z"},
       {"source_id":"SRC-02","url":"https://example.org/benchmark","source_type":"BENCHMARK","evidence_level":"TEST_EXECUTED","captured_text":b,"captured_text_sha256":hashlib.sha256(b.encode()).hexdigest(),"retrieved_at_utc":"2026-10-16T00:01:00Z"}],
      "claims":[{"claim_id":"CLM-01","statement":"Solver error should be evaluated under refinement.","source_ids":["SRC-01","SRC-02"],"epistemic_state":"SOURCE_ASSERTION","independent_confirmation":None}],
      "hypotheses":[{"hypothesis_id":"HYP-01","mechanism":"Use solver contracts to select numerical methods.","falsification_method":"Compare against analytic references and step-refinement benchmarks.","baseline_comparison":"Compare error, stability, and wall time against a fixed baseline.","alternatives":["Fixed solver selection","Adaptive solver selection"]}]}

class GedfResearchPipelineTests(unittest.TestCase):
    def test_plan_is_review_only(self):
        r=compile_capsule(capsule()); self.assertEqual(r["status"],"PENDING_HUMAN_REVIEW")
        self.assertFalse(r["execution_performed"]); self.assertFalse(r["canonical_promotion_allowed"])
        self.assertEqual(len(r["verification_tasks"]),11); self.assertEqual(len(r["plan_sha256"]),64)
    def test_tampering_detected(self):
        c=capsule(); c["sources"][0]["captured_text"]+=" altered"
        self.assertTrue(any("SHA-256 mismatch" in x for x in validate_capsule(c)))
    def test_unknown_source_fails_closed(self):
        c=capsule(); c["claims"][0]["source_ids"]=["MISSING"]
        self.assertTrue(any("unknown source_id" in x for x in validate_capsule(c)))
    def test_http_source_rejected(self):
        c=capsule(); c["sources"][0]["url"]="http://example.org/paper"
        self.assertTrue(any("HTTPS" in x for x in validate_capsule(c)))
    def test_hypothesis_requires_falsification_and_alternatives(self):
        c=capsule(); c["hypotheses"][0]["falsification_method"]=""; c["hypotheses"][0]["alternatives"]=[]
        errors=validate_capsule(c); self.assertTrue(any("falsification_method required" in x for x in errors)); self.assertTrue(any("alternatives required" in x for x in errors))
    def test_deterministic_plan(self):
        c=capsule(); self.assertEqual(compile_capsule(c)["plan_sha256"],compile_capsule(copy.deepcopy(c))["plan_sha256"])

if __name__=="__main__": unittest.main()
