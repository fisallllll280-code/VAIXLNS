# VX Supervised Runtime Bootstrap v1

**Mission:** VX-BOOTSTRAP-001  
**Status:** Implemented reference slice; production runtime NOT VERIFIED.  
**Dependencies:** Python 3.11+ and standard library only.

## Commands

\`\`\`bash
python -m py_compile runtime/*.py scripts/vx_bootstrap.py scripts/verify_vx_bootstrap_evidence.py tests/test_supervised_runtime.py
python -m unittest discover -s tests -p "test_supervised_runtime.py" -v
python scripts/vx_bootstrap.py --workdir .vx-bootstrap-run --output vx-bootstrap-evidence.json
python scripts/verify_vx_bootstrap_evidence.py vx-bootstrap-evidence.json
\`\`\`

The bootstrap launches a fixed repository-owned HTTP test service on 127.0.0.1, checks a real HTTP /health response, executes a task over HTTP and verifies the returned output, injects a controlled process termination, allows at most one restart, verifies health again, rejects an unauthorized production-deploy action, requests graceful shutdown, and checks exit code 0.

## Included components

- Supervisor and explicit lifecycle state machine with actor/timestamp/reason records.
- Agent registry with versioned identity, manifest digest, capability ceiling and lifecycle state.
- Mission engine with approved-mission check, bounded task count, schema, namespace and deadline validation.
- Bounded task queue, deadline checks and cancellation marker.
- Health monitor using process liveness plus an actual HTTP readiness check.
- Recovery manager with restart budget and time window.
- Fail-closed policy gate for action allowlist and resource limits.
- Hash-linked evidence ledger plus independent verifier.
- Fixed local-process adapter with no shell and no inherited environment variables; loopback service only.
- Manifest-only agent factory; generated arbitrary code is not executed or deployed.
- Offline paper-trading arithmetic explicitly tagged SIMULATED; no real-money order path or credentials.

## Evidence and limitations

The hash chain detects changed events when independently recomputed; it is not a digital signature or protected append-only store. The test service is a local integration fixture, not OS-enforced sandboxing. The agent factory creates metadata only. Its deployment gate remains blocked until a separate validation result and human approval are provided; this PR does not deploy agents. The paper simulator accepts caller-supplied price observations and does not fetch historical data or establish market performance. Durable registry/queue, container adapter, OS-level isolation, signed receipts, provider integrations and production deployment remain out of scope.

A local pass proves only this reference slice on the environment that ran it. GitHub CI is considered passed only when the workflow reports success for the exact commit.
