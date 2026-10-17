# VX Universal Model & Tool Federation v1

**Status:** IMPLEMENTATION SPECIFICATION — adapters are not declared active by this document.
**Target:** route approved tasks across multiple model providers, local model servers, coding assistants, repositories, MCP servers, and work applications through VX.
**Canonical authority:** VAIXLNS. **Discovery/research:** NEXENT. **Model activation boundary:** VLNS, subject to verified identity and contract. **Execution:** VX.

## Non-negotiable boundary

A registry entry is not a live connection. Every connector begins in `NOT_CONFIGURED` or `DISCOVERED`; it becomes `ACTIVE` only after credentials are provisioned securely, the adapter is installed, contract tests pass, policy review is recorded, and a fresh runtime probe/evidence receipt is reviewed. Never infer availability from a provider name or API key alone.

## Federation layers

1. **Connector Registry** — immutable connector ID, provider, endpoint class, supported operations, data boundary, auth method, owner, version and state.
2. **Capability Normalizer** — common task envelope without flattening provider-specific semantics (tools, vision, audio, context limits, structured output, streaming).
3. **Policy Gate** — task/data classification, provider allowlist, region/retention constraints, scopes, user approval, cost/time/input/output budgets.
4. **Router** — select only eligible, verified connectors; explain eligibility/exclusion; no silent privacy or quality downgrade.
5. **Execution Envelope** — request ID, idempotency key where supported, timeout, cancellation, bounded retries, circuit breaker and explicit error outcome.
6. **Evidence Receipt** — connector/model/version, policy and contract digests, timestamps, redacted request/response hashes, status and test evidence.
7. **Memory & Index Bridge** — publish approved artifacts and metadata into per-system indexes while preserving source, lineage, ACL, retention, tenant, and content hash. Do not copy secrets or unrestricted conversation histories into shared memory.
8. **Conformance & Admission** — functional tests, malformed response, timeout, rate-limit, auth failure, prompt-injection, data-boundary, fallback and recovery tests; independent review before activation.

## Connector families to implement

| Family | Examples / protocol | Minimum initial operations | Default state |
|---|---|---|---|
| Hosted model APIs | OpenAI API / OpenAI-compatible endpoints | chat, structured output where supported, embeddings only if declared | NOT_CONFIGURED |
| Hosted model APIs | Anthropic Claude API | messages, tool-use metadata where supported | NOT_CONFIGURED |
| Hosted model APIs | Google Gemini API | generate content, modality/capability metadata | NOT_CONFIGURED |
| Cloud model platforms | Azure OpenAI, AWS Bedrock, Google Vertex AI | provider-specific model invocation through separate adapters | NOT_CONFIGURED |
| Local model runtimes | Ollama, vLLM, llama.cpp servers | local inference; explicit loopback/private-network policy | NOT_CONFIGURED |
| Coding/model workspaces | Claude Code, IDE assistants, other agent workspaces | only documented API/CLI/MCP entry points; no UI scraping or credential bypass | DISCOVERED / CONTRACT REQUIRED |
| Repository platforms | GitHub, GitLab, Bitbucket | least-privilege read-only inventory first; writes require separate scopes and approval | NOT_CONFIGURED |
| Tool interoperability | MCP servers, OpenAPI/REST tools | tool discovery, schema validation, scoped invocation through VX gate | NOT_CONFIGURED |
| Work collaboration | Slack, Microsoft Teams, Google Workspace, Linear/Jira | explicitly scoped search/read; write actions separately approved | NOT_CONFIGURED |
| Browser automation | approved Playwright/browser gateway | isolated session, domain allowlist, no shared credentials | NOT_CONFIGURED |
| Research/data sources | approved search, documentation, scientific metadata APIs | retrieve, attribute, timestamp, preserve source provenance | NOT_CONFIGURED |

These are target connector families, not a statement that every named service exposes an equivalent API or that any connector is currently authenticated.

## Canonical connector state machine

`UNREGISTERED → DISCOVERED → METADATA_CAPTURED → CONTRACTED → CONFIGURED → CONTRACT_TESTED → POLICY_REVIEWED → EVALUATED → AUTHORIZED → ACTIVE`

Failure or stale evidence moves a connector to `DEGRADED`, `QUARANTINED`, `REVOKED`, or `NOT_CONFIGURED`; no failure is silently skipped. `ACTIVE` is time-bound and requires revalidation after credentials, endpoint, model revision, policy, or data classification changes.

## Shared index and memory contract

Every ingested artifact must preserve:
- `artifact_id`, `source_connector_id`, source URI/repository and observed timestamp;
- source owner/tenant, access-control label, retention and data classification;
- original content hash and normalized-content hash (if normalized);
- language, artifact type, model/provider/version where relevant;
- extraction method/version, lineage edges and duplicate/supersession links;
- verification status and evidence references.

Indexing must be idempotent, incremental, permission-aware, deletion-aware, and reversible. Shared memory stores references and approved summaries by default, not unrestricted copies. Each system keeps its own namespace; cross-system reads use explicit contracts and authorization. A search hit is not proof of truth or permission to execute.

## Security and reliability invariants

- Secrets are stored only in a secret manager or protected runtime environment, never committed or inserted into prompts/logs.
- Model outputs, retrieved documents, repository content, MCP metadata and webhooks are untrusted input.
- Tool execution is default-deny and goes through a role/version-bound VX dispatcher and policy gate.
- Provider fallback repeats all policy checks; no fallback to a connector with weaker privacy, region, safety, or permission guarantees.
- Timeouts, cancellations, rate limits, refusals, malformed outputs and unavailable providers remain explicit states.
- No automatic production deployment, destructive repository mutation, financial transaction, or permission expansion.
- Connector receipts and evidence hashes prove what was captured, not that the content is factually correct.

## Rollout sequence

1. Inventory owned repositories and current adapters; reconcile identities without renaming or merging systems.
2. Ship registry schema and validation tests; mark all unverified connectors `NOT_CONFIGURED`.
3. Implement read-only GitHub connector and one configurable model-provider adapter.
4. Add local OpenAI-compatible endpoint support for Ollama/vLLM, behind loopback/private-network restrictions.
5. Add MCP discovery with schema validation and default-deny tool dispatch.
6. Add remaining providers and collaboration connectors one family at a time.
7. Add permission-aware index ingestion, lineage, deduplication and deletion propagation.
8. Run failure/recovery, data-isolation, prompt-injection and independent conformance tests.
9. Activate each connector only after dated evidence and explicit governance admission.

## Acceptance criteria

- Registry validation rejects duplicate IDs, missing ownership, invalid state transitions and undeclared capabilities.
- No connector reports `ACTIVE` without fresh evidence and a successful contract test.
- An unconfigured connector returns `NOT_CONFIGURED` without attempting a network call.
- Disallowed data, scopes, tools, regions and budgets are blocked before dispatch.
- Fallback eligibility is recomputed for every candidate.
- Index results preserve source, ACL, timestamp, hash and lineage; revoked access and deletion are propagated.
- Identical registry, policy and request metadata yield a reproducible routing explanation.
- Unit/integration test reports identify exact revision and do not treat static metadata as live connectivity.

## Current execution boundary

This document is committed on a feature branch for review. It does not install adapters, create provider credentials, connect external accounts, start servers, or prove live connectivity. Those require per-provider setup and runtime evidence.
