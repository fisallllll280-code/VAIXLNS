"""ARC-X Reality Sovereignty Kernel.

Deterministic contract and candidate-evaluation layer. This module does not
establish external truth, authenticate signatures, grant authority, or execute
transitions. Any result is conditional on the evidence and trust inputs supplied.
"""
from datetime import datetime, timezone
import hashlib
import json
import re

REALITY_SCHEMA = "arcx-reality-object/v1"
ONTOLOGY_SCHEMA = "arcx-ontology-contract/v1"
IGNORANCE_SCHEMA = "arcx-proof-of-ignorance/v1"
TRANSITION_SCHEMA = "arcx-reality-transition/v1"
AUDIT_SCHEMA = "arcx-audit-chain/v1"

REALITY_LAYERS = {
    "EXTERNAL_REALITY",
    "OBSERVED_STATE",
    "BELIEVED_STATE",
    "AUTHORIZED_STATE",
    "EXECUTED_STATE",
}
EVIDENCE_ROLES = {"SUPPORTS", "CONTRADICTS"}
PATH_OUTCOMES = {
    "EXHAUSTED_NO_RESULT",
    "RESULT_FOUND",
    "BLOCKED",
    "FAILED",
    "NOT_RUN",
}
CONSTITUTIONAL_TERMS = {"USER", "FILE", "DELETE", "AUTHORIZE", "VERIFY", "SAFE", "ARCHIVE"}
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_SENSITIVE_KEYS = {
    "password", "passwd", "private_key", "secret_value", "credential_value",
    "access_token", "refresh_token", "api_key", "client_secret",
}


def stable_digest(value):
    """Return a SHA-256 digest over canonical JSON, prefixed for type clarity."""
    raw = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _digest(value):
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _utc(value):
    if not _text(value) or not value.endswith("Z"):
        return None
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed


def _valid_time_scope(scope):
    if not isinstance(scope, dict):
        return False
    start = _utc(scope.get("start_utc"))
    end = _utc(scope.get("end_utc"))
    return start is not None and end is not None and start <= end


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _contains_sensitive_key(value):
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9_]", "_", str(key).lower())
            if normalized in _SENSITIVE_KEYS or any(
                marker in normalized
                for marker in ("password", "private_key", "secret_value", "credential_value", "api_key")
            ):
                return True
            if _contains_sensitive_key(child):
                return True
    elif isinstance(value, list):
        return any(_contains_sensitive_key(item) for item in value)
    return False


def ontology_contract_digest(contract):
    if not isinstance(contract, dict):
        return None
    payload = {key: value for key, value in contract.items() if key != "contract_digest"}
    return stable_digest(payload)


def validate_ontology_contract(contract):
    errors = []
    if not isinstance(contract, dict):
        return {"valid": False, "errors": ["ONTOLOGY_NOT_OBJECT"], "computed_digest": None}
    if contract.get("schema_version") != ONTOLOGY_SCHEMA:
        errors.append("ONTOLOGY_SCHEMA_UNSUPPORTED")
    for field in ("ontology_id", "version", "authority_ref"):
        if not _text(contract.get(field)):
            errors.append(field.upper() + "_REQUIRED")
    definitions = contract.get("definitions")
    if not isinstance(definitions, dict) or not definitions:
        errors.append("DEFINITIONS_REQUIRED")
        definitions = {}
    for term, definition in definitions.items():
        if not _text(term) or not _text(definition):
            errors.append("DEFINITION_ENTRY_INVALID")
            break
    immutable = contract.get("immutable_concepts", [])
    if not isinstance(immutable, list) or any(not _text(item) for item in immutable):
        errors.append("IMMUTABLE_CONCEPTS_INVALID")
        immutable = []
    elif len(immutable) != len(set(immutable)):
        errors.append("IMMUTABLE_CONCEPTS_DUPLICATED")
    elif not set(immutable).issubset(set(definitions)):
        errors.append("IMMUTABLE_CONCEPT_NOT_DEFINED")
    parent = contract.get("parent_digest")
    genesis_ref = contract.get("genesis_authority_ref")
    if parent is not None and not _digest(parent):
        errors.append("PARENT_DIGEST_INVALID")
    if parent is None and not _text(genesis_ref):
        errors.append("GENESIS_AUTHORITY_REQUIRED")
    if parent is not None and _text(genesis_ref):
        errors.append("PARENT_AND_GENESIS_ARE_MUTUALLY_EXCLUSIVE")
    computed = ontology_contract_digest(contract)
    declared = contract.get("contract_digest")
    if declared is not None and (not _digest(declared) or declared != computed):
        errors.append("ONTOLOGY_DIGEST_MISMATCH")
    return {
        "valid": not errors,
        "errors": sorted(set(errors)),
        "computed_digest": computed,
    }


def assess_ontology_transition(previous, proposed, approval_bundle=None):
    """Assess a candidate ontology change; this function never approves or writes it."""
    old_check = validate_ontology_contract(previous)
    new_check = validate_ontology_contract(proposed)
    if not old_check["valid"] or not new_check["valid"]:
        return {
            "state": "REJECTED_INVALID_CONTRACT",
            "errors": sorted(set(old_check["errors"] + new_check["errors"])),
            "authority_granted": False,
            "canonical_write_performed": False,
        }

    old_defs = previous["definitions"]
    new_defs = proposed["definitions"]
    guarded = set(previous.get("immutable_concepts", []))
    guarded.update(proposed.get("immutable_concepts", []))
    guarded.update(term for term in CONSTITUTIONAL_TERMS if term in old_defs or term in new_defs)
    changed = sorted(term for term in guarded if old_defs.get(term) != new_defs.get(term))
    result = {
        "candidate_digest": new_check["computed_digest"],
        "changed_constitutional_terms": changed,
        "authority_granted": False,
        "canonical_write_performed": False,
    }
    if not changed:
        result.update({
            "state": "ELIGIBLE_FOR_INDEPENDENT_REVIEW",
            "blockers": ["INDEPENDENT_VERIFICATION_REQUIRED", "CANONICAL_AUTHORITY_REVIEW_REQUIRED"],
        })
        return result

    bundle = approval_bundle if isinstance(approval_bundle, dict) else {}
    approvals = bundle.get("approvals", [])
    if bundle.get("target_contract_digest") != new_check["computed_digest"] or not isinstance(approvals, list):
        result.update({
            "state": "REQUIRES_CONSTITUTIONAL_APPROVAL",
            "blockers": ["APPROVAL_BUNDLE_MISSING_OR_WRONG_TARGET"],
        })
        return result

    principals = set()
    domains = set()
    approval_errors = []
    for approval in approvals:
        if not isinstance(approval, dict):
            approval_errors.append("APPROVAL_ENTRY_INVALID")
            continue
        principal = approval.get("approver_id")
        domain = approval.get("authority_domain")
        if not _text(principal) or not _text(domain) or approval.get("scope") != "ONTOLOGY_CONSTITUTIONAL_CHANGE":
            approval_errors.append("APPROVAL_SCOPE_OR_ID_INVALID")
            continue
        if not _digest(approval.get("receipt_digest")):
            approval_errors.append("APPROVAL_RECEIPT_DIGEST_INVALID")
        principals.add(principal)
        domains.add(domain)
    if approval_errors or len(principals) < 2 or len(domains) < 2:
        result.update({
            "state": "REQUIRES_CONSTITUTIONAL_APPROVAL",
            "blockers": sorted(set(approval_errors + ["TWO_INDEPENDENT_AUTHORITY_DOMAINS_REQUIRED"])),
        })
    else:
        result.update({
            "state": "CANDIDATE_FOR_EXTERNAL_AUTHORITY_VERIFICATION",
            "blockers": [
                "APPROVAL_RECEIPTS_NOT_CRYPTOGRAPHICALLY_VERIFIED_HERE",
                "CANONICAL_AUTHORITY_REVIEW_REQUIRED",
            ],
        })
    return result


def validate_reality_object(item):
    errors = []
    if not isinstance(item, dict):
        return {"valid": False, "errors": ["REALITY_OBJECT_NOT_OBJECT"]}
    if item.get("schema_version") != REALITY_SCHEMA:
        errors.append("REALITY_SCHEMA_UNSUPPORTED")
    for field in ("object_id", "ontology_id", "ontology_version", "observation_scope"):
        if not _text(item.get(field)):
            errors.append(field.upper() + "_REQUIRED")
    if item.get("layer") not in REALITY_LAYERS:
        errors.append("REALITY_LAYER_INVALID")
    proposition = item.get("proposition")
    if not isinstance(proposition, dict) or any(
        not _text(proposition.get(key)) for key in ("subject", "predicate")
    ) or "object" not in proposition:
        errors.append("PROPOSITION_INVALID")
    if not _valid_time_scope(item.get("temporal_scope")):
        errors.append("TEMPORAL_SCOPE_INVALID")
    if not _digest(item.get("ontology_digest")):
        errors.append("ONTOLOGY_DIGEST_INVALID")
    evidence = item.get("evidence", [])
    if not isinstance(evidence, list):
        errors.append("EVIDENCE_LIST_INVALID")
        evidence = []
    seen = set()
    for index, envelope in enumerate(evidence):
        if not isinstance(envelope, dict):
            errors.append(f"EVIDENCE_{index}_INVALID")
            continue
        for field in ("evidence_id", "source_id", "independence_group"):
            if not _text(envelope.get(field)):
                errors.append(f"EVIDENCE_{index}_{field.upper()}_REQUIRED")
        if envelope.get("role") not in EVIDENCE_ROLES:
            errors.append(f"EVIDENCE_{index}_ROLE_INVALID")
        if not _digest(envelope.get("source_digest")):
            errors.append(f"EVIDENCE_{index}_SOURCE_DIGEST_INVALID")
        if not _utc(envelope.get("observed_at_utc")):
            errors.append(f"EVIDENCE_{index}_OBSERVED_AT_INVALID")
        evidence_id = envelope.get("evidence_id")
        if _text(evidence_id) and evidence_id in seen:
            errors.append("EVIDENCE_ID_DUPLICATED")
        if _text(evidence_id):
            seen.add(evidence_id)
    receipt = item.get("verification_receipt")
    if receipt is not None:
        if not isinstance(receipt, dict) or not _text(receipt.get("verifier_id")) or not _digest(receipt.get("receipt_digest")):
            errors.append("VERIFICATION_RECEIPT_REFERENCE_INVALID")
    return {"valid": not errors, "errors": sorted(set(errors))}


def assess_reality_object(item, as_of_utc=None):
    """Classify supplied evidence without claiming truth or authenticating receipts."""
    check = validate_reality_object(item)
    if not check["valid"]:
        return {
            "state": "INVALID",
            "errors": check["errors"],
            "object_id": item.get("object_id") if isinstance(item, dict) else None,
            "verification_performed": False,
        }
    if as_of_utc is not None:
        as_of = _utc(as_of_utc)
        freshness = item.get("fresh_until_utc")
        if as_of is None or (freshness is not None and _utc(freshness) is None):
            return {
                "state": "INVALID",
                "errors": ["AS_OF_OR_FRESHNESS_TIMESTAMP_INVALID"],
                "object_id": item["object_id"],
                "verification_performed": False,
            }
        if freshness is not None and as_of > _utc(freshness):
            return {
                "state": "STALE",
                "errors": [],
                "object_id": item["object_id"],
                "evidence_count": len(item.get("evidence", [])),
                "verification_performed": False,
            }
    roles = {entry["role"] for entry in item.get("evidence", [])}
    if roles == {"SUPPORTS", "CONTRADICTS"}:
        state = "CONFLICTING_EVIDENCE"
    elif "CONTRADICTS" in roles:
        state = "CONTRADICTED"
    elif "SUPPORTS" in roles:
        state = "SUPPORTED"
    else:
        state = "UNKNOWN"
    return {
        "state": state,
        "errors": [],
        "object_id": item["object_id"],
        "evidence_count": len(item.get("evidence", [])),
        "independence_groups": sorted({e["independence_group"] for e in item.get("evidence", [])}),
        "verification_performed": False,
        "notes": ["SUPPORTED_IS_NOT_VERIFIED", "INPUT_RECEIPT_REFERENCES_ARE_NOT_AUTHENTICATED_HERE"],
    }


def find_contradictions(objects):
    """Find scoped candidate conflicts without silently resolving either claim."""
    if not isinstance(objects, list):
        return {"state": "INVALID_INPUT", "contradictions": [], "invalid_object_ids": []}
    valid = []
    invalid_ids = []
    for item in objects:
        check = validate_reality_object(item)
        if check["valid"]:
            valid.append(item)
        else:
            invalid_ids.append(item.get("object_id") if isinstance(item, dict) else None)
    candidates = []
    ordered = sorted(valid, key=lambda obj: obj["object_id"])
    for index, left in enumerate(ordered):
        for right in ordered[index + 1:]:
            lp = left["proposition"]
            rp = right["proposition"]
            if lp["subject"] != rp["subject"] or lp["predicate"] != rp["predicate"]:
                continue
            if left["layer"] != right["layer"]:
                continue
            if left["ontology_digest"] != right["ontology_digest"]:
                continue
            if left["observation_scope"] != right["observation_scope"]:
                continue
            if left["temporal_scope"] != right["temporal_scope"]:
                continue
            if _canonical(lp["object"]) == _canonical(rp["object"]):
                continue
            pair = sorted([left["object_id"], right["object_id"]])
            candidates.append({
                "contradiction_id": "contra:" + stable_digest(pair).split(":", 1)[1],
                "claim_ids": pair,
                "scope": left["observation_scope"],
                "temporal_scope": left["temporal_scope"],
                "state": "UNRESOLVED_CANDIDATE",
                "resolution": None,
                "notes": ["CLAIMS_PRESERVED", "SEMANTIC_EQUIVALENCE_REQUIRES_DOMAIN_REVIEW"],
            })
    candidates.sort(key=lambda c: c["contradiction_id"])
    return {
        "state": "CANDIDATES_FOUND" if candidates else "NO_SCOPED_CANDIDATES_FOUND",
        "contradictions": candidates,
        "invalid_object_ids": invalid_ids,
        "resolution_performed": False,
    }


def verification_universe_digest(scope, path_ids):
    """Compute the declared bounded universe commitment used by ignorance proofs."""
    if not _text(scope) or not isinstance(path_ids, list) or not path_ids:
        raise ValueError("scope and a non-empty path_ids list are required")
    if any(not _text(path_id) for path_id in path_ids) or len(path_ids) != len(set(path_ids)):
        raise ValueError("path_ids must be non-empty unique strings")
    return stable_digest({"scope": scope, "path_ids": sorted(path_ids)})


def evaluate_proof_of_ignorance(universe):
    """Return a bounded-scope result only when every declared path is exhausted."""
    if not isinstance(universe, dict) or universe.get("schema_version") != IGNORANCE_SCHEMA:
        return {"state": "INVALID", "errors": ["IGNORANCE_SCHEMA_INVALID"], "proof_performed": False}
    scope = universe.get("scope")
    paths = universe.get("path_ids")
    observations = universe.get("observations")
    errors = []
    if not _text(scope):
        errors.append("SCOPE_REQUIRED")
    paths_valid = isinstance(paths, list) and bool(paths) and all(_text(p) for p in paths)
    if not paths_valid:
        errors.append("PATH_UNIVERSE_REQUIRED")
        paths = []
    if paths and len(paths) != len(set(paths)):
        errors.append("PATH_IDS_DUPLICATED")
    if not isinstance(observations, list):
        errors.append("OBSERVATIONS_INVALID")
        observations = []
    if paths and _text(scope) and len(paths) == len(set(paths)):
        if universe.get("universe_digest") != verification_universe_digest(scope, paths):
            errors.append("UNIVERSE_DIGEST_MISMATCH")
    else:
        errors.append("UNIVERSE_DIGEST_MISMATCH")
    if not _text(universe.get("closure_authority_ref")):
        errors.append("CLOSURE_AUTHORITY_REFERENCE_REQUIRED")
    if universe.get("closed_world") is not True:
        errors.append("UNIVERSE_NOT_DECLARED_CLOSED")
    if errors:
        return {"state": "INCOMPLETE", "errors": sorted(set(errors)), "proof_performed": False}

    by_path = {}
    for observation in observations:
        if not isinstance(observation, dict) or not _text(observation.get("path_id")):
            errors.append("OBSERVATION_INVALID")
            continue
        path_id = observation["path_id"]
        if path_id in by_path:
            errors.append("OBSERVATION_PATH_DUPLICATED")
        by_path[path_id] = observation
    expected = set(paths)
    actual = set(by_path)
    if actual != expected:
        errors.append("OBSERVATION_COVERAGE_MISMATCH")
    for path_id, observation in by_path.items():
        if observation.get("outcome") not in PATH_OUTCOMES:
            errors.append("OBSERVATION_OUTCOME_INVALID:" + path_id)
        if observation.get("checked_scope") != scope:
            errors.append("OBSERVATION_SCOPE_MISMATCH:" + path_id)
        if not _digest(observation.get("receipt_digest")):
            errors.append("OBSERVATION_RECEIPT_DIGEST_INVALID:" + path_id)
    if errors:
        return {"state": "INCOMPLETE", "errors": sorted(set(errors)), "proof_performed": False}
    outcomes = {entry["outcome"] for entry in by_path.values()}
    if "RESULT_FOUND" in outcomes:
        return {
            "state": "EVIDENCE_FOUND",
            "errors": [],
            "proof_performed": False,
            "scope": scope,
            "assumptions": ["A_RESULT_FOUND_WITHIN_THE_DECLARED_UNIVERSE"],
        }
    if outcomes != {"EXHAUSTED_NO_RESULT"}:
        return {
            "state": "INCOMPLETE",
            "errors": ["NOT_ALL_VERIFICATION_PATHS_EXHAUSTED_WITH_NO_RESULT"],
            "proof_performed": False,
        }
    return {
        "state": "PROVABLY_UNKNOWN_WITHIN_SCOPE",
        "errors": [],
        "proof_performed": True,
        "scope": scope,
        "universe_digest": universe["universe_digest"],
        "assumptions": [
            "THE_DECLARED_PATH_UNIVERSE_IS_EXHAUSTIVE_FOR_THIS_SCOPE",
            "COMPLETION_RECEIPT_DIGESTS_AND_CLOSURE_AUTHORITY_ARE_TRUSTED_INPUTS",
            "NO_CLAIM_IS_MADE_OUTSIDE_THE_DECLARED_SCOPE",
        ],
        "external_receipts_cryptographically_verified": False,
    }


def evaluate_transition_candidate(transition):
    """Check completeness of a proposed state transition; never authorize or execute."""
    required = (
        "transition_id", "intent_digest", "before_state_digest",
        "predicted_after_state_digest", "simulation_receipt_digest",
        "test_receipt_digest", "rollback_plan_ref", "authority_ticket_ref",
    )
    errors = []
    if not isinstance(transition, dict) or transition.get("schema_version") != TRANSITION_SCHEMA:
        return {
            "state": "BLOCKED",
            "errors": ["TRANSITION_SCHEMA_INVALID"],
            "authority_granted": False,
            "execution_performed": False,
            "canonical_write_performed": False,
        }
    for field in required:
        value = transition.get(field)
        if field.endswith("_digest"):
            if not _digest(value):
                errors.append(field.upper() + "_INVALID")
        elif not _text(value):
            errors.append(field.upper() + "_REQUIRED")
    invariants = transition.get("invariant_checks")
    if not isinstance(invariants, list) or not invariants:
        errors.append("INVARIANT_CHECKS_REQUIRED")
        invariants = []
    for index, invariant in enumerate(invariants):
        if not isinstance(invariant, dict) or not _text(invariant.get("invariant_id")):
            errors.append(f"INVARIANT_{index}_INVALID")
            continue
        if invariant.get("result") != "PASS":
            errors.append(f"INVARIANT_{index}_NOT_PASSED")
        if not _digest(invariant.get("evidence_digest")):
            errors.append(f"INVARIANT_{index}_EVIDENCE_DIGEST_INVALID")
    if errors:
        state = "BLOCKED"
    else:
        state = "ELIGIBLE_FOR_SEPARATE_AUTHORITY_CHECK"
    return {
        "state": state,
        "errors": sorted(set(errors)),
        "transition_digest": stable_digest(transition),
        "authority_granted": False,
        "execution_performed": False,
        "canonical_write_performed": False,
        "notes": [
            "RECEIPT_DIGESTS_ARE_REFERENCES_NOT_AUTHENTICATED_PROOFS",
            "AUTHORITY_TICKET_REFERENCE_IS_NOT_AUTHORIZATION",
            "VX_EXECUTION_REQUIRES_A_SEPARATE_ENFORCED_GATE",
        ],
    }


def reconcile_transition_outcome(report):
    """Compare an execution report with an observed postcondition without conflating them."""
    if not isinstance(report, dict) or report.get("schema_version") != TRANSITION_SCHEMA:
        return {
            "state": "INVALID",
            "errors": ["TRANSITION_SCHEMA_INVALID"],
            "execution_receipt_authenticated": False,
            "observation_receipt_authenticated": False,
        }
    required = ("transition_id", "observation_scope")
    errors = []
    for field in required:
        if not _text(report.get(field)):
            errors.append(field.upper() + "_REQUIRED")
    if not _digest(report.get("expected_postcondition_digest")):
        errors.append("EXPECTED_POSTCONDITION_DIGEST_INVALID")
    if not _valid_time_scope(report.get("temporal_scope")):
        errors.append("TEMPORAL_SCOPE_INVALID")

    execution_receipt = report.get("execution_receipt_digest")
    observed_digest = report.get("observed_postcondition_digest")
    observation_receipt = report.get("observation_receipt_digest")
    if execution_receipt is not None and not _digest(execution_receipt):
        errors.append("EXECUTION_RECEIPT_DIGEST_INVALID")
    if observed_digest is not None and not _digest(observed_digest):
        errors.append("OBSERVED_POSTCONDITION_DIGEST_INVALID")
    if observation_receipt is not None and not _digest(observation_receipt):
        errors.append("OBSERVATION_RECEIPT_DIGEST_INVALID")
    if errors:
        return {
            "state": "INVALID",
            "errors": sorted(set(errors)),
            "execution_receipt_authenticated": False,
            "observation_receipt_authenticated": False,
        }

    base = {
        "transition_id": report["transition_id"],
        "scope": report["observation_scope"],
        "temporal_scope": report["temporal_scope"],
        "execution_receipt_present": _digest(execution_receipt),
        "observation_receipt_present": _digest(observation_receipt),
        "execution_receipt_authenticated": False,
        "observation_receipt_authenticated": False,
        "canonical_write_performed": False,
    }
    if execution_receipt is None:
        base.update({
            "state": "EXECUTION_NOT_EVIDENCED",
            "reconciled": False,
            "notes": ["ABSENCE_OF_A_RECEIPT_DOES_NOT_PROVE_THAT_NO_EXTERNAL_ACTION_OCCURRED"],
        })
        return base
    if observed_digest is None or observation_receipt is None:
        base.update({
            "state": "EXECUTION_REPORTED_OUTCOME_UNKNOWN",
            "reconciled": False,
            "notes": ["EXECUTION_REPORT_IS_NOT_A_POSTCONDITION_OBSERVATION"],
        })
        return base
    if observed_digest != report["expected_postcondition_digest"]:
        base.update({
            "state": "POSTCONDITION_MISMATCH",
            "reconciled": False,
            "expected_postcondition_digest": report["expected_postcondition_digest"],
            "observed_postcondition_digest": observed_digest,
            "notes": ["DO_NOT_REWRITE_EXPECTED_STATE_AS_OBSERVED_STATE"],
        })
        return base
    base.update({
        "state": "POSTCONDITION_MATCH_CANDIDATE",
        "reconciled": True,
        "expected_postcondition_digest": report["expected_postcondition_digest"],
        "observed_postcondition_digest": observed_digest,
        "notes": [
            "MATCH_IS_CONDITIONAL_ON_RECEIPT_AUTHENTICITY_AND_SCOPE_BINDING",
            "INDEPENDENT_RECEIPT_VERIFICATION_REQUIRED",
        ],
    })
    return base


def build_provenance_graph(objects):
    """Build a deterministic claim-evidence-source graph and report correlation signals."""
    if not isinstance(objects, list):
        return {"state": "INVALID_INPUT", "nodes": [], "edges": [], "graph_digest": None}
    nodes = {}
    edges = set()
    invalid_ids = []
    identity_conflicts = []
    group_claims = {}
    evidence_fingerprints = {}

    for item in objects:
        check = validate_reality_object(item)
        if not check["valid"]:
            invalid_ids.append(item.get("object_id") if isinstance(item, dict) else None)
            continue
        claim_id = item["object_id"]
        claim_node_id = "claim:" + claim_id
        claim_node = {
            "node_id": claim_node_id,
            "node_type": "CLAIM",
            "layer": item["layer"],
            "ontology_digest": item["ontology_digest"],
            "scope": item["observation_scope"],
            "temporal_scope": item["temporal_scope"],
            "proposition_digest": stable_digest(item["proposition"]),
        }
        nodes[claim_node_id] = claim_node
        for envelope in item.get("evidence", []):
            evidence_id = envelope["evidence_id"]
            evidence_node_id = "evidence:" + evidence_id
            source_node_id = "source:" + envelope["source_id"]
            evidence_node = {
                "node_id": evidence_node_id,
                "node_type": "EVIDENCE",
                "source_id": envelope["source_id"],
                "source_digest": envelope["source_digest"],
                "independence_group": envelope["independence_group"],
            }
            fingerprint = stable_digest(evidence_node)
            if evidence_id in evidence_fingerprints and evidence_fingerprints[evidence_id] != fingerprint:
                identity_conflicts.append(evidence_id)
            evidence_fingerprints[evidence_id] = fingerprint
            nodes.setdefault(evidence_node_id, evidence_node)
            nodes.setdefault(source_node_id, {
                "node_id": source_node_id,
                "node_type": "SOURCE",
                "source_id": envelope["source_id"],
            })
            edges.add((source_node_id, evidence_node_id, "PROVENANCE_OF"))
            edges.add((evidence_node_id, claim_node_id, envelope["role"]))
            group_claims.setdefault(envelope["independence_group"], set()).add(claim_id)

    edge_rows = [
        {"from": source, "to": target, "relation": relation}
        for source, target, relation in sorted(edges)
    ]
    correlation_signals = [
        {"independence_group": group, "claim_ids": sorted(claim_ids), "signal": "SHARED_DECLARED_DEPENDENCY"}
        for group, claim_ids in sorted(group_claims.items())
        if len(claim_ids) > 1
    ]
    node_rows = sorted(nodes.values(), key=lambda node: node["node_id"])
    graph_payload = {"nodes": node_rows, "edges": edge_rows}
    return {
        "state": "PARTIAL" if invalid_ids or identity_conflicts else "BUILT",
        "nodes": node_rows,
        "edges": edge_rows,
        "invalid_object_ids": invalid_ids,
        "evidence_identity_conflicts": sorted(set(identity_conflicts)),
        "correlation_signals": correlation_signals,
        "independence_proved": False,
        "graph_digest": stable_digest(graph_payload),
        "notes": [
            "SOURCE_AND_INDEPENDENCE_LABELS_ARE_INPUT_ASSERTIONS",
            "CORRELATION_SIGNAL_IS_NOT_PROOF_OF_CAUSAL_DEPENDENCE",
        ],
    }


def build_audit_chain(events):
    """Build a tamper-evident hash-linked chain; it is not signed or immutable storage."""
    if not isinstance(events, list):
        return {"valid": False, "errors": ["EVENTS_MUST_BE_A_LIST"], "chain": []}
    if any(not isinstance(event, dict) for event in events):
        return {"valid": False, "errors": ["EVENT_MUST_BE_OBJECT"], "chain": []}
    if any(_contains_sensitive_key(event) for event in events):
        return {"valid": False, "errors": ["SENSITIVE_VALUE_FIELD_FORBIDDEN"], "chain": []}
    chain = []
    previous = "GENESIS"
    for sequence, event in enumerate(events):
        entry = {
            "schema_version": AUDIT_SCHEMA,
            "sequence": sequence,
            "previous_digest": previous,
            "event": event,
        }
        entry["event_digest"] = stable_digest(entry)
        chain.append(entry)
        previous = entry["event_digest"]
    return {
        "valid": True,
        "errors": [],
        "chain": chain,
        "chain_digest": previous,
        "signature_verified": False,
        "immutable_storage_confirmed": False,
    }


def verify_audit_chain(chain):
    if not isinstance(chain, list):
        return {"valid": False, "errors": ["CHAIN_MUST_BE_A_LIST"], "verified_entries": 0}
    errors = []
    previous = "GENESIS"
    for expected_sequence, entry in enumerate(chain):
        if not isinstance(entry, dict):
            errors.append("ENTRY_INVALID")
            break
        if entry.get("schema_version") != AUDIT_SCHEMA:
            errors.append("SCHEMA_VERSION_INVALID")
        if entry.get("sequence") != expected_sequence:
            errors.append("SEQUENCE_INVALID")
        if entry.get("previous_digest") != previous:
            errors.append("PREVIOUS_DIGEST_MISMATCH")
        event = entry.get("event")
        if not isinstance(event, dict) or _contains_sensitive_key(event):
            errors.append("EVENT_INVALID_OR_SENSITIVE")
        declared = entry.get("event_digest")
        payload = {key: value for key, value in entry.items() if key != "event_digest"}
        if not _digest(declared) or declared != stable_digest(payload):
            errors.append("EVENT_DIGEST_MISMATCH")
        previous = declared if _digest(declared) else "INVALID"
    return {
        "valid": not errors,
        "errors": sorted(set(errors)),
        "verified_entries": len(chain) if not errors else 0,
        "signature_verified": False,
        "immutable_storage_confirmed": False,
    }
