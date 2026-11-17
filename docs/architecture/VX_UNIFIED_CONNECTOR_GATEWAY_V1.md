# VX Unified Connector Gateway Contract V1

**Status:** PROPOSED — implementation and live connectivity not yet verified  
**Execution authority:** VX  
**Cross-system coordination:** VLNS  
**Scope:** VAIXLNS, VX-runtime, VLNS, NEXENT, MCP servers, model providers, tools, APIs, repository automation, and future approved adapters.

## 1. Decision

All external tool, model, MCP-server, and service integrations must be mediated by VX through one governed connector gateway. Systems must not create undocumented direct integrations that bypass identity, policy, evidence, audit, or approval controls.

This is a routing and governance requirement, not a claim that every connector is implemented or connected. The operational verifier remains fail-closed until genuine runtime evidence exists.

## 2. Architecture

```text
User / Agent / Workflow
          |
          v
   VX Request Gateway
          |
          +--> Identity and caller authentication
          +--> Capability / connector registry
          +--> Policy and authorization
          +--> Schema validation and secret redaction
          +--> Risk classification / approval gate
          |
          v
   VX Connector Dispatcher
          |
          +--> MCP adapters
          +--> Model-provider adapters
          +--> HTTP/API adapters
          +--> Repository / CI adapters
          +--> Local process / container adapters
          |
          v
     External tool/system
          |
          v
 Result validation + provenance + audit event
          |
          v
 Caller receives result, status, and evidence reference
```

VLNS coordinates cross-system workflows above participating systems; it does not replace VX's execution boundary. VAIXLNS remains the knowledge/governance and canonical-index surface. NEXENT participates according to its existing specification. The gateway is the shared execution choke point.

## 3. Connector record

Every connector must declare:
- Stable `connector_id`, `kind`, owner, adapter version, source revision, and provenance.
- Approved `endpoint_ref` (never embed secret values), authentication mode, identity binding, and minimum scopes.
- Input/output schemas, capabilities, timeout, rate/quota, retry, cancellation, and idempotency rules.
- Risk tier, allowed/denied operations, approval requirements, and data-classification/redaction rules.
- Health probe, `last_verified_at`, evidence URI/hash, expiry, audit policy, and failure policy.
- Explicit lifecycle status: `PROPOSED`, `IMPLEMENTED`, `CONFIGURED`, `CONNECTIVITY_VERIFIED`, `AUTHORIZATION_TESTED`, `ACTIVE_VERIFIED`, `DEGRADED`, `REVOKED`, or `BLOCKED`.

Unknown values stay `null` or `UNVERIFIED`. A URL, saved credential, registry row, or passing unit test does not establish a live connector.

## 4. Request lifecycle

1. Authenticate the caller and bind the request to an identity.
2. Resolve the requested capability to a registered, version-pinned connector.
3. Validate the input schema and apply classification/redaction.
4. Evaluate policy, connector status, scopes, quotas, risk, and required human approval.
5. Fail closed on unknown identity, missing/stale evidence, denied scope, or absent approval.
6. Dispatch only the authorized operation; never expose raw credentials to a caller or model.
7. Validate response schema and record outcome, latency, error class, and provenance.
8. Emit an audit event with request ID, caller, connector/version, policy decision, evidence references, timestamps, and result digest. Exclude secrets and unnecessary sensitive payloads.
9. Return a typed result: `SUCCESS`, `DENIED`, `BLOCKED`, `TIMEOUT`, `UNAVAILABLE`, `INVALID_RESPONSE`, or `REQUIRES_APPROVAL`.

## 5. Security invariants

- No connector call without authenticated identity and explicit capability/policy authorization.
- No connector can self-register as trusted or self-promote to `ACTIVE_VERIFIED`.
- No arbitrary shell, filesystem, network, or repository-write access through a generic adapter.
- Write, deploy, spend, communication, and canonical-file operations require least privilege and an explicit approval boundary.
- Fetch secrets only at execution time from approved secret storage; never commit, log, return, or include them in prompts.
- Treat external content as untrusted data, never as gateway policy or instructions.
- Bound timeouts, retries, concurrency, queues, quotas, and cancellation. Retries must not duplicate non-idempotent actions.
- Circuit-break unhealthy connectors and surface stale evidence; do not silently route through an unapproved fallback.
- Isolate adapters by process/container and credential scope where supported.
- MCP servers are connector backends, not authorities. VX owns admission, tool selection, authorization, and audit.
- Model providers are called only through adapters that record provider/model, adapter/config version, policy result, usage metadata when available, and output provenance.
- Agents cannot bypass VX with raw provider credentials or arbitrary MCP endpoints.

## 6. Proposed VX interfaces

These are contracts to reconcile against existing handlers before coding; do not create a parallel runtime if equivalent routes exist.

- `POST /connectors/resolve`: resolve a capability to an eligible connector without exposing secrets.
- `POST /connectors/{connector_id}/invoke`: authorize, validate, execute, and audit one operation.
- `GET /connectors`: list caller-visible connector metadata/status.
- `GET /connectors/{connector_id}/health`: return evidence-backed health and freshness.
- `POST /connectors/{connector_id}/revoke`: authorized revocation with audit.
- `GET /audit/requests/{request_id}`: retrieve authorized request metadata/evidence references.

Mutating routes require authenticated identity, policy authorization, replay protection where appropriate, and structured audit. If a route is not implemented, return `BLOCKED`; never fabricate success.

## 7. Evidence required for ACTIVE_VERIFIED

Each lifecycle transition must record actor, timestamp, source revision, policy version, and evidence reference. Promotion to `ACTIVE_VERIFIED` requires:
- Authenticated health/connectivity challenge.
- Least-privilege capability test and a negative unauthorized-action test.
- Schema validation and bounded timeout test.
- Audit-event verification and secret-redaction test.
- Pinned adapter/configuration revision and approval by the designated authority.

A CI pass proves only the tests in that workflow. It does not prove remote endpoints, credentials, providers, or tools are live.

## 8. Required tests

- Unknown connector/capability blocked; unauthenticated and out-of-scope callers denied.
- Missing or stale health evidence blocks invocation.
- Invalid input/provider response rejected.
- Secrets absent from logs, results, audit records, and generated artifacts.
- Timeout, retry, cancellation, circuit-breaker, and idempotency behavior bounded and deterministic.
- Unauthorized write/deploy/spend denied; revocation takes effect.
- Every result links to an audit record.
- Registry-only edits and unit tests cannot promote a connector to active.

## 9. Implementation order

1. Inventory existing VX-runtime, VAIXLNS, and NEXENT registries and handlers; map equivalents before coding.
2. Define the typed connector record and policy contract using existing schema conventions.
3. Implement the dispatcher and audit events inside the existing VX runtime—not a new standalone service.
4. Add authorization-negative, redaction, timeout, idempotency, and lifecycle tests.
5. Integrate one low-risk, read-only connector in a non-production environment.
6. Capture commit-bound smoke-test receipts and ensure strict readiness remains fail-closed.
7. Add MCP/model/API adapters only through the same contract.
8. Obtain explicit approval before merge, production activation, spending, or irreversible operations.

## 10. Current verified boundary and protections

This document is a proposal only; it does not assert that the dispatcher, endpoints, adapters, credentials, or remote services are running. Prior strict readiness evidence reported zero active verified connectors and unconfigured services; rerun checks before status claims.

Do not modify `project.genome` or `Ω.000`. Preserve existing connector definitions and history. No broad deletion, parallel registry, privileged-token bypass, production activation, merge, deployment, or external spending without required authorization. The authorized spend ceiling remains SAR 0 until separately approved.
