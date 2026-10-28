import unittest

from scripts.vx_federation_gate import ErrorSignal, FederationGate, Instance


class VXFederationGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = FederationGate()
        self.gate.register(Instance(
            "VX-Code-01", "software-engineering",
            ("coding", "simulation", "verification", "diagnosis"),
            "ACTIVE", ("observe", "simulate", "verify", "diagnose"),
        ))
        self.gate.register(Instance(
            "VX-Computer-01", "computer-engineering",
            ("hardware-analysis", "simulation", "verification", "diagnosis"),
            "ACTIVE", ("observe", "simulate", "verify", "diagnose"),
        ))
        self.gate.register(Instance(
            "VX-Security-01", "security",
            ("security-review", "diagnosis"),
            "ACTIVE", ("diagnose", "review"),
        ))

    def test_discover_returns_multiple_connected_instances(self):
        instances = self.gate.discover("simulation")
        self.assertEqual([item["instance_id"] for item in instances], ["VX-Code-01", "VX-Computer-01"])

    def test_route_is_capability_and_authority_aware(self):
        route = self.gate.route("hardware-analysis", "simulate")
        self.assertEqual(route["route_target"], "VX-Computer-01")

    def test_isolated_instance_is_not_routable(self):
        self.gate.set_state("VX-Computer-01", "ISOLATED")
        with self.assertRaises(LookupError):
            self.gate.route("hardware-analysis")

    def test_error_routes_to_registered_specialist(self):
        result = self.gate.route_error(ErrorSignal("ERR-1", "VX-runtime", "test_failure", "HIGH"))
        self.assertEqual(result["routing_status"], "ROUTED")
        self.assertEqual(result["route_target"], "VX-Code-01")

    def test_critical_error_blocks_deployment(self):
        result = self.gate.route_error(ErrorSignal("ERR-2", "NEXENT", "security", "CRITICAL"))
        self.assertTrue(result["deployment_blocked"])
        self.assertTrue(result["isolation_recommended"])
        self.assertEqual(result["route_target"], "VX-Security-01")

    def test_unknown_error_remains_unassigned_and_blocked(self):
        result = self.gate.route_error(ErrorSignal("ERR-3", "NEXENT", "unclassified failure", "HIGH"))
        self.assertEqual(result["routing_status"], "UNASSIGNED")
        self.assertTrue(result["deployment_blocked"])
        self.assertIsNone(result["route_target"])

    def test_duplicate_registration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_instance_id"):
            self.gate.register(Instance("VX-Code-01", "duplicate", ("coding",), "ACTIVE", ("diagnose",)))


if __name__ == "__main__":
    unittest.main()
