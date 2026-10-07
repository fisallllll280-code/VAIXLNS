import unittest

from scripts.vaixl_private_pattern_domain import invoke_pattern_capability
from scripts.vaixl_pattern_factory import (
    FACTORY_ID,
    DIRECTIONS,
    adversarial_mutation_engine,
    build_factory_run,
    build_route_pattern,
    normalize_input,
    replay_factory_run,
)


class VAIXLNSPatternFactoryTests(unittest.TestCase):
    def request(self, routes=2):
        return {
            "problem": "recover from architecture drift",
            "objective": "produce a bounded evidence-backed recovery pattern",
            "constraints": ["no-self-authorization", "replay-required"],
            "capabilities": ["observe", "replay", "verify"],
            "routes_per_direction": routes,
        }

    def test_identity_and_direction_count(self):
        self.assertEqual(FACTORY_ID, "VAIXLNS-PATTERN-FACTORY-001")
        self.assertEqual(len(DIRECTIONS), 10)

    def test_normalization_is_sorted_and_bounded(self):
        data = normalize_input({
            "problem": "x",
            "objective": "y",
            "constraints": ["b", "a", "a"],
            "capabilities": ["verify", "observe", "verify"],
            "routes_per_direction": 80,
        })
        self.assertEqual(data.constraints, ("a", "b"))
        self.assertEqual(data.capabilities, ("observe", "verify"))
        self.assertEqual(data.routes_per_direction, 80)

    def test_factory_builds_10_by_80_logical_routes(self):
        result = build_factory_run(self.request(routes=80))
        self.assertEqual(result["topology"]["direction_count"], 10)
        self.assertEqual(result["topology"]["routes_per_direction"], 80)
        self.assertEqual(result["topology"]["total_logical_routes"], 800)
        self.assertTrue(result["deterministic"])
        replay = replay_factory_run(self.request(routes=80), result)
        self.assertTrue(replay["match"])

    def test_all_reference_routes_survive_security_gates(self):
        result = build_factory_run(self.request(routes=3))
        self.assertEqual(len(result["candidates"]), 30)
        self.assertEqual(result["quarantined"], [])
        self.assertIsNotNone(result["selected_pattern"])
        self.assertTrue(all(item["blocking_findings"] == 0 for item in result["candidates"]))
        self.assertTrue(all(item["private_language_bound"] for item in result["candidates"]))
        fabric = result["selected_pattern"]["private_language"]["fabric"]
        self.assertEqual(fabric["model"], "5-LAYER-4-DIRECTION-FABRIC")
        self.assertEqual(fabric["layer_count"], 5)
        self.assertEqual(fabric["directions_per_layer"], 4)
        self.assertEqual(fabric["total_directions"], 20)
        self.assertEqual(len(fabric["layers"]), 5)
        self.assertTrue(all(len(layer["directions"]) == 4 for layer in fabric["layers"]))
        self.assertEqual(fabric["cross_layer_gate"], "CROSS_LAYER_CONSISTENCY")
        self.assertEqual(result["selected_pattern"]["private_language"]["interface"]["mode"], "CAPABILITY_ONLY")
        self.assertEqual(
            result["selected_pattern"]["private_language"]["source"]["location"],
            "EXTERNAL_SECRET_VAULT",
        )

    def test_mutation_engine_blocks_expected_attack_classes(self):
        pattern = build_route_pattern(
            normalize_input(self.request(routes=1)),
            DIRECTIONS[0][0],
            DIRECTIONS[0][1],
            1,
        )
        records = adversarial_mutation_engine(pattern)
        self.assertEqual(len(records), 7)
        self.assertTrue(all(item["blocked"] for item in records))

    def test_capability_interface_does_not_expose_private_source(self):
        result = build_factory_run(self.request(routes=1))
        pattern = result["selected_pattern"]
        capability_result = invoke_pattern_capability(
            pattern,
            capability="verify",
            request={"input": "synthetic"},
            authority_envelope={
                "issuer": "external-authority",
                "grants": ["PATTERN_LANGUAGE_USE", "verify"],
            },
        )
        self.assertEqual(capability_result["status"], "CAPABILITY_RESULT")
        self.assertFalse(capability_result["language_source_returned"])
        self.assertFalse(capability_result["language_source_exposed"])
        self.assertNotIn("syntax", capability_result)
        self.assertNotIn("grammar", capability_result)

    def test_replay_hash_is_stable(self):
        request = self.request(routes=2)
        first = build_factory_run(request)
        replay = replay_factory_run(request, first)
        self.assertTrue(replay["match"])
        self.assertEqual(first["evidence_hash"], replay["replay_evidence_hash"])


if __name__ == "__main__":
    unittest.main()
