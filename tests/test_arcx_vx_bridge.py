"""Unit tests for the local ARC-X -> VX bridge contract; no network access."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import unittest
from unittest.mock import patch

from scripts.arcx_vx_bridge import (
    BridgeError,
    build_envelope,
    canonical_json,
    sha256_hex,
    validate_task,
    verify_receipt,
    _NoRedirectHandler,
    _configured_endpoint,
)


def sample_task() -> dict:
    return {
        "schema_version": "1.0",
        "task_id": "task-engineering-001",
        "idempotency_key": "idempotency-key-000001",
        "parent_task_id": None,
        "created_at": "2026-10-09T12:00:00Z",
        "deadline": None,
        "source_revision": "a" * 40,
        "input_artifacts": [{
            "artifact_id": "source-001",
            "uri": "https://example.invalid/source",
            "sha256": "b" * 64,
            "media_type": "text/plain",
            "trust_state": "UNTRUSTED",
            "source_revision": "a" * 40,
            "license_ref": "license-record-001",
        }],
        "eir_ref": "eir-001",
        "memory_context": {
            "record_refs": ["memory-record-001"],
            "index_revision": "omega-000@revision-001",
            "retrieval_receipt_ref": "retrieval-receipt-001",
            "coverage_state": "PARTIAL",
            "query_ref": "memory-query-001",
            "uncovered_scopes": ["historical archive not fully enumerated"],
            "rationale": "Relevant records were found; historical coverage remains partial.",
            "context_digest": "e" * 64,
        },
        "language_artifact_refs": ["language-contract-v1"],
        "index_delta_ref": None,
        "system_context_refs": ["ARC-X-OMEGA", "VX"],
        "claim_refs": ["claim-001"],
        "lineage": {
            "parent_record_refs": ["source-001"],
            "previous_decision_ref": None,
            "policy_version": "policy-1",
        },
        "domain": "SOFTWARE_ENGINEERING",
        "operation": "RUN_TESTS",
        "required_capabilities": ["software.test"],
        "input_schema": None,
        "output_schema": None,
        "assumptions": [{"statement": "sandbox is isolated", "status": "DECLARED", "evidence_refs": []}],
        "constraints": [{"constraint_id": "no-egress", "kind": "SECURITY", "expression": "network egress denied", "hard_gate": True}],
        "proof_obligations": [{
            "obligation_id": "test-pass",
            "statement": "required tests pass",
            "acceptance_method": "INTEGRATION_TEST",
            "criticality": "BLOCKING",
            "tolerance": None,
            "evidence_refs": [],
        }],
        "verification_profile": {
            "profile_id": "software-ci-v1",
            "independent_verification_required": True,
            "fail_closed": True,
            "minimum_verifier_diversity": 1,
            "allowed_equivalence": "SEMANTIC_CONTRACT",
        },
        "resource_request": {
            "cpu_cores": 1,
            "memory_mib": 512,
            "accelerator_class": "NONE",
            "accelerator_memory_mib": None,
            "disk_mib": 256,
            "wall_time_seconds": 60,
            "max_attempts": 2,
            "max_cost_microunits": 0,
            "parallelism": 1,
        },
        "security": {
            "classification": "INTERNAL",
            "data_residency": ["local"],
            "network_policy": "DENY",
            "external_side_effects_allowed": False,
            "license_refs": ["license-record-001"],
            "secret_refs": [],
        },
        "reproducibility": {
            "environment_digest": "sha256:" + "c" * 64,
            "dependency_lock_digest": "sha256:" + "d" * 64,
            "seed_policy": "NOT_APPLICABLE",
            "seed": None,
            "determinism_requirement": "SEMANTIC_CONTRACT",
            "solver_version": None,
            "precision": None,
            "unit_system": None,
            "initial_conditions_digest": None,
            "boundary_conditions_digest": None,
        },
        "execution_mode": "TEST",
        "policy_version": "policy-1",
        "authorization_ref": None,
        "status": "DRAFT",
    }


class BridgeValidationTests(unittest.TestCase):
    def test_valid_local_task_passes_preflight(self):
        self.assertEqual(validate_task(sample_task()), [])

    def test_missing_proof_obligations_fail_closed(self):
        task = sample_task()
        task["proof_obligations"] = []
        self.assertIn("PROOF_OBLIGATIONS_REQUIRED", validate_task(task))

    def test_missing_memory_context_is_rejected(self):
        task = sample_task()
        task.pop("memory_context")
        self.assertTrue(any(code.startswith("MISSING_REQUIRED_FIELDS:") and "memory_context" in code
                            for code in validate_task(task)))

    def test_complete_memory_scope_requires_receipt_and_no_hidden_gaps(self):
        task = sample_task()
        task["memory_context"]["coverage_state"] = "COMPLETE_FOR_SCOPE"
        task["memory_context"]["retrieval_receipt_ref"] = None
        task["memory_context"]["uncovered_scopes"] = ["missing old archive"]
        errors = validate_task(task)
        self.assertIn("COMPLETE_MEMORY_SCOPE_REQUIRES_RETRIEVAL_RECEIPT", errors)
        self.assertIn("COMPLETE_MEMORY_SCOPE_CANNOT_HIDE_UNCOVERED_SCOPES", errors)

    def test_fail_closed_must_be_true(self):
        task = sample_task()
        task["verification_profile"]["fail_closed"] = False
        self.assertIn("FAIL_CLOSED_VERIFICATION_PROFILE_REQUIRED", validate_task(task))

    def test_external_side_effects_must_be_disabled(self):
        task = sample_task()
        task["security"]["external_side_effects_allowed"] = True
        self.assertIn("EXTERNAL_SIDE_EFFECTS_MUST_BE_DISABLED", validate_task(task))

    def test_execute_requires_authorization_reference(self):
        task = sample_task()
        task["execution_mode"] = "EXECUTE"
        self.assertIn("EXECUTE_REQUIRES_AUTHORIZATION_REFERENCE", validate_task(task))

    def test_physics_execution_is_blocked_by_bridge(self):
        task = sample_task()
        task["domain"] = "PHYSICS_SIMULATION"
        task["execution_mode"] = "EXECUTE"
        task["authorization_ref"] = "approved-scope"
        self.assertIn("PHYSICS_ACTUATION_NOT_ALLOWED_BY_BRIDGE_CLIENT", validate_task(task))

    def test_bad_digest_is_rejected(self):
        task = sample_task()
        task["input_artifacts"][0]["sha256"] = "not-a-digest"
        self.assertTrue(any(code.startswith("INVALID_ARTIFACT_DIGEST") for code in validate_task(task)))

    def test_malformed_trust_state_does_not_crash(self):
        task = sample_task()
        task["input_artifacts"][0]["trust_state"] = ["TRUSTED"]
        self.assertTrue(any(code.startswith("INVALID_ARTIFACT_TRUST_STATE") for code in validate_task(task)))

    def test_malformed_execution_mode_does_not_crash(self):
        task = sample_task()
        task["execution_mode"] = ["EXECUTE"]
        self.assertIn("INVALID_EXECUTION_MODE", validate_task(task))

    def test_build_envelope_binds_exact_task_digest(self):
        task = sample_task()
        key = b"request-signing-key-that-is-long-enough"
        envelope = build_envelope(task, key)
        self.assertEqual(envelope["task_digest"], sha256_hex(canonical_json(task)))
        expected = hmac.new(key, canonical_json({k: v for k, v in envelope.items() if k != "signature"}), hashlib.sha256).hexdigest()
        self.assertTrue(hmac.compare_digest(envelope["signature"], expected))


class ReceiptVerificationTests(unittest.TestCase):
    def signed_receipt(self, task_id: str, digest: str, key: bytes) -> dict:
        receipt = {
            "receipt_id": "receipt-001",
            "task_id": task_id,
            "task_digest": digest,
            "status": "QUEUED",
            "issued_at": "2026-10-09T12:00:01Z",
        }
        receipt["response_signature"] = hmac.new(key, canonical_json(receipt), hashlib.sha256).hexdigest()
        return receipt

    def test_valid_receipt_is_accepted_as_ack_only(self):
        key = b"receipt-verification-key-is-long-enough"
        result = verify_receipt(
            self.signed_receipt("task-1", "a" * 64, key),
            expected_task_id="task-1",
            expected_task_digest="a" * 64,
            receipt_key=key,
        )
        self.assertEqual(result["status"], "QUEUED")

    def test_receipt_for_another_task_is_rejected(self):
        key = b"receipt-verification-key-is-long-enough"
        with self.assertRaises(BridgeError):
            verify_receipt(
                self.signed_receipt("wrong-task", "a" * 64, key),
                expected_task_id="task-1",
                expected_task_digest="a" * 64,
                receipt_key=key,
            )

    def test_tampered_receipt_is_rejected(self):
        key = b"receipt-verification-key-is-long-enough"
        receipt = self.signed_receipt("task-1", "a" * 64, key)
        receipt["status"] = "ADMITTED"
        with self.assertRaises(BridgeError):
            verify_receipt(
                receipt,
                expected_task_id="task-1",
                expected_task_digest="a" * 64,
                receipt_key=key,
            )

    def test_unknown_state_cannot_claim_success(self):
        key = b"receipt-verification-key-is-long-enough"
        receipt = self.signed_receipt("task-1", "a" * 64, key)
        receipt["status"] = "VERIFIED"
        receipt.pop("response_signature")
        receipt["response_signature"] = hmac.new(key, canonical_json(receipt), hashlib.sha256).hexdigest()
        with self.assertRaises(BridgeError):
            verify_receipt(
                receipt,
                expected_task_id="task-1",
                expected_task_digest="a" * 64,
                receipt_key=key,
            )

    def test_unhashable_status_cannot_crash_receipt_verifier(self):
        key = b"receipt-verification-key-is-long-enough"
        receipt = self.signed_receipt("task-1", "a" * 64, key)
        receipt["status"] = ["QUEUED"]
        with self.assertRaises(BridgeError):
            verify_receipt(
                receipt,
                expected_task_id="task-1",
                expected_task_digest="a" * 64,
                receipt_key=key,
            )


class EndpointSafetyTests(unittest.TestCase):
    def test_endpoint_missing_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(BridgeError):
                _configured_endpoint()

    def test_public_http_is_rejected(self):
        with patch.dict(os.environ, {"VX_ENGINEERING_SERVER_URL": "http://example.com"}, clear=True):
            with self.assertRaises(BridgeError):
                _configured_endpoint()

    def test_loopback_http_requires_explicit_opt_in(self):
        env = {
            "VX_ENGINEERING_SERVER_URL": "http://127.0.0.1:8787",
            "VX_ENGINEERING_ALLOW_INSECURE_LOOPBACK": "true",
        }
        with patch.dict(os.environ, env, clear=True):
            self.assertEqual(_configured_endpoint(), "http://127.0.0.1:8787")

    def test_malformed_url_is_rejected_without_traceback(self):
        with patch.dict(os.environ, {"VX_ENGINEERING_SERVER_URL": "http://[broken"}, clear=True):
            with self.assertRaises(BridgeError):
                _configured_endpoint()

    def test_redirects_are_not_followed(self):
        handler = _NoRedirectHandler()
        result = handler.redirect_request(None, None, 302, "Found", {}, "https://redirect.invalid/")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
