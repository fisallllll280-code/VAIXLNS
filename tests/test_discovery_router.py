import unittest

from scripts.discovery_router import route_discovery


POLICY = {
    "directive_id": "parent-001",
    "version": "routing-policy-1",
    "family_routes": {
        "family-engineering": ["VX-ENGINEERING", "VX-FINANCIAL"],
        "family-finance": ["VX-FINANCIAL"],
    },
    "domain_routes": {
        "ENGINEERING": ["VX-ENGINEERING"],
        "FINANCIAL": ["VX-FINANCIAL"],
    },
}


def discovery(**overrides):
    value = {
        "discovery_id": "disc-001",
        "parent_directive_id": "parent-001",
        "classification": {
            "status": "CONFIRMED",
            "domains": ["ENGINEERING", "FINANCIAL"],
            "rationale": "Reviewed and confirmed",
        },
        "candidate_families": [
            {"family_id": "family-engineering", "identity_status": "VERIFIED"}
        ],
        "evidence": {"verification_status": "VERIFIED"},
        "security_status": "CLEAR",
        "license_status": "CLEAR",
    }
    value.update(overrides)
    return value


class DiscoveryRouterTests(unittest.TestCase):
    def test_routes_to_both_domains_without_authorizing_execution(self):
        result = route_discovery(discovery(), POLICY)
        self.assertEqual(
            [route["destination"] for route in result["routes"]],
            ["VX-ENGINEERING", "VX-FINANCIAL"],
        )
        self.assertFalse(result["execution_authorization"])
        self.assertEqual(result["decision_status"], "ROUTED")

    def test_missing_policy_holds_for_parent_review(self):
        result = route_discovery(discovery(), {})
        self.assertEqual(result["routes"][0]["destination"], "PARENT_REVIEW")
        self.assertEqual(result["decision_status"], "HOLD")
        self.assertFalse(result["execution_authorization"])

    def test_unverified_family_identity_holds(self):
        value = discovery(candidate_families=[
            {"family_id": "family-engineering", "identity_status": "UNVERIFIED"}
        ])
        result = route_discovery(value, POLICY)
        self.assertEqual(result["routes"][0]["destination"], "PARENT_REVIEW")

    def test_unverified_evidence_waits_for_evidence(self):
        value = discovery(evidence={"verification_status": "UNVERIFIED"})
        result = route_discovery(value, POLICY)
        self.assertTrue(all(route["status"] == "WAITING_FOR_EVIDENCE" for route in result["routes"]))
        self.assertFalse(result["execution_authorization"])

    def test_security_hold_blocks_normal_routing(self):
        result = route_discovery(discovery(security_status="RISK_FOUND"), POLICY)
        self.assertTrue(all(route["status"] == "SECURITY_HOLD" for route in result["routes"]))

    def test_license_hold_blocks_normal_routing(self):
        result = route_discovery(discovery(license_status="RESTRICTED"), POLICY)
        self.assertTrue(all(route["status"] == "LICENSE_HOLD" for route in result["routes"]))

    def test_pending_license_status_holds(self):
        result = route_discovery(discovery(license_status="PENDING"), POLICY)
        self.assertTrue(all(route["status"] == "LICENSE_HOLD" for route in result["routes"]))
        self.assertFalse(result["execution_authorization"])

    def test_engineering_only_does_not_route_to_finance(self):
        value = discovery(classification={
            "status": "CONFIRMED", "domains": ["ENGINEERING"], "rationale": "Engineering-only"
        })
        result = route_discovery(value, POLICY)
        self.assertEqual([route["destination"] for route in result["routes"]], ["VX-ENGINEERING"])

    def test_conflicting_parent_directive_holds(self):
        result = route_discovery(discovery(parent_directive_id="parent-old"), POLICY)
        self.assertEqual(result["routes"][0]["destination"], "PARENT_REVIEW")

    def test_decision_is_deterministic(self):
        first = route_discovery(discovery(), POLICY)
        second = route_discovery(discovery(), POLICY)
        self.assertEqual(first, second)

