import unittest

from scripts.vx_federation_gate import FederationGate, Instance


class VXFederationGateTests(unittest.TestCase):
    def setUp(self):
        self.gate = FederationGate()
        self.gate.register(
            Instance(
                "VX-Code-01",
                "software-engineering",
                ("coding", "simulation", "verification"),
                "ACTIVE",
                ("observe", "simulate", "verify"),
            )
        )
        self.gate.register(
            Instance(
                "VX-Computer-01",
                "computer-engineering",
                ("hardware-analysis", "simulation", "verification"),
                "ACTIVE",
                ("observe", "simulate", "verify"),
            )
        )

    def test_discover_returns_multiple_connected_instances(self):
        instances = self.gate.discover("simulation")
        self.assertEqual(
            [item["instance_id"] for item in instances],
            ["VX-Code-01", "VX-Computer-01"],
        )

    def test_route_is_capability_and_authority_aware(self):
        route = self.gate.route("hardware-analysis", "simulate")
        self.assertEqual(route["route_target"], "VX-Computer-01")

    def test_isolated_instance_is_not_routable(self):
        self.gate.set_state("VX-Computer-01", "ISOLATED")
        with self.assertRaises(LookupError):
            self.gate.route("hardware-analysis")
