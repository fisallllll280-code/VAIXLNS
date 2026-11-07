# Ω-Impossibility Engine + Execution Fabric V1

**State:** IMPLEMENTED ON FEATURE BRANCH; verification status follows current CI. Not canonical and not a general theorem prover.

## What is executable

- Conservative feasibility triage and numeric range contradiction detection.
- Bounded concurrent batch scheduler; deterministic ordering of results and explicit task IDs.
- Load-aware remote scheduler selecting by observed EWMA latency × in-flight load, enforcing per-worker concurrency caps, opening a batch-scoped circuit after a worker failure, and trying another configured node before fallback.
- Worker adapter using only operator-configured HTTPS endpoints, bearer tokens from environment variables, bounded timeouts, response-size checks, and task-fingerprint correlation.
- Minimal typed HTTP worker exposing only `GET /healthz` and `POST /v1/assess`; it does not execute code or shell commands.
- Visible fallback to local execution, or strict remote failure via `--strict-remote`.

## Run local mode

From the repository root with Python 3.11+:

```powershell
python -m unittest tests.test_impossibility_engine tests.test_impossibility_fabric -v
@'
{
  "problems": [
    {
      "title": "Latency target",
      "goal": "Respond within 40 ms under the stated load",
      "constraints": [{"kind": "range", "variable": "latency_ms", "min": 0, "max": 40}],
      "evidence": [{"state": "OBSERVED", "ref": "baseline-run-001"}]
    },
    {
      "title": "Conflicting requirement",
      "goal": "Meet a configured range",
      "constraints": [{"kind": "range", "variable": "latency_ms", "min": 50, "max": 20}],
      "evidence": [{"state": "OBSERVED", "ref": "fixture"}]
    }
  ],
  "max_workers": 4
}
'@ | python -m tools.impossibility_engine batch --max-workers 4
```

Legacy single-problem mode remains available as `python -m tools.impossibility_engine < problem.json`.

## Run a worker

```powershell
python -m tools.impossibility_engine serve --host 127.0.0.1 --port 8787 --worker-id worker-local
```

Workers bind to loopback by default. Any non-loopback bind requires a non-empty secret in the environment variable named by `--token-env`. Put the worker behind a TLS-terminating reverse proxy before remote use. The coordinator accepts only explicitly configured HTTPS URLs ending in `/v1/assess`, reads bearer secrets from environment variables, limits timeouts and response size, and never auto-discovers arbitrary hosts.

Set `OMEGA_REMOTE_WORKERS` to JSON like:

```json
[
  {
    "worker_id": "compute-a",
    "endpoint": "https://compute-a.example/v1/assess",
    "token_env": "OMEGA_COMPUTE_A_TOKEN",
    "timeout_seconds": 15,
    "max_concurrency": 2
  },
  {
    "worker_id": "compute-b",
    "endpoint": "https://compute-b.example/v1/assess",
    "token_env": "OMEGA_COMPUTE_B_TOKEN",
    "timeout_seconds": 15
  }
]
```

Store each token in the corresponding environment variable; never place secrets in JSON, source control, or the worker URL. For a remote node, configure `OMEGA_WORKER_TOKEN` (or the chosen `--token-env`) on the worker process. Use valid HTTPS and a reverse proxy/TLS setup; the sample worker HTTP server does not provide TLS itself.

Then run `python -m tools.impossibility_engine batch --max-workers 8 < batch.json`. Use `--strict-remote` to disable local fallback. The response records the selected worker, transport, elapsed time, EWMA latency, per-worker peak concurrency, circuit state, and fallback/failure counts. A batch that uses local fallback is marked `DEGRADED`, not `EXECUTED`.

## Limits and honest performance boundary

This implementation executes batch dispatch and local work. The local scheduler is not evidence of CPU speedup for the small pure-Python triage function; local concurrency mainly validates orchestration and can overlap I/O-bound work. Horizontal throughput requires at least one separately deployed worker endpoint plus explicit configuration. The router ranks eligible workers by estimated completion time (`EWMA latency × (in-flight + 1)`), respects each node's concurrency cap, and avoids repeatedly sending jobs to a node whose circuit opened after failure. No remote endpoints are configured by default and no remote cluster has been provisioned by this PR.

Task fingerprints provide correlation and accidental-mismatch detection, not proof that a remote worker is honest or that its scientific conclusion is true. The engine does not claim physical impossibility from lack of a candidate, does not auto-promote a claim to `VERIFIED`, and performs no arbitrary shell/code execution.

## CI acceptance gates

- Input and schema validation.
- Stable result order under concurrent completion.
- Bounded concurrency and explicit failure states.
- HTTPS-only remote configuration, no inline credentials, and visible fallback.
- Unit tests and repository conformance workflows must pass before merge.

## Canonical boundary

This implementation is an ordinary proposed execution component. It does not modify `project.genome`, `Ω0_GENESIS_CORE`, or `Ω.000`. Scientific completeness and novelty are unassessed.
