import unittest

from scripts.omega_pattern_foundry import (
    ReferenceGenerator,
    adversarial_attack,
    build_candidate,
    gate,
    sha256_hex,
    validate_pattern,
)


class OmegaPatternFoundryTests(unittest.TestCase):
    def test_reference_candidate_is_valid(self):
        candidate = build_candidate({
            "problem": "coordinate recovery after service drift",
            "objective": "restore service safely",
            "constraints": ["no self-authorization"],
            "capabilities": ["observe", "replay", "verify"],
        })
        result = validate_pattern(candidate)
        self.assertTrue(result.valid, result.errors)
        self.assertEqual(candidate["status"], "PROPOSAL")

    def test_gate_accepts_hardened_reference_candidate(self):
        candidate = ReferenceGenerator().generate({
            "problem": "detect and recover from configuration drift",
            "objective": "recover with evidence",
            "constraints": ["bounded authority"],
            "capabilities": ["observe", "replay"],
        })
        candidate["provenance"]["genome_hash"] = sha256_hex(candidate)
        result = gate(candidate)
        self.assertTrue(result["valid"])
        self.assertEqual(result["blocking_findings"], 0)
        self.assertTrue(result["promotion_candidate"])

    def test_attack_blocks_missing_counterevidence(self):
        candidate = build_candidate({
            "problem": "test attack",
            "objective": "find weaknesses",
        })
        candidate["evidence_requirements"]["counterevidence_required"] = False
        findings = adversarial_attack(candidate)
        self.assertTrue(any(f.attack_class == "EVIDENCE" and f.result == "BLOCK" for f in findings))

    def test_attack_blocks_self_granting_authority(self):
        candidate = build_candidate({
            "problem": "test authority",
            "objective": "execute safely",
        })
        candidate["authority_model"] = {"permissions": ["admin:*"], "promotion": "self-promote"}
        findings = adversarial_attack(candidate)
        self.assertTrue(any(f.attack_class == "AUTHORITY" and f.result == "BLOCK" for f in findings))

    def test_evolved_pattern_requires_lineage(self):
        candidate = build_candidate({
            "problem": "test lineage",
            "objective": "evolve",
        })
        candidate["version"] = "1.1.0"
        candidate["provenance"]["parent_patterns"] = []
        result = validate_pattern(candidate)
        self.assertFalse(result.valid)
        self.assertIn("lineage_required_for_evolved_pattern", result.errors)


if __name__ == "__main__":
    unittest.main()
