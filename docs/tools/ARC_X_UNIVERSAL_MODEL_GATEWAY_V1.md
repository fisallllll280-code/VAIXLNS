# ARC-X Universal Model Gateway v1

**State:** SPECIFIED. This document defines an integration contract; it does not claim that any provider is connected.

## Objective

Make approved models discoverable through one capability-based interface while preserving provider identity, model-specific limits, data boundaries, provenance, and fallback policy. "Universal" means one governed adapter contract, not unrestricted access to every model.

## Architecture

1. **Model Registry** — provider, exact model ID, supported modalities/capabilities, context/output limits, region/data policy, pricing metadata source, version and availability timestamp.
2. **Adapter Contract** — normalize requests/responses without pretending that provider semantics are identical.
3. **Policy Gate** — checks task classification, tenant boundary, allowed data classes, provider/model allowlist, region, cost/time budgets and tool permissions before routing.
4. **Router** — selects only eligible models; records why a candidate was selected and why others were excluded.
5. **Execution Envelope** — request ID, timeout, token/cost cap, cancellation, retry ceiling, idempotency policy and circuit breaker.
6. **Evidence Ledger** — provider/model/version, request policy hash, timestamps, redacted input/output hashes, errors, and evaluation results. Never log secrets or unrestricted sensitive prompts by default.
7. **Independent Evaluation** — benchmark task-specific quality, safety, latency, reliability and cost; provider self-reported claims are not independent evidence.
8. **Human/Governed Release Gate** — new providers, new data classes, tool access, cross-border processing and production changes require explicit authorization.

## Canonical interface (conceptual)

`ModelRequest -> PolicyDecision -> EligibleCandidates -> RouteDecision -> AdapterExecution -> ValidatedResponse -> EvidenceRecord`

A refusal, timeout, malformed response or unavailable provider is an explicit outcome—not a fabricated answer. Fallback is permitted only among candidates that independently pass the same policy gate. No silent downgrade of privacy, safety, or quality constraints.

## Minimum adapter metadata

`provider_id, model_id, model_revision_or_snapshot, modalities, capabilities, limits, region, retention_policy, tool_support, pricing_source, observed_at, contract_digest`

Unknown or stale metadata is `PENDING_VERIFICATION`. Never infer a model's abilities from its name alone.

## Isolation and security

- Treat provider output and retrieved content as untrusted data, not executable instructions.
- Tool calls use separate least-privilege capabilities and per-call authorization.
- Never pass credentials in prompts, source control, logs, or model-visible context.
- Enforce tenant isolation, data minimization, explicit retention rules and outbound-domain allowlists.
- Prevent prompt injection from granting tools, changing policy, or crossing tenant/system boundaries.
- Apply per-tenant quotas, global budgets, timeout ceilings, circuit breakers and audit trails.
- No provider gets access to the entire repository or other providers' credentials by default.

## Integration states

`DISCOVERED -> METADATA_CAPTURED -> POLICY_REVIEWED -> CONTRACT_TESTED -> EVALUATED -> AUTHORIZED -> ACTIVE`

Each transition requires dated evidence and an accountable authority. A discovered endpoint or valid API key alone does not establish compatibility, safety or production readiness.

## Required conformance tests

- provider identity and model revision preserved;
- invalid capabilities and disallowed data are rejected before routing;
- budget and timeout enforcement;
- tenant and secret isolation;
- untrusted model output cannot alter policy;
- fallback re-runs eligibility checks;
- malformed/time-out/refusal outcomes remain explicit;
- evidence records are reproducible and redact sensitive content;
- deterministic route decisions for identical registry, policy and request metadata.

## Operational limitation

Live provider access requires provider terms, approved credentials, network/runtime infrastructure and policy configuration. Credentials must be provisioned through the relevant secret manager by an authorized operator. This specification does not claim that external providers are currently connected.
