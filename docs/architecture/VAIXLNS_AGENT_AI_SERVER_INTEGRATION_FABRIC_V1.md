# VAIXLNS Agent, Model, Tool, and Server Integration Fabric v1.0

**Status:** SPECIFIED / PROPOSAL  
**Authority:** Subordinate to `project.genome`, `Ω0_GENESIS_CORE`, and the applicable VAIXLNS constitutional and security policies.  
**Purpose:** Define an incremental, testable architecture for connecting specialist agents, heterogeneous AI providers, MCP-compatible tools, repositories, and local/remote compute without weakening authority boundaries.

## 1. Non-goals and truth conditions

This document is an engineering specification, not evidence that the entire fabric is implemented, deployed, or production-ready. A connector being discoverable does not mean it is authenticated or connected. A successful repository CI run does not prove provider interoperability, deployment, or end-to-end performance.

Do not label a capability `VERIFIED` until its proof obligation has reproducible execution evidence, versioned inputs, test results, and provenance. Use `SPECIFIED`, `PARTIAL`, `MISSING`, `CONFLICT`, or `PROPOSAL` when that evidence is absent or incomplete.

## 2. Target architecture

1. **Authority and canonical registry** — canonical genome, schemas, policy, capability identity, trust boundaries, evidence requirements, and change authority.
2. **Intent and orchestration** — task decomposition into a dependency DAG; deadlines, budget ceilings, retry ceilings, cancellation, idempotency, and deterministic state transitions.
3. **Model gateway** — provider adapters behind one internal contract; route by task capability, evaluation quality, latency, cost, residency, and policy. Isolate provider credentials from agent prompts and logs.
4. **Agent registry and specialist workers** — explicit role, version, tool allowlist, input/output schema, maximum budget, evaluation suite, and owner for each agent. Agents are untrusted principals, not policy authorities.
5. **Tool / MCP registry** — protocol and version, input/output schema, declared effects, scope, authentication mode, trust tier, health, timeouts, and provenance. Discover first; grant least privilege separately.
6. **Execution fabric** — isolated local or remote workers, resource quotas, restricted network egress, immutable task envelope, artifact capture, and reproducible replay where possible.
7. **Event and task fabric** — durable task state, bounded queues, backpressure, idempotent delivery, capped exponential backoff with jitter, dead-letter handling, and cancellation.
8. **Evidence and ARC-X verification** — input/output hashes, source revision, tool and model versions, test reports, counterevidence, proof obligations, and conservative claim classification.
9. **Observability** — distributed trace ID across orchestration/model/tool/worker/evidence stages; p50/p95 latency, queue wait, token and compute cost, retry/timeout rates, error classes, and quality acceptance.
10. **Governance and promotion** — human approval for external publication, privilege changes, canonical writes, production deployment, and other high-impact side effects.

## 3. Task envelope

Every dispatched task should carry:
- `task_id`, `trace_id`, `parent_task_id`, and an idempotency key;
- intent, bounded plan, dependency list, and expected output schema;
- repository and revision identifiers where applicable;
- policy context, allowed capabilities, denied capabilities, and approval requirements;
- deadline, retry ceiling, concurrency ceiling, token/compute budget, and cost budget;
- provenance references, evidence requirements, and a stop condition.

Task outputs must identify completion state, artifacts, hashes, test evidence, warnings, unresolved assumptions, and any external side effects. Never silently convert timeout, missing output, or partial execution into success.

## 4. Routing and performance policy

Choose the lowest-cost route that satisfies the task's measured quality and policy requirements, not the cheapest model unconditionally. Use capability-aware routing, bounded fallbacks, and circuit breakers. Cache only when keys include all correctness-relevant inputs, versions, policy context, and data sensitivity constraints. Avoid duplicate parallel work; fan out only independent tasks and measure whether wall-clock savings exceed coordination and validation costs.

Establish a baseline before optimization. Required metrics:
- end-to-end and per-stage p50/p95 latency;
- successful, accepted, failed, retried, cancelled, and timed-out tasks;
- cost per accepted artifact and cost per successful workflow;
- output quality and regression rate on a fixed evaluation suite;
- queue depth, worker utilization, saturation, and backpressure events;
- reproducibility and provenance completeness;
- security-policy violations and unapproved side effects (target: zero).

Do not claim a percentage speedup until before/after runs use a representative workload, controlled conditions, sufficient samples, and a published measurement method.

## 5. Security boundaries

- Treat model output, repository content, retrieved documents, tool results, and agent messages as untrusted data.
- Do not let instructions embedded in retrieved content override system policy or user authorization.
- Use separate credentials per connector and environment; never place secrets in prompts, logs, repository artifacts, or model-visible diagnostics.
- Start with read-only scopes. Write scopes must be separately authorized, narrow, auditable, and revocable.
- Block path traversal and symlink escapes; apply file-size and file-type limits; restrict network egress and subprocess execution.
- Use isolated workers for code execution, with CPU/memory/time limits and explicit filesystem/network policy.
- Require human approval before publishing externally, changing access control, merging privileged changes, or promoting canonical state.
- Make all autonomous loops budget-bounded and cancellable; no agent can expand its own authority.

## 6. Integration sequence

### Phase A — Inventory and contracts
Inventory each repository, runtime, tool, model provider, server, and protocol. Record owner, version, auth mode, scopes, data class, effects, health check, test suite, and evidence location. Resolve conflicting definitions against canonical authority rather than silently merging them.

**Exit evidence:** machine-readable registry; schema validation; no unknown privileged capability.

### Phase B — Read-only gateway
Validate the local ARC-X MCP prototype on supported operating systems; test path confinement, symlinks, sensitive-file denial, file-size bounds, deterministic hashes, malformed input, and dependency isolation. Confirm actual host compatibility before claiming ChatGPT connectivity.

**Exit evidence:** CI pass, security tests, host handshake test, and documented unsupported paths.

### Phase C — Orchestrator and event lifecycle
Implement task envelopes, DAG execution, idempotency, cancellation, deadlines, retry ceilings, structured error types, and event provenance. Keep workers read-only initially.

**Exit evidence:** replay tests, duplicate-delivery tests, timeout/cancellation tests, and bounded-resource tests.

### Phase D — Model gateway and specialist agents
Add provider adapters one at a time. Evaluate task routing against a fixed benchmark. Add agents only when they provide a distinct capability and pass the same evaluation and permission controls.

**Exit evidence:** per-provider quality/latency/cost matrix; credentials isolation; fallback and circuit-breaker tests.

### Phase E — Sandboxed execution
Introduce isolated workers with explicit artifact inputs/outputs, quotas, network policy, and versioned runtime images. Require reproducible tests before creating a promotion candidate.

**Exit evidence:** sandbox escape tests, resource-limit tests, provenance bundle, replay record.

### Phase F — Controlled promotion and bounded evolution
Create proposed patches and release candidates automatically, but require human approval for external publication and canonical promotion. Evolution proposals must include the motivating evidence, expected benefit, regression suite, rollback path, and stopping conditions.

**Exit evidence:** approval audit trail, rollback test, policy-denial tests, and measurable release criteria.

## 7. Capability registry schema (conceptual)

Each integration record should include:
- `id`, `name`, `kind`, `version`, `owner`, `status`;
- `protocol`, `endpoint_mode`, `auth_ref` (reference only, never secret value);
- `input_schema`, `output_schema`, `capabilities`, `side_effects`;
- `allowed_scopes`, `data_classes`, `network_policy`, `resource_limits`;
- `health_check`, `timeouts`, `retry_policy`, `evaluation_suite`;
- `evidence_refs`, `content_hash`, `last_verified_at`, and explicit `verification_state`.

Use stable identifiers and versioned schemas. Unknown capabilities default to denied, not allowed.

## 8. Definition of done

The fabric is not considered production-ready until:
1. critical integration contracts are versioned and validated;
2. identity, authentication, authorization, revocation, and audit logging are tested;
3. task execution is bounded, cancellable, and resistant to duplicate delivery;
4. sensitive data and secrets are excluded from unauthorized model/tool contexts;
5. the end-to-end evaluation suite reports quality, latency, cost, reliability, and reproducibility;
6. rollback and failure recovery are demonstrated;
7. publication and canonical promotion remain approval-gated;
8. every claimed capability links to current, reproducible evidence.

## 9. Current evidence boundary

- **ARC-X Windows MCP prototype:** PR #105; Windows CI run `38021108068` completed successfully, including dependency installation and the ARC-X unit-test step. This verifies that specific workflow run only; it does not verify a real Windows machine installation, ChatGPT host connection, remote server, or production security.
- **GitHub integration:** repository and CI inspection are available through the connected GitHub tools; this does not mean all repositories or external systems are federated into a single running runtime.
- **Undermind:** a deep literature review was launched to investigate orchestration, model/tool interoperability, secure execution, evaluation, and performance engineering. Findings must be reviewed before they are treated as implementation evidence.
- **MagicPath dashboard:** a dashboard component was built to visualize the proposed layers and status boundaries. It is an interface artifact, not a deployed backend or runtime service.

## 10. Decision rule

Integrate incrementally, preserve source provenance, and prefer small reviewable changes. No destructive rewrite, repository deletion, canonical rewrite, external publication, or privilege expansion is authorized by this specification alone.
