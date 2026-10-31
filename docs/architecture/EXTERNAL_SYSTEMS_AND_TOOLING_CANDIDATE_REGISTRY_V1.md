# External Systems & Tooling Candidate Registry v1

**Record date:** 2026-10-28  
**Registry status:** `PROPOSED / UNASSESSED`  
**Canonical owner:** VAIXLNS  
**Discovery and evaluation:** NEXENT  
**Execution adapters:** VX, only after explicit authorization  
**Independent acceptance:** VV / ARC-X Ω evidence gates

## Purpose

Register external projects, frameworks, protocols, and infrastructure that may strengthen VAIXLNS × VX × NEXENT × VLNS. This is an intake register, not a claim that these tools are installed, connected, tested, or production-ready. Preserve source identity and license; do not vendor, merge, deploy, or grant credentials automatically.

## Candidate catalog

| Domain | Candidate systems | Potential fit | Initial state |
|---|---|---|---|
| Agent orchestration | OpenAI Agents SDK, LangGraph, Microsoft Agent Framework, AutoGen, CrewAI, Semantic Kernel | Typed agent tasks, delegation, tool boundaries, human approval | UNASSESSED |
| Workflow and durable execution | Temporal, n8n, Prefect, Apache Airflow, Dagster, Argo Workflows | Durable jobs, retries, schedules, workflow replay | UNASSESSED |
| Browser and web extraction | Firecrawl | Governed web discovery, crawling, extraction, source lineage | UNASSESSED |
| Telemetry and incident diagnosis | OpenTelemetry, Prometheus, Grafana, Jaeger, Sentry, Loki | Traces, metrics, logs, error and latency evidence | UNASSESSED |
| Policy, provenance, supply-chain security | Open Policy Agent, Sigstore/Cosign, SLSA, in-toto, Trivy | Policy decisions, artifact provenance, signing, vulnerability checks | UNASSESSED |
| Knowledge and retrieval | Neo4j, Qdrant, OpenSearch, PostgreSQL, DuckDB, Apache Iceberg | Graph relationships, semantic retrieval, search, analytical storage | UNASSESSED |
| Build and test | GitHub Actions, Dagger, BuildKit, Testcontainers, Nix, Renovate | Reproducible builds, isolated integration tests, dependency maintenance | UNASSESSED |
| Local and hosted model runtimes | Ollama, llama.cpp, vLLM, Hugging Face Transformers | Provider-neutral model execution and local inference options | UNASSESSED |
| Interoperability | MCP, OpenAPI, webhooks, gRPC, message brokers | Typed tool contracts and bounded system-to-system communication | UNASSESSED |
| Identity and secrets | HashiCorp Vault, workload identity, short-lived credentials | Least privilege, secret isolation, credential rotation | UNASSESSED |
| Runtime and infrastructure | Docker, Podman, Kubernetes, Linux, Termux | Portable runtime, sandboxing, Android-side development | UNASSESSED |
| Reliability and adversarial testing | Property-based testing, fuzzing, fault injection, digital-twin/simulation tooling | Failure discovery, recovery verification, regression evidence | UNASSESSED |
| Data and event lineage | Event sourcing, schema registries, CDC, data-lineage tooling | Auditable state changes, replay, schema evolution, provenance | UNASSESSED |
| Research and evaluation | Scientific-literature search, benchmark harnesses, model-evaluation frameworks | Evidence-backed discovery, reproducible comparisons | UNASSESSED |
| Business automation | CRM, billing, customer support, price monitoring, analytics | VX service delivery and first-revenue workflows | UNASSESSED |

## Admission pipeline

1. **DISCOVER** — record canonical project URL, owner, exact repository identity, release/commit, license, maintenance signals, and source timestamp.
2. **IDENTIFY** — classify capability, dependencies, data exposure, deployment model, and overlap with existing project assets.
3. **QUARANTINE** — no secrets, production access, automatic install, or execution during initial inspection.
4. **ASSESS** — inspect code, license, security posture, SBOM/dependencies where available, compatibility, resource cost, and exit/replacement path.
5. **SANDBOX** — use a disposable environment with least privilege and bounded network/filesystem access.
6. **TEST** — define acceptance criteria, failure cases, reproducibility, rollback, and measurable benefit before integration.
7. **VERIFY** — require independent evidence and record exact test commands, outputs, artifact hashes, and source revision.
8. **PROPOSE** — document the adapter/contract boundary, data flow, threat model, operating owner, and cost.
9. **ADMIT** — only authorized review may promote a candidate to `APPROVED`; passing a local test alone is not canonical admission.
10. **REVALIDATE** — monitor upstream changes, license/security advisories, compatibility, and continued value.

## Status vocabulary

- `UNASSESSED`: listed only; no evaluation evidence recorded.
- `ASSESSING`: inspection is underway and its scope is recorded.
- `SANDBOX_TESTED`: bounded tests ran; no production implication.
- `APPROVED_FOR_ADAPTER`: reviewed for a specified adapter and scope.
- `INTEGRATED`: change exists in a named repository/commit.
- `VERIFIED`: named acceptance checks passed with inspectable evidence.
- `REJECTED` / `DEFERRED`: rationale and date recorded.

Never infer a higher status from a name, README, catalog entry, green unrelated CI, or architectural proposal.

## Evidence record required per candidate

`candidate_id`, `canonical_url`, `upstream_owner`, `repository`, `pinned_revision`, `license`, `capability_tags`, `data_classes`, `required_permissions`, `dependencies`, `security_review`, `sandbox_recipe`, `acceptance_tests`, `test_receipt`, `artifact_sha256`, `decision`, `decision_owner`, `rollback_plan`, `last_reviewed_at`.

## First-pass priority

1. **P0 — foundations:** OpenTelemetry; GitHub Actions; OPA; Sigstore/Cosign; MCP/OpenAPI; isolated test environments.
2. **P1 — durable execution and discovery:** Temporal or current workflow engine comparison; Firecrawl; event/trace replay; retrieval/search.
3. **P2 — model and agent frameworks:** compare current VX/NEXENT runtime against candidate frameworks using one shared benchmark and threat model.
4. **P3 — business operations:** CRM, billing, customer support, and price-monitoring integrations after access scopes and business requirements are documented.

Priority is a proposed evaluation order, not an installation instruction or claim of superiority.

## Safety and preservation rules

- Keep this registry additive; do not overwrite historical indexes or source repositories.
- Avoid duplicate integrations: compare existing contracts, adapters, and repository ownership first.
- Do not copy or redistribute upstream code until its license and obligations are reviewed.
- No production credentials or external side effects in discovery/sandbox stages.
- Missing evidence means `UNKNOWN`, not success.
- No merge, deployment, canonical promotion, or irreversible action without the project's required authorization and rollback path.
