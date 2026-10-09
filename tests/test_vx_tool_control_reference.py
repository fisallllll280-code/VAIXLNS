"""Unit tests for the VX tool-control reference evaluator (stdlib only)."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from vx_tool_control_reference import evaluate_action, policy_digest


def active_policy():
    return {
        "policy_id": "VAIXLNS.VX_TOOL_CONTROL.TEST",
        "version": "1.0.0",
        "status": "ACTIVE",
        "enforcement_status": "ACTIVE",
        "default_max_authority": "A3_SANDBOX_MUTATE",
        "initial_nonproduction_budget_ceiling": {
            "max_execution_seconds": 300,
            "max_retries": 2,
            "max_concurrency": 4,
            "max_tokens": 50000,
            "max_network_calls": 20,
            "max_write_bytes": 1048576,
            "max_estimated_cost_usd": 0.0,
        },
        "approval_rules": {
            "action_digest_binding_required": True,
            "independent_approver_for_high_risk": True,
            "require_human_approval_from_risk_tier": "R3_HIGH",
        },
    }


def actor_profile():
    return {
        "status": "ADMITTED",
        "role": "VX Research Agent",
        "authority_ceiling": "A1_RESEARCH",
        "allowed_operation_classes": ["OBSERVE", "RESEARCH"],
        "allowed_resource_ids": ["repo:docs"],
        "allowed_environments": ["LOCAL_READ_ONLY"],
        "allowed_data_classes": ["PUBLIC", "INTERNAL"],
        "budget": {
            "max_execution_seconds": 120,
            "max_retries": 1,
            "max_concurrency": 2,
            "max_tokens": 10000,
            "max_network_calls": 10,
            "max_write_bytes": 0,
            "max_estimated_cost_usd": 0.0,
        },
    }


def tool_profile():
    return {
        "status": "ADMITTED",
        "version": "1.0.0",
        "adapter_id": "docs-search-adapter",
        "adapter_digest": "sha256:" + "a" * 64,
        "capability_id": "docs.search",
        "max_authority": "A1_RESEARCH",
        "allowed_operation_classes": ["OBSERVE", "RESEARCH"],
        "allowed_resource_ids": ["repo:docs"],
        "allowed_environments": ["LOCAL_READ_ONLY"],
        "allowed_data_classes": ["PUBLIC", "INTERNAL"],
        "requires_fresh_proof": False,
        "budget": {
            "max_execution_seconds": 120,
            "max_retries": 1,
            "max_concurrency": 2,
            "max_tokens": 10000,
            "max_network_calls": 10,
            "max_write_bytes": 0,
            "max_estimated_cost_usd": 0.0,
        },
    }


def action_envelope(policy, now=None):
    now = now or datetime.now(timezone.utc)
    return {
        "schema_version": "1.0.0",
        "action_id": "ACT-test-0001",
        "task_id": "TASK-test-0001",
        "correlation_id": "CORR-test-0001",
        "requested_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        "idempotency_key": "idem-test-key-000000001",
        "actor": {
            "identity_id": "AG-RESEARCHER",
            "kind": "AGENT",
            "role": "VX Research Agent",
            "authority_ceiling": "A1_RESEARCH",
        },
        "tool": {
            "tool_id": "docs-search",
            "version": "1.0.0",
            "adapter_id": "docs-search-adapter",
            "adapter_digest": "sha256:" + "a" * 64,
            "capability_id": "docs.search",
        },
        "operation": {
            "name": "search_docs",
            "class": "RESEARCH",
            "summary": "Search approved public project documentation.",
            "input_digest": "sha256:" + "b" * 64,
            "input_artifact_refs": [],
            "expected_effect": "Return source-linked read-only search results.",
        },
        "scope": {
            "resource_ids": ["repo:docs"],
            "path_allowlist": [],
            "network_allowlist": [],
            "data_classes": ["PUBLIC"],
            "environment": "LOCAL_READ_ONLY",
            "region_or_tenant": "test",
        },
        "policy_binding": {
            "policy_id": policy["policy_id"],
            "version": policy["version"],
            "digest": policy_digest(policy),
        },
        "budget": {
            "max_execution_seconds": 60,
            "max_retries": 1,
            "max_concurrency": 1,
            "max_tokens": 1000,
            "max_network_calls": 5,
            "max_write_bytes": 0,
            "max_estimated_cost_usd": 0.0,
        },
        "risk": {
            "tier": "R1_LOW",
            "impact_summary": "Read-only project documentation search.",
            "reversibility": "REVERSIBLE",
        },
        "verification": {
            "required_checks": ["source_provenance"],
            "proof_refs": [],
            "replay_required": False,
        },
        "approval_requirement": {
            "human_approval_required": False,
            "independent_approver_required": False,
            "approval_refs": [],
        },
    }


class VXToolControlReferenceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 10, 10, 0, 0, tzinfo=timezone.utc)
        self.policy = active_policy()
        self.actors = {"AG-RESEARCHER": actor_profile()}
        self.tools = {"docs-search": tool_profile()}
        self.envelope = action_envelope(self.policy, self.now)

    def evaluate(self, **overrides):
        args = {
            "actors": self.actors,
            "tools": self.tools,
            "policy": self.policy,
            "now": self.now,
            "environment_ceiling": "A3_SANDBOX_MUTATE",
        }
        args.update(overrides)
        return evaluate_action(self.envelope, **args)

    def test_exact_scoped_read_is_allowed(self):
        result = self.evaluate()
        self.assertEqual(result["decision"], "ALLOW")
        self.assertEqual(result["effective_authority"], "A1_RESEARCH")
        self.assertEqual(result["next_action"], "EXECUTE_EXACT_ACTION")
        self.assertIn("decision_digest", result)

    def test_unadmitted_policy_holds_every_request(self):
        self.policy["status"] = "PROPOSED_NOT_ADMITTED"
        self.envelope["policy_binding"]["digest"] = policy_digest(self.policy)
        result = self.evaluate()
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("POLICY_NOT_ADMITTED", result["reason_codes"])

    def test_unknown_tool_is_quarantined(self):
        self.envelope["tool"]["tool_id"] = "unknown-tool"
        result = self.evaluate()
        self.assertEqual(result["decision"], "QUARANTINE")
        self.assertIn("UNKNOWN_TOOL", result["reason_codes"])

    def test_adapter_digest_drift_is_quarantined(self):
        self.envelope["tool"]["adapter_digest"] = "sha256:" + "c" * 64
        result = self.evaluate()
        self.assertEqual(result["decision"], "QUARANTINE")
        self.assertIn("TOOL_QUARANTINED", result["reason_codes"])

    def test_actor_cannot_claim_a_higher_ceiling(self):
        self.envelope["actor"]["authority_ceiling"] = "A4_BRANCH_MUTATE"
        result = self.evaluate()
        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("MISSING_AUTHORITY", result["reason_codes"])

    def test_scope_escape_is_rejected(self):
        self.envelope["scope"]["resource_ids"] = ["repo:private"]
        result = self.evaluate()
        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("SCOPE_MISMATCH", result["reason_codes"])

    def test_expired_envelope_is_rejected(self):
        self.envelope["expires_at"] = (self.now - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        result = self.evaluate()
        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("EXPIRED_ENVELOPE", result["reason_codes"])

    def test_budget_overrun_holds_request(self):
        self.envelope["budget"]["max_tokens"] = 50001
        result = self.evaluate()
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("BUDGET_EXCEEDED", result["reason_codes"])

    def test_emergency_stop_rejects_new_work(self):
        result = self.evaluate(emergency_stop=True)
        self.assertEqual(result["decision"], "REJECT")
        self.assertIn("EMERGENCY_STOP", result["reason_codes"])

    def test_idempotency_key_is_not_reexecuted(self):
        records = {self.envelope["idempotency_key"]: {"action_digest": "prior", "status": "COMPLETED"}}
        result = self.evaluate(idempotency_records=records)
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("IDEMPOTENCY_CONFLICT", result["reason_codes"])

    def test_high_risk_action_holds_without_separate_approval(self):
        self.envelope["risk"]["tier"] = "R3_HIGH"
        self.envelope["verification"]["proof_refs"] = ["proof://test/proof-1"]
        self.envelope["verification"]["proof_digest"] = "sha256:" + "d" * 64
        self.envelope["verification"]["proof_valid_until"] = (
            self.now + timedelta(minutes=2)
        ).isoformat().replace("+00:00", "Z")
        result = self.evaluate()
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("APPROVAL_REQUIRED", result["reason_codes"])

    def test_tool_must_be_admitted(self):
        self.tools["docs-search"]["status"] = "CONFIGURED_NOT_ADMITTED"
        result = self.evaluate()
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("CAPABILITY_NOT_ADMITTED", result["reason_codes"])


if __name__ == "__main__":
    unittest.main()
