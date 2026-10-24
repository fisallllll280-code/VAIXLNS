"""No-network conformance tests for gateway selection."""
import unittest

from scripts.vx_gateway_comparison import compare_gateways


def route():
    return {"state": "ROUTE_CANDIDATES_READY", "candidates": [{"provider_id": "test", "model_id": "mock"}],
            "provider_called": False, "plan_sha256": "test-policy-route"}


def policy():
    return {"allow_live_requests": False, "max_external_spend_sar": 0,
            "allowed_gateways": ["litellm", "omniroute"]}


def gateways():
    return [{"gateway_id": key, "contract_verified": True,
             "tenant_isolation_verified": True, "credential_mode": "external_secret_store",
             "estimated_request_cost_sar": 0, "egress_enabled": False}
            for key in ("litellm", "omniroute")]


class GatewayComparisonTests(unittest.TestCase):
    def test_offline_comparison_is_stable(self):
        first = compare_gateways(route(), gateways(), policy())
        second = compare_gateways(route(), list(reversed(gateways())), policy())
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "OFFLINE_COMPARISON_READY")
        self.assertFalse(first["execution_performed"])
        self.assertFalse(first["verified_performance_claim"])
        self.assertEqual(len(first["gateways"]), 2)

    def test_missing_route_blocks(self):
        self.assertEqual(compare_gateways({}, gateways(), policy())["status"], "BLOCKED")

    def test_nonzero_spend_blocks(self):
        p = policy()
        p["max_external_spend_sar"] = 0.01
        self.assertIn("ZERO_SPEND_POLICY_REQUIRED", compare_gateways(route(), gateways(), p)["blockers"])

    def test_live_mode_blocks(self):
        p = policy()
        p["allow_live_requests"] = True
        self.assertEqual(compare_gateways(route(), gateways(), p)["status"], "BLOCKED")

    def test_unverified_and_egress_gateways_rejected(self):
        bad = gateways()
        bad[0]["contract_verified"] = False
        bad[1]["egress_enabled"] = True
        self.assertIn("NO_VERIFIED_OFFLINE_GATEWAY",
                      compare_gateways(route(), bad, policy())["blockers"])

    def test_unknown_gateway_rejected(self):
        bad = gateways()
        bad[0]["gateway_id"] = "unregistered"
        result = compare_gateways(route(), bad, policy())
        self.assertEqual([x["gateway_id"] for x in result["gateways"]], ["omniroute"])

    def test_malformed_allowlist_fails_closed_with_receipt(self):
        for value in ([{}], [[]], [None], [123], ["litellm", {}]):
            with self.subTest(value=value):
                p = policy()
                p["allowed_gateways"] = value
                result = compare_gateways(route(), gateways(), p)
                self.assertEqual(result["status"], "BLOCKED")
                self.assertIn("INVALID_GATEWAY_ALLOWLIST", result["blockers"])
                self.assertEqual(result["gateways"], [])
                self.assertEqual(len(result["receipt_sha256"]), 64)
                self.assertFalse(result["execution_performed"])
                self.assertFalse(result["live_provider_called"])

    def test_malformed_gateway_id_skipped_without_exception(self):
        for value in ({}, [], None, 42):
            with self.subTest(value=value):
                bad = gateways()
                bad[0]["gateway_id"] = value
                result = compare_gateways(route(), bad, policy())
                self.assertEqual(result["status"], "OFFLINE_COMPARISON_READY")
                self.assertEqual([x["gateway_id"] for x in result["gateways"]], ["omniroute"])
                self.assertFalse(result["execution_performed"])

    def test_only_invalid_gateway_ids_fail_closed(self):
        bad = gateways()
        bad[0]["gateway_id"] = {}
        bad[1]["gateway_id"] = []
        result = compare_gateways(route(), bad, policy())
        self.assertEqual(result["status"], "BLOCKED")
        self.assertIn("NO_VERIFIED_OFFLINE_GATEWAY", result["blockers"])
        self.assertEqual(result["gateways"], [])
        self.assertEqual(len(result["receipt_sha256"]), 64)

    def test_missing_secret_boundary_rejected(self):
        bad = gateways()
        for item in bad:
            item["credential_mode"] = "inline"
        self.assertEqual(compare_gateways(route(), bad, policy())["status"], "BLOCKED")

    def test_positive_cost_estimate_rejected(self):
        bad = gateways()
        for item in bad:
            item["estimated_request_cost_sar"] = 1
        self.assertEqual(compare_gateways(route(), bad, policy())["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
