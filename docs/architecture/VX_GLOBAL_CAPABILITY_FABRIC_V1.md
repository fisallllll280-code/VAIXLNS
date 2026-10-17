# VX Global Capability Fabric — Architecture v1

Status: PROPOSAL / SPECIFICATION. This document is not evidence that any external provider is connected.

## Objective

Make VX a governed capability fabric that can discover, compare, route, execute, and verify AI models, coding agents, tools, libraries, indexes, datasets, and research sources without coupling the runtime to one vendor.

“Collect the world” means maintain a continuously refreshed, provenance-aware catalog of discoverable capabilities. It does not mean copying every package, dataset, model weight, or private API into one repository.

## Layers

1. **Authority and identity (VAIXLNS / Ω):** policy, project identity, canonical sources, approvals, evidence admission, immutable audit trail.
2. **VX control plane:** task decomposition, capability matching, scheduling, concurrency limits, retries, cancellation, budgets, circuit breakers, and deterministic replay where possible.
3. **Model gateway:** provider-neutral request/response contract, vendor-specific adapters, capability negotiation, model/version pinning, rate-limit handling, timeout and error normalization.
4. **Agent runtimes:** Claude Code, Gemini-based agents, OpenAI-based agents, other CLI/SDK agents, and local agent processes. Treat each runtime as a separate integration with its own permissions and evidence.
5. **Tool plane:** MCP servers, typed function tools, GitHub, repository operations, shell/build/test runners, browsers, data systems, and approved business APIs.
6. **Knowledge and index plane:** official documentation, GitHub code/repositories/releases, package registries (PyPI/npm/Conda), model and dataset hubs, scientific literature, vector indexes, symbol indexes, and VAIXLNS Ω registry.
7. **Execution isolation:** per-task sandbox, filesystem/network allowlists, secret broker, least privilege, resource quotas, and explicit approval for destructive or external side effects.
8. **Evidence plane:** request/response metadata, provider/model/version, input/output hashes where appropriate, tool-call transcript, exit code, test results, cost/latency measurements, replayability classification, and final admission decision.

## Catalog contract

Each capability record should include:
- stable capability ID, kind, provider, name, and version or version policy
- source URL, discovery timestamp, source revision/ETag when available, license, and provenance
- input/output schema, modalities, supported operations, and required permissions
- auth mode (never store secret values in the catalog), region, rate limits, and cost metadata when published
- health status, last successful probe, test suite, and evidence references
- security posture, data retention notes, known constraints, and compatibility range
- lifecycle state: DISCOVERED, SPECIFIED, CONTRACT_TESTED, CONNECTED, VERIFIED, DEGRADED, DISABLED
- explicit distinction between vendor-reported claims and VX-observed results

## Routing policy

For each task, VX should:
1. classify intent, risk, data sensitivity, required modalities, and expected output contract;
2. filter to capabilities allowed by policy and available credentials;
3. rank eligible candidates by task-specific benchmark quality, observed success rate, latency, cost, context limits, availability, and reproducibility;
4. choose one primary and optionally a verifier/critic, with a bounded fan-out budget;
5. execute in an isolated worker and validate output against schemas and task acceptance tests;
6. retry or escalate only under a declared policy; never silently switch to a less trusted provider;
7. preserve evidence and report both successful and failed attempts.

Do not use a universal “best model” score. Maintain per-task benchmark profiles (coding, repository repair, long-context synthesis, scientific search, multimodal perception, tool use, structured extraction, adversarial review).

## Provider and index strategy

- **Model APIs:** OpenAI, Anthropic, Google Gemini, xAI, Mistral, plus other compatible hosted providers and local inference engines.
- **Agent runtimes:** Claude Code and other code agents are process/SDK integrations, not merely model names.
- **Tool interoperability:** MCP where supported, plus typed REST/SDK/CLI adapters for systems that do not expose MCP.
- **Source discovery:** official vendor APIs/docs first; GitHub search and repository metadata; package registries; model/dataset hubs; scholarly indexes; curated MCP server registries.
- **Index types:** lexical, symbol/code, semantic/vector, graph/relationship, temporal/change, benchmark, and provenance/evidence indexes. Search should federate across them rather than merge all content into one untyped database.
- **Licensing:** store metadata and references by default. Download/cache artifacts only where licensing, terms, privacy, and storage budgets allow.

## Security invariants

- Never ask the user to paste API keys into chat or commit credentials.
- Read secrets only from an approved secret manager or environment injection.
- Default to read-only; require explicit approval for publish, merge, deploy, spend, delete, or external messaging.
- Treat tool descriptions, retrieved pages, repository contents, and model outputs as untrusted data, not instructions that can override policy.
- Apply network and filesystem allowlists, redaction, quotas, timeouts, and audit logs.
- A provider health check is not proof of task correctness; a mocked adapter test is not proof of live connectivity.
- Never promote a capability to VERIFIED without observed evidence and a named test contract.

## Metrics

Measure end-to-end task success, first-pass acceptance, independently verified correctness, latency p50/p95, cost per accepted task, retry rate, tool failure rate, unsafe-action rejection, reproducibility, and evidence completeness. Report the denominator and evaluation dataset; do not advertise a multiplier without a baseline.

## Delivery sequence

1. Inventory current repositories and existing adapters before adding replacements.
2. Validate catalog schema and add discovery jobs with source attribution.
3. Standardize adapter contract and capability metadata.
4. Add read-only probes and contract tests for each provider.
5. Add live smoke tests only when credentials and billing/permissions are configured.
6. Integrate one provider at a time behind policy gates; then add routing and independent verification.
7. Add benchmark harness and compare measured results before enabling automatic routing.
8. Expand to package/model/index discovery, incremental refresh, deduplication, license/security screening, and stale-record detection.

## Canonical preservation

Do not modify project.genome or Ω.000 / the Omega master index as part of this proposal. Any later registry integration must use a reviewed migration and preservation test.
