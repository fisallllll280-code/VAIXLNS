import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from patterns.vaixl_pattern_factory import DIRECTIONS, PatternFactory, PrivatePatternDomain, diagnose_route
from patterns.vaixl_language_vault import binding_fingerprint, verify_binding

def test_none_guard_does_not_crash():
    assert PrivatePatternDomain.validate(None)["state"] == "MISSING"

def test_replay_is_safe_when_absent():
    routes = PatternFactory(architectures=("a",)).build({
        "language": {"language_id": "L1", "binding_fingerprint": "f" * 64}
    })
    assert len(routes) == 4
    assert all(route["replay"] == {} for route in routes)

def test_each_language_has_exactly_four_directions():
    routes = PatternFactory(architectures=("a", "b")).build({
        "language": {"language_id": "L1", "binding_fingerprint": "f" * 64},
        "replay": {"seed": "deterministic"},
    })
    assert len(routes) == 8
    assert {r["direction"] for r in routes} == set(DIRECTIONS)

def test_route_diagnosis_does_not_weaken_security():
    result = diagnose_route({
        "candidate_id": "c", "architecture": "a", "language_id": "L1", "direction": "semantic"
    })
    assert result["state"] == "SECURITY_REJECTION"

def test_binding_is_verifiable_without_storing_secret():
    secret = b"test-secret"
    fingerprint = binding_fingerprint(secret, "pattern-1")
    assert verify_binding(secret, "pattern-1", fingerprint)
    assert not verify_binding(b"wrong", "pattern-1", fingerprint)
