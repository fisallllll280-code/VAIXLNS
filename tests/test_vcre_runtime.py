import unittest

from vcre.engine import Invariant, RealityEngine, ScientificObject

class VCREExecutableTests(unittest.TestCase):
    def setUp(self):
        self.engine = RealityEngine("VCRE-DEMO", "1.0.0")
        self.engine.register_invariant(Invariant("nonnegative-energy", lambda s: s["energy"] >= 0, "energy became negative"))
        self.engine.register_invariant(Invariant("finite-position", lambda s: abs(s["position"]) < 10_000, "position escaped admissible domain"))

    def test_scientific_state_cannot_be_arbitrary(self):
        obj = ScientificObject("position", "mechanics", "m", 1.0, "SIMULATED")
        obj.validate()
        with self.assertRaises(ValueError):
            ScientificObject("x", "mechanics", "m", 1.0, "CERTIFIED_TRUE").validate()

    def test_deterministic_transition_and_replay(self):
        initial = {"position": 0.0, "velocity": 2.0, "energy": 2.0}
        self.engine.create_world("W0", initial)
        steps = []
        for _ in range(4):
            def step(state):
                state["position"] += state["velocity"]
                return state
            steps.append(("constant-velocity", step, 1.0))
            self.engine.transition("W0", "constant-velocity", step, observation={"source": "synthetic-demo"})
        replay = self.engine.replay("W0", initial, steps)
        self.assertEqual(replay.state["position"], self.engine.worlds["W0"].state["position"])
        self.assertEqual(replay.state_hash, self.engine.worlds["W0"].state_hash)
        self.assertTrue(self.engine.ledger.verify())

    def test_invariant_violation_fails_closed(self):
        self.engine.create_world("W", {"position": 0.0, "energy": 1.0})
        with self.assertRaisesRegex(ValueError, "invariant violation"):
            self.engine.transition("W", "bad", lambda s: {"position": s["position"], "energy": -1.0})
        self.assertTrue(self.engine.ledger.verify())
        self.assertEqual(self.engine.worlds["W"].state["energy"], 1.0)

    def test_counterfactual_branch_isolated(self):
        self.engine.create_world("BASE", {"position": 1.0, "energy": 1.0})
        self.engine.branch("BASE", "ALT", {"position": 99.0})
        self.assertEqual(self.engine.worlds["BASE"].state["position"], 1.0)
        self.assertEqual(self.engine.worlds["ALT"].state["position"], 1.0)
        self.assertTrue(self.engine.ledger.verify())

    def test_proof_carrying_certificate(self):
        self.engine.create_world("CERT", {"position": 0.0, "energy": 1.0})
        cert = self.engine.certificate(
            result={"answer": 2.0},
            assumptions=["synthetic educational model"],
            errors={"rounding": 0.0},
            uncertainty={"model_form": 0.0},
            status="NUMERICALLY_VERIFIED",
        )
        self.assertIn("certificate_hash", cert)
        self.assertIn("replay_manifest", cert)
        self.assertTrue(self.engine.ledger.verify())

    def test_impossibility_returns_structured_record(self):
        result = self.engine.impossibility("outside validity domain", "example-model", ["x > x_max"])
        self.assertEqual(result["status"], "IMPOSSIBLE_OR_INVALID")
        self.assertIn("certificate_hash", result)
        self.assertTrue(self.engine.ledger.verify())

if __name__ == "__main__":
    unittest.main()
