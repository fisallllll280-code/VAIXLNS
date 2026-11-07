import math
import unittest

from vcre.predictive import (
    PredictiveModelContract,
    PredictiveSimulationError,
    run_counterfactual_scenarios,
    simulate_rk4,
    validate_observations,
)


def oscillator_contract():
    return PredictiveModelContract(
        model_id="synthetic-harmonic-oscillator",
        version="1.0.0",
        state_units={"x": "m", "v": "m/s"},
        parameter_units={"omega": "1/s"},
        assumptions=("synthetic undamped harmonic oscillator", "constant angular frequency"),
    )


def oscillator(_t, state, parameters):
    omega = parameters["omega"]
    return {"x": state["v"], "v": -(omega * omega) * state["x"]}


class PredictiveSimulationTests(unittest.TestCase):
    def test_harmonic_oscillator_is_reproducible_and_has_diagnostics(self):
        args = dict(
            contract=oscillator_contract(),
            derivative=oscillator,
            initial_state={"x": 1.0, "v": 0.0},
            parameters={"omega": 1.0},
            t0=0.0,
            t_end=2 * math.pi,
            dt=0.04,
            invariants={"bounded_energy": lambda s: s["x"] ** 2 + s["v"] ** 2 <= 1.000001},
        )
        first = simulate_rk4(**args)
        second = simulate_rk4(**args)
        final = first["trajectory"][-1]["state"]
        self.assertAlmostEqual(final["x"], 1.0, delta=1e-7)
        self.assertAlmostEqual(final["v"], 0.0, delta=1e-7)
        self.assertEqual(first["receipt_hash"], second["receipt_hash"])
        self.assertTrue(first["diagnostics"]["all_committed_states_checked"])
        self.assertEqual(first["status"], "SIMULATED")
        self.assertEqual(first["diagnostics"]["empirical_forecast_accuracy"], "NOT_ESTABLISHED")
        self.assertEqual(first["model"]["implementation_pin_status"], "UNPINNED")
        self.assertGreater(first["diagnostics"]["sum_local_truncation_error_estimates"]["x"], 0.0)

    def test_invariant_violation_stops_the_simulation(self):
        contract = PredictiveModelContract(
            "linear", "1", {"x": "m"}, {}, ("test model",)
        )
        with self.assertRaisesRegex(PredictiveSimulationError, "invariant violation"):
            simulate_rk4(
                contract, lambda _t, s, _p: {"x": 1.0}, {"x": 0.0}, {},
                t_end=1.0, dt=0.25,
                invariants={"x-not-too-large": lambda s: s["x"] <= 0.5},
            )

    def test_model_contract_rejects_missing_or_nonfinite_inputs(self):
        contract = oscillator_contract()
        with self.assertRaisesRegex(PredictiveSimulationError, "keys mismatch"):
            simulate_rk4(contract, oscillator, {"x": 1.0}, {"omega": 1.0})
        with self.assertRaisesRegex(PredictiveSimulationError, "finite"):
            simulate_rk4(contract, oscillator, {"x": float("nan"), "v": 0.0}, {"omega": 1.0})
        with self.assertRaisesRegex(PredictiveSimulationError, "unit label"):
            PredictiveModelContract("bad", "1", {"x": ""}, {}).validate()

    def test_derivative_output_must_match_state_schema(self):
        contract = PredictiveModelContract("bad-derivative", "1", {"x": "m"}, {})
        with self.assertRaisesRegex(PredictiveSimulationError, "keys mismatch"):
            simulate_rk4(contract, lambda _t, _s, _p: {"y": 1.0}, {"x": 0.0}, {})

    def test_max_step_budget_fails_closed(self):
        contract = PredictiveModelContract("linear", "1", {"x": "m"}, {})
        with self.assertRaisesRegex(PredictiveSimulationError, "max_steps"):
            simulate_rk4(
                contract, lambda _t, s, _p: {"x": 1.0}, {"x": 0.0}, {},
                t_end=5.0, dt=0.1, max_steps=2,
            )

    def test_counterfactual_scenarios_compare_model_conditionally(self):
        contract = PredictiveModelContract(
            "exponential-growth", "1", {"x": "unitless"}, {"rate": "1/s"},
            ("synthetic first-order system",),
        )
        result = run_counterfactual_scenarios(
            contract,
            lambda _t, s, p: {"x": p["rate"] * s["x"]},
            {"x": 1.0},
            {"baseline": {"rate": 0.0}, "growth": {"rate": 1.0}},
            t_end=1.0, dt=0.02,
        )
        self.assertGreater(result["final_state_deltas_from_reference"]["growth"]["x"], 1.7)
        self.assertIn("MODEL_CONDITIONAL_ONLY", result["causal_interpretation"])
        self.assertEqual(len(result["scenario_set_hash"]), 64)

    def test_validation_is_inconclusive_without_tolerance_and_uses_explicit_metrics(self):
        prediction = simulate_rk4(
            PredictiveModelContract("linear", "1", {"x": "m"}, {}),
            lambda _t, _s, _p: {"x": 1.0},
            {"x": 0.0}, {}, t_end=1.0, dt=0.25,
        )
        observations = [{"step": 0, "state": {"x": 0.0}}, {"step": 4, "state": {"x": 1.0}}]
        inconclusive = validate_observations(prediction, observations)
        self.assertEqual(inconclusive["status"], "INCONCLUSIVE_NO_DECLARED_TOLERANCE")
        passed = validate_observations(prediction, observations, absolute_tolerances={"x": 1e-12})
        self.assertEqual(passed["status"], "PASS_ON_DECLARED_TOLERANCE")
        failed = validate_observations(
            prediction, [{"step": 4, "state": {"x": 2.0}}],
            absolute_tolerances={"x": 0.1},
        )
        self.assertEqual(failed["status"], "FAIL_DECLARED_TOLERANCE")
        with self.assertRaisesRegex(PredictiveSimulationError, "duplicate"):
            validate_observations(
                prediction,
                [{"step": 1, "state": {"x": 0.25}}, {"step": 1, "state": {"x": 0.25}}],
            )

    def test_declared_implementation_digest_is_validated(self):
        good = PredictiveModelContract(
            "pinned", "1", {"x": "m"}, {}, implementation_sha256="a" * 64
        )
        self.assertEqual(good.record()["implementation_pin_status"], "CALLER_DECLARED")
        with self.assertRaisesRegex(PredictiveSimulationError, "SHA-256"):
            PredictiveModelContract(
                "invalid", "1", {"x": "m"}, {}, implementation_sha256="not-a-hash"
            ).validate()


if __name__ == "__main__":
    unittest.main()
