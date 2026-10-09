"""Conformance tests for the federated innovation network planner."""
from __future__ import annotations

import unittest

from scripts.innovation_network import build_network, digest


class InnovationNetworkTests(unittest.TestCase):
    def setUp(self):
        self.source = {
            "schema": "legacy",
            "items": [
                {"name": "Architecture Search", "family": "Architecture", "owner": "NEXNET", "state": "SOURCE-ASSERTED"},
                {"name": "Proof Engine", "family": "Verification", "owner": "VAIXLNS", "state": "PARTIAL"},
            ],
        }

    def test_network_is_deterministic_and_hash_is_valid(self):
        first = build_network(self.source)
        second = build_network(self.source)
        self.assertEqual(first, second)
        self.assertEqual(first["network_sha256"], digest({k: v for k, v in first.items() if k != "network_sha256"}))

    def test_each_innovation_has_full_bounded_research_lanes(self):
        network = build_network(self.source)
        self.assertEqual(network["summary"]["innovation_count"], 2)
        self.assertEqual(network["summary"]["task_count"], 22)
        for packet in network["work_packets"]:
            self.assertEqual(len(packet["research_lanes"]), 11)
            self.assertTrue(all(task["dispatch_state"] == "PLANNED_NOT_DISPATCHED" for task in packet["research_lanes"]))
            self.assertTrue(all(task["authority_scope"] == "RESEARCH_AND_RECOMMENDATION_ONLY" for task in packet["research_lanes"]))

    def test_no_live_connectivity_or_self_promotion_is_claimed(self):
        network = build_network(self.source)
        self.assertFalse(network["summary"]["system_connectivity_verified"])
        self.assertEqual(network["summary"]["dispatched_count"], 0)
        for packet in network["work_packets"]:
            self.assertFalse(packet["promotion_gate"]["self_promotion_allowed"])

    def test_priority_puts_unverified_ideas_ahead_of_verified_records(self):
        network = build_network(self.source)
        by_name = {packet["name"]: packet for packet in network["work_packets"]}
        self.assertGreater(by_name["Architecture Search"]["priority_score"], by_name["Proof Engine"]["priority_score"])


if __name__ == "__main__":
    unittest.main()
