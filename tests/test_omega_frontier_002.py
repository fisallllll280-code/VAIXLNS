import unittest

from scripts.omega_frontier_002 import (
    assurance_causality_map, assurance_singularity, compare_refactor,
    compete_hypotheses, minimal_proof_surface, reconcile_histories,
    synthesize_forbidden_states, uncertainty_to_action,
)


class OmegaFrontier002Tests(unittest.TestCase):
    def test_uncertainty_blocks_only_affected_actions(self):
        result = uncertainty_to_action([
            {"condition": "stale-policy", "state": "UNKNOWN", "affected_actions": ["deploy", "merge"]},
            {"condition": "signed-input", "state": "VERIFIED", "affected_actions": ["inspect"]},
        ])
        self.assertEqual(result["decision"], "RESTRICTED")
        self.assertEqual(result["blocked_actions"]["deploy"], ["stale-policy"])
        self.assertNotIn("inspect", result["blocked_actions"])

    def test_invalid_uncertainty_input_is_incomplete(self):
        self.assertEqual(uncertainty_to_action([{"condition": "x", "affected_actions": "deploy"}])["decision"],
                         "INCOMPLETE")

    def test_singularity_finds_shared_dependency(self):
        result = assurance_singularity({"A": ["clock", "sig"], "B": ["clock"], "C": ["clock"]})
        self.assertEqual(result["candidates"][0]["dependency"], "clock")
        self.assertEqual(result["candidates"][0]["affected_count"], 3)
        self.assertIn("HEURISTIC", result["analysis"])

    def test_hypothesis_engine_does_not_claim_proof(self):
        result = compete_hypotheses([
            {"id": "H1", "supporting_evidence": ["e1", "e2"], "refuting_evidence": []},
            {"id": "H2", "supporting_evidence": ["e3"], "refuting_evidence": ["e4"]},
        ])
        self.assertEqual(result["result"], "LEADING_HYPOTHESIS_ONLY")

    def test_hypothesis_tie_remains_unresolved(self):
        result = compete_hypotheses([
            {"id": "H1", "supporting_evidence": ["e1"], "refuting_evidence": []},
            {"id": "H2", "supporting_evidence": ["e2"], "refuting_evidence": []},
        ])
        self.assertEqual(result["result"], "UNRESOLVED")

    def test_forbidden_state_returns_counterexample(self):
        result = synthesize_forbidden_states("start", {"start": ["safe"], "safe": ["forbidden"]},
                                             ["forbidden"], max_depth=4)
        self.assertEqual(result["result"], "COUNTEREXAMPLE_FOUND")
        self.assertEqual(result["path"], ["start", "safe", "forbidden"])

    def test_forbidden_state_no_path_is_bounded_not_universal(self):
        result = synthesize_forbidden_states("start", {"start": ["safe"], "safe": []},
                                             ["forbidden"], max_depth=4)
        self.assertEqual(result["result"], "NO_COUNTEREXAMPLE_WITHIN_SEARCH_BOUND")
        self.assertIn("not a universal proof", result["warning"])
        self.assertFalse(result["exhaustive_over_reachable_graph"])
        complete = synthesize_forbidden_states("start", {"start": ["safe"], "safe": []},
                                               ["forbidden"], max_depth=4, model_complete=True)
        self.assertTrue(complete["exhaustive_over_reachable_graph"])

    def test_history_reconciliation_preserves_concurrent_order_ambiguity(self):
        result = reconcile_histories([
            {"source": "A", "events": [{"id": "a", "caused_by": []}]},
            {"source": "B", "events": [{"id": "b", "caused_by": []}]},
        ])
        self.assertEqual(result["result"], "RECONCILABLE")
        self.assertEqual(result["causal_edges"], [])

    def test_history_reconciliation_detects_same_id_conflict(self):
        result = reconcile_histories([
            {"source": "A", "events": [{"id": "x", "value": 1, "caused_by": []}]},
            {"source": "B", "events": [{"id": "x", "value": 2, "caused_by": []}]},
        ])
        self.assertEqual(result["result"], "CONFLICTED")

    def test_history_reconciliation_detects_causal_cycle(self):
        result = reconcile_histories([{"source": "A", "events": [
            {"id": "a", "caused_by": ["b"]}, {"id": "b", "caused_by": ["a"]}]}])
        self.assertEqual(result["result"], "CONFLICTED")
        self.assertTrue(any(x.get("reason") == "CAUSAL_CYCLE" for x in result["conflicts"]))

    def test_refactor_detects_capability_expansion(self):
        result = compare_refactor(
            {"properties": {"determinism": True}, "capabilities": ["READ"]},
            {"properties": {"determinism": True}, "capabilities": ["READ", "WRITE"]},
            ["determinism"])
        self.assertEqual(result["result"], "CONTRACT_REGRESSION")
        self.assertEqual(result["added_capabilities"], ["WRITE"])

    def test_refactor_missing_coverage_is_inconclusive(self):
        result = compare_refactor({"properties": {}}, {"properties": {}}, ["replay"])
        self.assertEqual(result["result"], "INCONCLUSIVE")

    def test_minimal_surface_preserves_mandatory_evidence(self):
        result = minimal_proof_surface({"A", "B"}, [
            {"id": "mandatory", "verified": True, "mandatory": True, "covers": ["A"]},
            {"id": "extra-a", "verified": True, "covers": ["A"]},
            {"id": "b", "verified": True, "covers": ["B"]},
            {"id": "unverified", "verified": False, "covers": ["B"]},
        ])
        self.assertEqual(result["result"], "MINIMAL_WITHIN_BOUNDED_CANDIDATES")
        self.assertEqual(result["selected_evidence"], ["b", "mandatory"])
        self.assertTrue(result["mandatory_preserved"])

    def test_minimal_surface_rejects_uncovered_obligation(self):
        result = minimal_proof_surface({"A", "B"}, [{"id": "a", "verified": True, "covers": ["A"]}])
        self.assertEqual(result["result"], "INCOMPLETE")
        self.assertEqual(result["reason"], "OBLIGATION_UNCOVERED")

    def test_assurance_map_fails_closed(self):
        result = assurance_causality_map(
            [{"id": "I1"}, {"id": "I2"}],
            {"I1": ["e1"], "I2": ["e2"]},
            {"e1": "VERIFIED", "e2": "UNKNOWN"})
        self.assertEqual(result["invariants"][0]["status"], "ELIGIBLE_FOR_NEXT_GATE")
        self.assertEqual(result["invariants"][1]["status"], "UNRESOLVED")
        self.assertFalse(result["authority_granted"])
        self.assertFalse(result["execution_performed"])


    def test_unresolved_condition_without_actions_is_incomplete(self):
        result = uncertainty_to_action([{"condition": "unknown-source", "state": "UNKNOWN",
                                         "affected_actions": []}])
        self.assertEqual(result["decision"], "INCOMPLETE")
        self.assertEqual(result["findings"][0]["status"], "INVALID_INPUT")

    def test_invalid_hypothesis_prevents_a_false_leader(self):
        result = compete_hypotheses([
            {"id": "H1", "supporting_evidence": ["e1", "e2"], "refuting_evidence": []},
            {"id": "H1", "supporting_evidence": ["e3"], "refuting_evidence": []},
        ])
        self.assertEqual(result["result"], "INCOMPLETE")

    def test_missing_causal_relation_is_unobservable(self):
        result = reconcile_histories([{"source": "A", "events": [{"id": "event-1"}]}])
        self.assertEqual(result["result"], "UNOBSERVABLE")

    def test_capability_widening_precedes_missing_property_coverage(self):
        result = compare_refactor(
            {"properties": {}, "capabilities": ["READ"]},
            {"properties": {}, "capabilities": ["READ", "WRITE"]},
            ["replay"])
        self.assertEqual(result["result"], "CONTRACT_REGRESSION")

    def test_duplicate_evidence_ids_fail_minimization_closed(self):
        result = minimal_proof_surface({"A"}, [
            {"id": "same", "verified": True, "covers": ["A"]},
            {"id": "same", "verified": True, "covers": ["A"]},
        ])
        self.assertEqual(result["result"], "INCOMPLETE")
        self.assertEqual(result["reason"], "DUPLICATE_EVIDENCE_ID")

    def test_unverified_mandatory_evidence_cannot_be_dropped(self):
        result = minimal_proof_surface({"A"}, [
            {"id": "mandatory", "verified": False, "mandatory": True, "covers": ["A"]},
            {"id": "optional", "verified": True, "covers": ["A"]},
        ])
        self.assertEqual(result["result"], "INCOMPLETE")
        self.assertEqual(result["reason"], "MANDATORY_EVIDENCE_NOT_VERIFIED")

    def test_supported_is_not_sufficient_for_assurance_eligibility(self):
        result = assurance_causality_map(
            [{"id": "I1"}], {"I1": ["e1"]}, {"e1": "SUPPORTED"})
        self.assertEqual(result["invariants"][0]["status"], "UNRESOLVED")

    def test_missing_dependencies_do_not_get_vacuous_eligibility(self):
        result = assurance_causality_map([{"id": "I1"}], {}, {})
        self.assertEqual(result["invariants"][0]["status"], "UNRESOLVED")
        self.assertEqual(result["invariants"][0]["reason"], "DEPENDENCIES_NOT_DECLARED")


if __name__ == "__main__":
    unittest.main()
