"""Deterministic predictive-simulation primitives for VCRE.

The kernel is intentionally bounded: it simulates caller-supplied ODE models.
It does not claim arbitrary physical truth or autonomous discovery of new laws.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import math
from numbers import Real
from typing import Any

Dynamics = Callable[[float, Mapping[str, float], Mapping[str, float]], Mapping[str, float]]
Invariant = Callable[[Mapping[str, float]], bool]


class PredictiveSimulationError(ValueError):
    """A model contract, numerical result, or invariant failed closed."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def content_digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise PredictiveSimulationError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise PredictiveSimulationError(f"{name} must be finite")
    return result


def _numeric_map(value: Mapping[str, Any], keys: set[str], name: str) -> dict[str, float]:
    if not isinstance(value, Mapping):
        raise PredictiveSimulationError(f"{name} must be a mapping")
    missing, extra = keys - set(value), set(value) - keys
    if missing or extra:
        raise PredictiveSimulationError(
            f"{name} keys mismatch; missing={sorted(missing)}, extra={sorted(extra)}"
        )
    return {key: _number(value[key], f"{name}.{key}") for key in sorted(keys)}


@dataclass(frozen=True)
class PredictiveModelContract:
    """Typed identity and declared unit labels for a supplied deterministic model.

    Unit strings are provenance-bearing declarations. This module does not
    parse them into dimensional algebra and therefore does not claim to prove
    dimensional consistency automatically.
    """

    model_id: str
    version: str
    state_units: Mapping[str, str]
    parameter_units: Mapping[str, str]
    assumptions: tuple[str, ...] = ()
    implementation_sha256: str | None = None

    def validate(self) -> None:
        if not isinstance(self.model_id, str) or not self.model_id.strip():
            raise PredictiveSimulationError("model_id is required")
        if not isinstance(self.version, str) or not self.version.strip():
            raise PredictiveSimulationError("version is required")
        if not self.state_units or any(not isinstance(k, str) or not k.strip() for k in self.state_units):
            raise PredictiveSimulationError("state_units must declare named state variables")
        if any(not isinstance(v, str) or not v.strip() for v in self.state_units.values()):
            raise PredictiveSimulationError("every state variable requires a unit label")
        if any(not isinstance(k, str) or not k.strip() for k in self.parameter_units):
            raise PredictiveSimulationError("parameter names must be non-empty strings")
        if any(not isinstance(v, str) or not v.strip() for v in self.parameter_units.values()):
            raise PredictiveSimulationError("every parameter requires a unit label")
        if any(not isinstance(x, str) or not x.strip() for x in self.assumptions):
            raise PredictiveSimulationError("assumptions must be non-empty strings")
        if self.implementation_sha256 is not None:
            digest = self.implementation_sha256.lower()
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise PredictiveSimulationError("implementation_sha256 must be a SHA-256 hex digest")

    def record(self) -> dict[str, Any]:
        self.validate()
        return {
            "model_id": self.model_id,
            "version": self.version,
            "state_units": dict(sorted(self.state_units.items())),
            "parameter_units": dict(sorted(self.parameter_units.items())),
            "assumptions": list(self.assumptions),
            "implementation_sha256": self.implementation_sha256.lower() if self.implementation_sha256 else None,
            "implementation_pin_status": "CALLER_DECLARED" if self.implementation_sha256 else "UNPINNED",
        }


def _evaluate(
    derivative: Dynamics,
    t: float,
    state: Mapping[str, float],
    parameters: Mapping[str, float],
    keys: set[str],
) -> dict[str, float]:
    try:
        raw = derivative(t, dict(state), dict(parameters))
    except Exception as exc:
        raise PredictiveSimulationError(
            f"model evaluation failed at t={t!r}: {type(exc).__name__}: {exc}"
        ) from exc
    return _numeric_map(raw, keys, f"derivative(t={t!r})")


def _rk4_step(
    derivative: Dynamics,
    t: float,
    state: Mapping[str, float],
    h: float,
    parameters: Mapping[str, float],
    keys: set[str],
) -> dict[str, float]:
    k1 = _evaluate(derivative, t, state, parameters, keys)
    k2_state = {k: state[k] + h * k1[k] / 2 for k in keys}
    k2 = _evaluate(derivative, t + h / 2, k2_state, parameters, keys)
    k3_state = {k: state[k] + h * k2[k] / 2 for k in keys}
    k3 = _evaluate(derivative, t + h / 2, k3_state, parameters, keys)
    k4_state = {k: state[k] + h * k3[k] for k in keys}
    k4 = _evaluate(derivative, t + h, k4_state, parameters, keys)
    result = {
        k: state[k] + h * (k1[k] + 2 * k2[k] + 2 * k3[k] + k4[k]) / 6
        for k in keys
    }
    return _numeric_map(result, keys, "next_state")


def _check_invariants(
    state: Mapping[str, float],
    invariants: Mapping[str, Invariant],
    t: float,
) -> dict[str, str]:
    outcomes: dict[str, str] = {}
    for name, check in sorted(invariants.items()):
        if not isinstance(name, str) or not name.strip() or not callable(check):
            raise PredictiveSimulationError("invariants require named callable checks")
        try:
            passed = bool(check(dict(state)))
        except Exception as exc:
            raise PredictiveSimulationError(
                f"invariant {name!r} failed to evaluate at t={t!r}: {type(exc).__name__}"
            ) from exc
        if not passed:
            raise PredictiveSimulationError(f"invariant violation at t={t!r}: {name}")
        outcomes[name] = "PASS"
    return outcomes


def simulate_rk4(
    contract: PredictiveModelContract,
    derivative: Dynamics,
    initial_state: Mapping[str, Any],
    parameters: Mapping[str, Any],
    *,
    t0: float = 0.0,
    t_end: float = 1.0,
    dt: float = 0.01,
    invariants: Mapping[str, Invariant] | None = None,
    max_steps: int = 100_000,
) -> dict[str, Any]:
    """Integrate a supplied ODE and report step-doubling truncation diagnostics.

    Accepted points use two half-sized RK4 steps. A full-sized RK4 step is
    compared with them and abs(fine - coarse)/15 is reported as a local error
    estimate. It is diagnostic only, not a certified global error bound.
    """
    contract.validate()
    if not callable(derivative):
        raise PredictiveSimulationError("derivative must be callable")
    start, end, requested_dt = _number(t0, "t0"), _number(t_end, "t_end"), _number(dt, "dt")
    if end <= start:
        raise PredictiveSimulationError("t_end must exceed t0")
    if requested_dt <= 0:
        raise PredictiveSimulationError("dt must be positive")
    if isinstance(max_steps, bool) or not isinstance(max_steps, int) or max_steps < 1:
        raise PredictiveSimulationError("max_steps must be a positive integer")

    keys = set(contract.state_units)
    pkeys = set(contract.parameter_units)
    state = _numeric_map(initial_state, keys, "initial_state")
    p = _numeric_map(parameters, pkeys, "parameters")
    checks = dict(invariants or {})
    invariant_results = _check_invariants(state, checks, start)
    model_record = contract.record()

    def point(t: float, values: Mapping[str, float], error: Mapping[str, float]) -> dict[str, Any]:
        sorted_state = dict(sorted(values.items()))
        return {
            "t": t,
            "state": sorted_state,
            "state_hash": content_digest({
                "model_id": contract.model_id, "version": contract.version,
                "t": t, "state": sorted_state,
            }),
            "local_truncation_error_estimate": dict(sorted(error.items())),
        }

    zero_error = {k: 0.0 for k in keys}
    trajectory = [point(start, state, zero_error)]
    max_error = {k: 0.0 for k in keys}
    sum_error = {k: 0.0 for k in keys}
    t = start
    steps = 0

    while t < end:
        if steps >= max_steps:
            raise PredictiveSimulationError(f"max_steps={max_steps} exceeded")
        remaining = end - t
        h = min(requested_dt, remaining)
        coarse = _rk4_step(derivative, t, state, h, p, keys)
        half = _rk4_step(derivative, t, state, h / 2, p, keys)
        fine = _rk4_step(derivative, t + h / 2, half, h / 2, p, keys)
        local = {k: abs(fine[k] - coarse[k]) / 15 for k in keys}
        _numeric_map(local, keys, "local_error")
        next_t = end if h >= remaining else t + h
        if next_t <= t:
            raise PredictiveSimulationError("time progression stalled at floating-point resolution")
        _check_invariants(fine, checks, next_t)
        for k in keys:
            max_error[k] = max(max_error[k], local[k])
            sum_error[k] += local[k]
        state, t = fine, next_t
        steps += 1
        trajectory.append(point(t, state, local))

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "status": "SIMULATED",
        "model": model_record,
        "solver": {
            "id": "RK4_STEP_DOUBLING_DIAGNOSTIC_V1",
            "requested_step_size": requested_dt,
            "accepted_step_count": steps,
            "time_interval": {"start": start, "end": end},
            "maximum_steps": max_steps,
        },
        "parameters": dict(sorted(p.items())),
        "trajectory": trajectory,
        "diagnostics": {
            "invariant_checks": invariant_results,
            "all_committed_states_checked": True,
            "max_local_truncation_error_estimate": dict(sorted(max_error.items())),
            "sum_local_truncation_error_estimates": dict(sorted(sum_error.items())),
            "numerical_error_status": "DIAGNOSTIC_ONLY_NOT_CERTIFIED_GLOBAL_BOUND",
            "empirical_forecast_accuracy": "NOT_ESTABLISHED",
            "measurement_uncertainty": "NOT_QUANTIFIED",
            "parameter_uncertainty": "NOT_QUANTIFIED",
            "model_form_uncertainty": "NOT_QUANTIFIED",
        },
        "limitations": [
            "Unit labels and derivative semantics are caller-declared, not automatically proven.",
            "Fixed-step RK4 step-doubling does not guarantee numerical stability for every model.",
            "Local truncation estimates are not certified global error bounds.",
            "Physical forecast accuracy requires independent observations and validation.",
        ],
    }
    result["result_hash"] = content_digest(result)
    result["receipt_hash"] = content_digest(result)
    return result


def run_counterfactual_scenarios(
    contract: PredictiveModelContract,
    derivative: Dynamics,
    initial_state: Mapping[str, Any],
    scenarios: Mapping[str, Mapping[str, Any]],
    *,
    reference_scenario: str = "baseline",
    t0: float = 0.0,
    t_end: float = 1.0,
    dt: float = 0.01,
    invariants: Mapping[str, Invariant] | None = None,
) -> dict[str, Any]:
    """Compare explicit parameter scenarios; causal validity is not implied."""
    if not isinstance(scenarios, Mapping) or not scenarios or reference_scenario not in scenarios:
        raise PredictiveSimulationError(f"scenarios must include {reference_scenario!r}")
    runs: dict[str, dict[str, Any]] = {}
    for name, params in sorted(scenarios.items()):
        if not isinstance(name, str) or not name.strip():
            raise PredictiveSimulationError("scenario names must be non-empty strings")
        runs[name] = simulate_rk4(
            contract, derivative, initial_state, params, t0=t0, t_end=t_end,
            dt=dt, invariants=invariants,
        )
    baseline = runs[reference_scenario]["trajectory"][-1]["state"]
    deltas = {
        name: {
            key: result["trajectory"][-1]["state"][key] - baseline[key]
            for key in sorted(baseline)
        }
        for name, result in sorted(runs.items())
    }
    payload = {
        "schema_version": "1.0",
        "status": "SIMULATED",
        "reference_scenario": reference_scenario,
        "scenario_receipts": {name: run["receipt_hash"] for name, run in sorted(runs.items())},
        "final_state_deltas_from_reference": deltas,
        "causal_interpretation": "MODEL_CONDITIONAL_ONLY; real-world causal validity is not established",
    }
    payload["scenario_set_hash"] = content_digest(payload)
    return payload


def validate_observations(
    prediction: Mapping[str, Any],
    observations: Sequence[Mapping[str, Any]],
    *,
    absolute_tolerances: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare observed state samples at trajectory indices against predictions.

    Observations are caller-supplied and not authenticated here. Omitting
    tolerances yields INCONCLUSIVE, never automatic validation.
    """
    trajectory = prediction.get("trajectory")
    if not isinstance(trajectory, list) or not trajectory:
        raise PredictiveSimulationError("prediction requires a non-empty trajectory")
    if not observations:
        raise PredictiveSimulationError("at least one observation is required")
    keys = set(trajectory[0]["state"])
    errors: dict[str, list[float]] = {k: [] for k in sorted(keys)}
    used: set[int] = set()

    for index, obs in enumerate(observations):
        if not isinstance(obs, Mapping) or "step" not in obs or "state" not in obs:
            raise PredictiveSimulationError(f"observation {index} requires step and state")
        step = obs["step"]
        if isinstance(step, bool) or not isinstance(step, int) or step < 0 or step >= len(trajectory):
            raise PredictiveSimulationError(f"observation {index} has invalid trajectory step")
        if step in used:
            raise PredictiveSimulationError(f"duplicate observation step {step}")
        used.add(step)
        measured = _numeric_map(obs["state"], keys, f"observations[{index}].state")
        predicted = trajectory[step]["state"]
        for key in keys:
            errors[key].append(predicted[key] - measured[key])

    metrics: dict[str, Any] = {}
    for key, values in sorted(errors.items()):
        metrics[key] = {
            "sample_count": len(values),
            "bias": sum(values) / len(values),
            "mae": sum(abs(v) for v in values) / len(values),
            "rmse": math.sqrt(sum(v * v for v in values) / len(values)),
            "max_absolute_error": max(abs(v) for v in values),
        }

    tolerances = None
    status = "INCONCLUSIVE_NO_DECLARED_TOLERANCE"
    if absolute_tolerances is not None:
        tolerances = _numeric_map(absolute_tolerances, keys, "absolute_tolerances")
        if any(v < 0 for v in tolerances.values()):
            raise PredictiveSimulationError("absolute tolerances must be non-negative")
        status = (
            "PASS_ON_DECLARED_TOLERANCE"
            if all(metrics[k]["max_absolute_error"] <= tolerances[k] for k in keys)
            else "FAIL_DECLARED_TOLERANCE"
        )
    return {
        "status": status,
        "observation_provenance": "CALLER_SUPPLIED_NOT_INDEPENDENTLY_AUTHENTICATED",
        "observed_steps": sorted(used),
        "metrics": metrics,
        "absolute_tolerances": tolerances,
        "claim_boundary": "Tolerance comparison is not proof of physical truth or future forecast accuracy.",
    }
