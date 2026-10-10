import copy
import unittest

from scripts.arcx_reality_sovereignty import (
    IGNORANCE_SCHEMA,
    ONTOLOGY_SCHEMA,
    REALITY_SCHEMA,
    TRANSITION_SCHEMA,
    assess_ontology_transition,
    assess_reality_object,
    build_audit_chain,
    evaluate_proof_of_ignorance,
    evaluate_transition_candidate,
    find_contradictions,
    stable_digest,
    validate_ontology_contract,
    validate_reality_object,
    verification_universe_digest,
    verify_audit_chain,
)


def ontology(definitions=None, parent=None):
    payload = {
        "schema_version": ONTOLOGY_SCHEMA,
        "ontology_id": "vlns-core",
        "version": "1.0.0" if parent is None else "1.0.1",
        "authority_ref": "authority://canonical-root",
        "definitions": definitions or {
            "FILE": "A versioned digital object.",
            "ARCHIVE": "A reversible preservation operation.",
            "DELETE": "An authorized destructive removal operation.",
            "SAFE": "A policy-constrained state with explicit proof obligations.",
        },
        "immutable_concepts": ["FILE", "ARCHIVE", "DELETE", "SAFE"],
        "parent_digest": parent,
    }
    if parent is None:
        payload["genesis_authority_ref"] = "genesis://omega0"
    return payload


def evidence(evidence_id="ev-1", role="SUPPORTS", group="source-a"):
    return {
        "evidence_id": evidence_id,
        "role": role,
        "source_id": "source://" + evidence_id,
        "source_digest": "sha256:" + "a" * 64,
        "independence_group": group,
        "observed_at_utc": "2026-10-10T10:00:00Z",
    }


def reality(object_id="claim-1", value="present", evidence_items=None, scope="repo@commit-1"):
    contract = ontology()
    return {
        "schema_version": REALITY_SCHEMA,
        "object_id": object_id,
        "ontology_id": contract["ontology_id"],
        "ontology_version": contract["version"],
        "ontology_digest": stable_digest(contract),
        "layer": "OBSERVED_STATE",
        "proposition": {"subject": "file:/README.md", "predicate": "exists", "object": value},
        "temporal_scope": {
            "start_utc": "2026-10-10T00:00:00Z",
            "end_utc": "2026-10-11T00:00:00Z",
        },
        "observation_scope": scope,
        "evidence": [] if evidence_items is None else evidence_items,
    }


def universe(outcomes=None):
    paths = ["repo-search", "registry-query"]
    scope = "repository=VAIXLNS;revision=commit-1"
    results = outcomes or {
        "repo-search": "EXHAUSTED_NO_RESULT",
        "registry-query": "EXHAUSTED_NO_RESULT",
    }
    return {
        "schema_version": IGNORANCE_SCHEMA,
        "scope": scope,
        "path_ids": paths,
        "universe_digest": verification_universe_digest(scope, paths),
        "closed_world": True,
        "closure_authority_ref": "authority://bounded-search-policy-v1",
        "observations": [
            {
                "path_id": path,
                "outcome": outcome,
                "checked_scope": scope,
                "receipt_digest": "sha256:" + ("b" if path == "repo-search" else "c") * 64,
            }
            for path, outcome in results.items()
        ],
    }


def transition():
    return {
        "schema_version": TRANSITION_SCHEMA,
        "transition_id": "transition-001",
        "intent_digest": "sha256:" + "1" * 64,
        "before_state_digest": "sha256:" + "2" * 64,
        "predicted_after_state_digest": "sha256:" + "3" * 64,
        "simulation_receipt_digest": "sha256:" + "4" * 64,
        "test_receipt_digest": "sha256:" + "5" * 64,
        "rollback_plan_ref": "rollback://plan-1",
        "authority_ticket_ref": "ticket://candidate-1",
        "invariant_checks": [{
            "invariant_id": "no-privilege-escalation",
            "result": "PASS",
            "evidence_digest": "sha256:" + "6" * 64,
        }],
    }


class RealitySovereigntyTests(unittest.TestCase):
    def test_valid_ontology_has_deterministic_digest(self):
        contract = ontology()
        self.assertTrue(validate_ontology_contract(contract)["valid"])
        self.assertEqual(
            validate_ontology_contract(contract)["computed_digest"],
            validate_ontology_contract(copy.deepcopy(contract))["computed_digest"],
        )

    def test_ontology_declared_digest_mismatch_fails_closed(self):
        contract = ontology()
        contract["contract_digest"] = "sha256:" + "f" * 64
        self.assertIn("ONTOLOGY_DIGEST_MISMATCH", validate_ontology_contract(contract)["errors"])

    def test_archive_cannot_be_redefined_without_constitutional_gate(self):
        old = ontology()
        new_defs = dict(old["definitions"])
        new_defs["ARCHIVE"] = "A permanent destructive removal operation."
        proposed = ontology(new_defs, parent=stable_digest(old))
        result = assess_ontology_transition(old, proposed)
        self.assertEqual(result["state"], "REQUIRES_CONSTITUTIONAL_APPROVAL")
        self.assertFalse(result["canonical_write_performed"])

    def test_constitutional_change_requires_two_independent_domains(self):
        old = ontology()
        new_defs = dict(old["definitions"])
        new_defs["DELETE"] = "A destructive operation with separate authority."
        proposed = ontology(new_defs, parent=stable_digest(old))
        digest = validate_ontology_contract(proposed)["computed_digest"]
        approval = {
            "target_contract_digest": digest,
            "approvals": [
                {"approver_id": "alice", "authority_domain": "engineering", "scope": "ONTOLOGY_CONSTITUTIONAL_CHANGE", "receipt_digest": "sha256:" + "a" * 64},
                {"approver_id": "bob", "authority_domain": "security", "scope": "ONTOLOGY_CONSTITUTIONAL_CHANGE", "receipt_digest": "sha256:" + "b" * 64},
            ],
        }
        result = assess_ontology_transition(old, proposed, approval)
        self.assertEqual(result["state"], "CANDIDATE_FOR_EXTERNAL_AUTHORITY_VERIFICATION")
        self.assertFalse(result["authority_granted"])

    def test_reality_object_validates(self):
        self.assertTrue(validate_reality_object(reality(evidence_items=[evidence()]))["valid"])

    def test_supported_is_not_verified(self):
        result = assess_reality_object(reality(evidence_items=[evidence()]))
        self.assertEqual(result["state"], "SUPPORTED")
        self.assertFalse(result["verification_performed"])

    def test_no_evidence_is_unknown_not_absent(self):
        result = assess_reality_object(reality(evidence_items=[]))
        self.assertEqual(result["state"], "UNKNOWN")

    def test_conflicting_evidence_is_preserved(self):
        result = assess_reality_object(reality(evidence_items=[
            evidence("ev-yes", "SUPPORTS", "source-a"),
            evidence("ev-no", "CONTRADICTS", "source-b"),
        ]))
        self.assertEqual(result["state"], "CONFLICTING_EVIDENCE")

    def test_stale_evidence_scope_is_explicit(self):
        item = reality(evidence_items=[evidence()])
        item["fresh_until_utc"] = "2026-10-10T10:30:00Z"
        result = assess_reality_object(item, as_of_utc="2026-10-10T11:00:00Z")
        self.assertEqual(result["state"], "STALE")

    def test_bad_ontology_digest_invalidates_claim(self):
        item = reality(evidence_items=[evidence()])
        item["ontology_digest"] = "sha256:bad"
        self.assertEqual(assess_reality_object(item)["state"], "INVALID")

    def test_contradictions_require_identical_observation_and_temporal_scope(self):
        first = reality("claim-a", "present", [evidence("a")], "same-snapshot")
        second = reality("claim-b", "absent", [evidence("b", "SUPPORTS", "source-b")], "same-snapshot")
        found = find_contradictions([first, second])
        self.assertEqual(found["state"], "CANDIDATES_FOUND")
        self.assertEqual(found["contradictions"][0]["resolution"], None)
        second["observation_scope"] = "different-snapshot"
        self.assertEqual(find_contradictions([first, second])["state"], "NO_SCOPED_CANDIDATES_FOUND")

    def test_bounded_ignorance_requires_complete_declared_universe(self):
        result = evaluate_proof_of_ignorance(universe())
        self.assertEqual(result["state"], "PROVABLY_UNKNOWN_WITHIN_SCOPE")
        self.assertFalse(result["external_receipts_cryptographically_verified"])

    def test_ignorance_universe_missing_path_cannot_prove_absence(self):
        item = universe()
        item["observations"] = item["observations"][:1]
        result = evaluate_proof_of_ignorance(item)
        self.assertEqual(result["state"], "INCOMPLETE")

    def test_blocked_search_path_cannot_prove_unknown(self):
        result = evaluate_proof_of_ignorance(universe({
            "repo-search": "EXHAUSTED_NO_RESULT",
            "registry-query": "BLOCKED",
        }))
        self.assertEqual(result["state"], "INCOMPLETE")

    def test_found_result_defeats_ignorance_claim(self):
        result = evaluate_proof_of_ignorance(universe({
            "repo-search": "RESULT_FOUND",
            "registry-query": "EXHAUSTED_NO_RESULT",
        }))
        self.assertEqual(result["state"], "EVIDENCE_FOUND")

    def test_universe_digest_mismatch_fails_closed(self):
        item = universe()
        item["universe_digest"] = "sha256:" + "f" * 64
        self.assertEqual(evaluate_proof_of_ignorance(item)["state"], "INCOMPLETE")

    def test_transition_candidate_never_executes(self):
        result = evaluate_transition_candidate(transition())
        self.assertEqual(result["state"], "ELIGIBLE_FOR_SEPARATE_AUTHORITY_CHECK")
        self.assertFalse(result["execution_performed"])
        self.assertFalse(result["canonical_write_performed"])

    def test_failed_invariant_blocks_transition(self):
        item = transition()
        item["invariant_checks"][0]["result"] = "UNKNOWN"
        self.assertEqual(evaluate_transition_candidate(item)["state"], "BLOCKED")

    def test_audit_chain_detects_tampering(self):
        chain = build_audit_chain([
            {"event_type": "CLAIM_INGESTED", "claim_id": "claim-1"},
            {"event_type": "EVIDENCE_ATTACHED", "evidence_id": "ev-1"},
        ])
        self.assertTrue(verify_audit_chain(chain["chain"])["valid"])
        tampered = copy.deepcopy(chain["chain"])
        tampered[0]["event"]["claim_id"] = "claim-evil"
        self.assertFalse(verify_audit_chain(tampered)["valid"])

    def test_audit_refuses_secret_value_fields(self):
        result = build_audit_chain([{"event_type": "CREDENTIAL_READ", "api_key": "never-log"}])
        self.assertFalse(result["valid"])
        self.assertEqual(result["chain"], [])

    def test_audit_hash_chain_does_not_claim_signature_or_immutability(self):
        result = build_audit_chain([{"event_type": "START"}])
        self.assertFalse(result["signature_verified"])
        self.assertFalse(result["immutable_storage_confirmed"])


if __name__ == "__main__":
    unittest.main()
