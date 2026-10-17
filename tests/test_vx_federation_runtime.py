import os
import unittest
from unittest.mock import patch

from scripts.vx_federation_runtime import (
    ACTIVE_STATE, Connector, FederationRouter, Policy, TaskRequest,
    ConnectorError, load_registry
)


class FakeAdapter:
    def __init__(self, result=None, error=None):
        self.result = result or {"text": "ok"}
        self.error = error

    def complete(self, connector, request):
        if self.error:
            raise self.error
        return self.result


def connector(**overrides):
    value = {
        "connector_id": "model.test",
        "provider": "test",
        "model": "test-model",
        "adapter": "fake",
        "status": ACTIVE_STATE,
        "capabilities": ["chat"],
        "allowed_data_classes": ["PUBLIC"],
        "contract_digest": "a" * 64,
        "evidence_ref": "evidence://test/1"
    }
    value.update(overrides)
    return Connector.from_mapping(value)


def request(**overrides):
    value = {"messages": ({"role": "user", "content": "hello"},)}
    value.update(overrides)
    return TaskRequest(**value)


class VXFederationRuntimeTests(unittest.TestCase):
    def test_registry_has_multiple_connectors_and_none_active_by_default(self):
        registry = load_registry("registry/federation/vx_model_connectors.v1.json")
        self.assertGreaterEqual(len(registry), 10)
        self.assertTrue(all(item.status == "NOT_CONFIGURED" for item in registry))

    def test_unconfigured_connector_is_never_selected(self):
        item = connector(status="NOT_CONFIGURED")
        router = FederationRouter([item], Policy(frozenset({"test"})), {"fake": FakeAdapter()})
        response, receipt, decision = router.execute(request())
        self.assertIsNone(response)
        self.assertEqual(decision.outcome, "NO_ELIGIBLE_CONNECTOR")
        self.assertEqual(receipt.outcome, "BLOCKED")

    def test_active_connector_requires_contract_and_fresh_evidence(self):
        item = connector(contract_digest="UNVERIFIED", evidence_ref=None)
        router = FederationRouter([item], Policy(frozenset({"test"})), {"fake": FakeAdapter()})
        self.assertEqual(router.decide(request()).outcome, "NO_ELIGIBLE_CONNECTOR")

    def test_provider_allowlist_is_enforced(self):
        router = FederationRouter([connector()], Policy(frozenset({"different"})), {"fake": FakeAdapter()})
        decision = router.decide(request())
        self.assertIsNone(decision.selected_connector_id)
        self.assertIn("PROVIDER_NOT_ALLOWED_BY_POLICY", {e["reason"] for e in decision.exclusions})

    def test_restricted_data_fails_closed(self):
        router = FederationRouter(
            [connector(allowed_data_classes=["PUBLIC", "RESTRICTED"])],
            Policy(frozenset({"test"}), allowed_data_classes=frozenset({"PUBLIC"})),
            {"fake": FakeAdapter()}
        )
        self.assertEqual(router.decide(request(data_classification="RESTRICTED")).outcome, "BLOCKED_POLICY")

    def test_missing_capability_is_excluded(self):
        router = FederationRouter([connector()], Policy(frozenset({"test"})), {"fake": FakeAdapter()})
        decision = router.decide(request(required_capabilities=frozenset({"chat", "vision"})))
        self.assertEqual(decision.outcome, "NO_ELIGIBLE_CONNECTOR")
        self.assertEqual(decision.exclusions[0]["reason"], "REQUIRED_CAPABILITY_MISSING")

    def test_success_emits_hash_only_evidence(self):
        router = FederationRouter([connector()], Policy(frozenset({"test"})), {"fake": FakeAdapter({"text": "private answer"})})
        response, receipt, decision = router.execute(request())
        self.assertEqual(response["text"], "private answer")
        self.assertEqual(receipt.outcome, "SUCCESS")
        self.assertEqual(len(receipt.input_digest), 64)
        self.assertEqual(len(receipt.output_digest), 64)
        self.assertNotIn("private answer", str(receipt))
        self.assertEqual(decision.outcome, "ROUTED")

    def test_adapter_error_is_explicit_and_redacted(self):
        router = FederationRouter([connector()], Policy(frozenset({"test"})), {"fake": FakeAdapter(error=ConnectorError("AUTH_FAILED", "secret-bearing raw response"))})
        response, receipt, _ = router.execute(request())
        self.assertIsNone(response)
        self.assertEqual(receipt.outcome, "FAILED")
        self.assertEqual(receipt.error_code, "AUTH_FAILED")
        self.assertNotIn("secret-bearing", str(receipt))

    def test_timeout_and_budget_are_checked_before_routing(self):
        router = FederationRouter([connector()], Policy(frozenset({"test"}), max_timeout_seconds=5), {"fake": FakeAdapter()})
        decision = router.decide(request(timeout_seconds=6))
        self.assertEqual(decision.outcome, "BLOCKED_BUDGET")

    def test_missing_environment_credential_blocks_connector(self):
        item = connector(api_key_env="VX_TEST_MISSING_KEY")
        with patch.dict(os.environ, {}, clear=True):
            router = FederationRouter([item], Policy(frozenset({"test"})), {"fake": FakeAdapter()})
            self.assertEqual(router.decide(request()).outcome, "NO_ELIGIBLE_CONNECTOR")


if __name__ == "__main__":
    unittest.main()
