# VAIXLNS Innovation Server v1

## Purpose

A local-first, provider-neutral job API to shorten the feedback loop for bounded knowledge-engineering operations. It provides a durable queue, idempotent submissions, worker execution for a fixed allowlist, and inspectable job receipts. It is an initial server node, not a claim of a globally distributed production platform.

## Run locally

Requires Python 3.12+ and the standard library only.

```bash
python -m services.innovation_server.server
```

Defaults:
- Bind: `127.0.0.1:8765`
- SQLite WAL database: `./.vaixlns/innovation-jobs.sqlite3`
- External effects: disabled

Environment variables:
- `VAIXLNS_SERVER_HOST`: bind address; loopback is recommended.
- `VAIXLNS_SERVER_PORT`: port, default `8765`.
- `VAIXLNS_SERVER_DB`: SQLite database path.
- `VAIXLNS_SERVER_TOKEN`: bearer token. A non-loopback bind is rejected unless a token of at least 32 characters is set.
- `VAIXLNS_SERVER_WORKERS`: worker count, default `4`, valid range `1..32`. This bounds concurrent local handlers; it does not enable distributed or multi-host execution.

Generate a local token with a cryptographically secure password manager or secret generator. Never commit it to the repository or pass it in URLs. For internet-facing deployment, place the service behind a managed TLS reverse proxy/API gateway, use managed secret storage, network restrictions, rate limits, monitoring, and a reviewed threat model. This reference server itself does not terminate TLS.

## API

### Health
`GET /health`

Returns service state and the fixed allowlisted action list. If a token is configured, send `Authorization: Bearer <token>`.

### Submit a job
`POST /v1/jobs`

```json
{
  "action": "hash_json",
  "payload": {"repository": "fisallllll280-code/VAIXLNS", "revision": "PINNED_COMMIT_SHA"},
  "idempotency_key": "unique-client-request-id"
}
```

Supported actions:
- `hash_json`: canonical JSON digest.
- `echo`: bounded payload echo for integration tests.
- `tokenize`: deterministic lexical token extraction from `payload.text`.

Arbitrary Python, shell, repository writes, network fetches, model-provider calls, and external side effects are not supported.

### Inspect jobs
- `GET /v1/jobs`
- `GET /v1/jobs/{job_id}`

A completed handler returns `verification_state: NOT_VERIFIED`. Completion means the allowlisted handler ran; it does not mean the result is correct, independently reproduced, or safe for production.

## Reliability and safety model

- SQLite WAL persists accepted jobs and results across process restarts.
- Idempotency keys prevent accidental duplicate submissions when the same key is reused with the same action and payload; conflicting reuse is rejected.
- Jobs are claimed transactionally. Interrupted `RUNNING` jobs are requeued on service startup because current handlers are deterministic and have no external effects.
- Request and result sizes are bounded.
- Unknown actions fail closed.
- Loopback is the default. Non-loopback binding requires a bearer token of at least 32 characters, but this is not a substitute for TLS, secret rotation, rate limiting, or gateway controls.
- The queue is single-node SQLite; it is not a multi-host broker and is not suitable for horizontal worker scaling yet.
- The HTTP server is a reference implementation; production deployment requires concurrency, load, fault-injection, security, observability, backup/restore, and operational-readiness testing.

## Integration roadmap

1. Add read-only adapters for the innovation index and pinned repository metadata.
2. Connect evidence-checked memory retrieval through the Memory–Task–Innovation Kernel.
3. Add an authenticated queue backend abstraction and a separately tested distributed broker only after workload and consistency requirements are measured.
4. Add worker pools with explicit capability scopes and lease/heartbeat semantics.
5. Integrate Microsoft-hosted services only through documented, optional provider adapters after tenant access, data boundaries, cost, and security are reviewed. No partnership or deployment is implied.
6. Require ARC-X-style independent evidence receipts before any result can be promoted into canonical knowledge.

## Current status

- Source code and regression tests are proposed on a feature branch.
- GitHub Actions status must be observed on the exact branch head before claiming test success.
- No server has been deployed, exposed to the public internet, or connected to live production data.
- Canonical `project.genome` and `Ω.000` are untouched.
