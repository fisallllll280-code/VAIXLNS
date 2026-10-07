import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).parents[1]))

from patterns.vaixl_pattern_factory import (
    DIRECTIONS,
    PatternFactory,
    PrivatePatternDomain,
    diagnose_route,
)
from patterns.vaixl_language_vault import binding_fingerprint, verify_binding


class PatternFactoryTests(unittest.TestCase):
    def test_none_guard_does_not_crash(self):
        self.assertEqual(PrivatePatternDomain.validate(None)["state"], "MISSING")

    def test_replay_is_safe_when_absent(self):
        routes = PatternFactory(architectures=("a",)).build({
            "language": {"language_id": "L1", "binding_fingerprint": "f" * 64}
        })
        self.assertEqual(len(routes), 4)
        self.assertTrue(all(route["replay"] == {} for route in routes))

    def test_each_language_has_exactly_four_directions(self):
        routes = PatternFactory(architectures=("a", "b")).build({
            "language": {"language_id": "L1", "binding_fingerprint": "f" * 64},
            "replay": {"seed": "deterministic"},
        })
        self.assertEqual(len(routes), 8)
        self.assertEqual({r["direction"] for r in routes}, set(DIRECTIONS))

    def test_route_diagnosis_does_not_weaken_security(self):
        result = diagnose_route({
            "candidate_id": "c",
            "architecture": "a",
            "language_id": "L1",
            "direction": "semantic",
        })
        self.assertEqual(result["state"], "SECURITY_REJECTION")

    def test_binding_is_verifiable_without_storing_secret(self):
        secret = b"test-secret"
        fingerprint = binding_fingerprint(secret, "pattern-1")
        self.assertTrue(verify_binding(secret, "pattern-1", fingerprint))
        self.assertFalse(verify_binding(b"wrong", "pattern-1", fingerprint))


if __name__ == "__main__":
    unittest.main()
