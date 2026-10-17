# VAIXLNS Ω — Global Research System V1

**State:** SPECIFIED  
**Scope:** Research architecture and staged implementation contract  
**Canonical home:** VAIXLNS  
**Authority:** This document is a proposal/specification. It does not claim live global crawling, external data-provider access, verified scientific discoveries, or production deployment.

## 1. Mission

Build a provenance-first research fabric that discovers, normalizes, relates, evaluates, simulates, and operationalizes knowledge from authorized sources while preserving uncertainty, source lineage, privacy, licensing, and reproducibility.

The system must distinguish *finding a claim* from *validating a claim*, and *generating an idea* from *demonstrating novelty or correctness*.

## 2. Research pipeline

`SOURCE_DISCOVERY → INGESTION → NORMALIZATION → ENTITY_RESOLUTION → KNOWLEDGE_GRAPH → HYPOTHESIS → EVIDENCE_REVIEW → REPLICATION_OR_SIMULATION → SYNTHESIS → HUMAN_OR_POLICY_GATE → CONTROLLED_INTEGRATION → MONITORING → EVOLUTION`

Each stage emits versioned records and explicit failure outcomes. Failed or ambiguous items are retained as `UNRESOLVED`, `CONFLICT`, `INSUFFICIENT_EVIDENCE`, or `REJECTED_WITH_REASON`; they are never silently dropped.

## 3. Core agents

| Agent | Responsibility | Required output |
|---|---|---|
| Discovery | Search approved APIs, repositories, papers, standards, patents and datasets | Source candidates + query provenance |
| Retrieval | Fetch authorized content and preserve exact source location | Immutable source snapshot or content hash |
| Extraction | Extract claims, entities, equations, methods, requirements and limitations | Atomic claim/evidence records |
| Ontology | Resolve names, aliases, versions and entity types | Entity links with confidence and alternatives |
| Relation | Find dependency, contradiction, complementarity and lineage candidates | Typed edges with supporting evidence |
| Evidence auditor | Grade evidence quality, freshness, replication and conflicts | Evidence matrix; no unsupported promotion |
| Novelty analyst | Compare a candidate with indexed prior art and close variants | Similarity map + search coverage + unresolved gaps |
| Research planner | Convert questions into falsifiable hypotheses and experiments | Preregistered plan, metrics, controls, stop rules |
| Simulation | Run sandboxed models or tests where executable assets exist | Inputs, environment, outputs, seeds, limitations |
| Synthesis | Combine supported results into a reviewable design or report | Traceable synthesis and alternatives |
| Safety/governance | Enforce privacy, licensing, security, cost and approval boundaries | Allow, constrain, quarantine, or deny decision |
| Integration | Propose patches or adapters; never self-merge protected changes | Patch, tests, rollback plan, review request |
| Observer | Track drift, failures, stale evidence and regressions | Alerts and versioned change records |

Agents are roles, not an assumption that every capability already exists or runs autonomously.

## 4. Research memory and atomic record

Every source, claim, hypothesis, experiment, result, design, and decision must have stable identity and provenance. Minimum fields:

- `uid`, `record_type`, `title`, `aliases`, `domain`, `language`
- `source_id`, `source_uri`, `source_location`, `retrieved_at`, `content_hash`
- `parent`, `children`, `lineage`, `relations`, `supersedes`
- `claim`, `assumptions`, `method`, `limitations`, `counterevidence`
- `evidence_items`, `confidence_rationale`, `replication_status`
- `license`, `privacy_class`, `security_class`, `retention_policy`
- `state`, `reviewer`, `version`, `created_at`, `updated_at`

Confidence is not proof. Store confidence with its rationale and method; never infer it from source count alone.

## 5. Evidence and lifecycle states

- `DISCOVERED`: source candidate located.
- `INGESTED`: source snapshot or verifiable hash retained.
- `EXTRACTED`: structured records emitted with source locations.
- `CORRELATED`: a relationship candidate exists; not yet validated.
- `SUPPORTED`: evidence meets a defined, domain-appropriate criterion.
- `REPLICATED`: an independent replication or reproduction succeeded under recorded conditions.
- `SPECIFIED`: design or behavior described, not implemented.
- `IMPLEMENTED`: code or mechanism exists in a known revision.
- `VERIFIED`: a defined test/proof passed and the evidence is attached.
- `CONFLICT`, `UNRESOLVED`, `STALE`, `REJECTED`: explicit non-success states with reasons.

Transitions require declared preconditions and append-only event records. No language model output alone can authorize `VERIFIED`, `REPLICATED`, or `CANONICAL`.

## 6. Global source strategy

Use source adapters in priority order:
1. Public scholarly indexes and publisher/open-access APIs.
2. Standards bodies, official technical documentation and public specifications.
3. Public code hosts, issue trackers, release notes and reproducible build artifacts.
4. Patent and prior-art search services where permitted.
5. Public datasets and government/institutional data catalogs.
6. User-provided repositories, files and conversations only through explicitly authorized connectors.

Respect provider terms, rate limits, robots/access controls, copyright, license conditions, privacy, and retention requirements. No bypass of access controls. Record query, time, provider, filters, pagination, errors, and coverage boundaries. “Global” means a multi-source architecture with measured coverage—not a claim that every source on the internet has been searched.

## 7. Novelty and innovation protocol

1. Form a precise candidate claim and define the relevant domain.
2. Search exact terms, aliases, translations, taxonomies, citations, and neighboring disciplines.
3. Search code, papers, patents, standards, historical VAIXLNS records, and known variants.
4. Build a prior-art matrix: overlap, difference, date, source, strength, and missing coverage.
5. Label novelty as `UNASSESSED`, `POSSIBLE`, `CONTRADICTED_BY_PRIOR_ART`, or `REVIEWED_WITH_SCOPE`.
6. Require expert review for consequential claims. Never promise absolute novelty from incomplete search coverage.

## 8. Research execution and safety gates

- Default to read-only collection and isolated sandboxes.
- Pin dependencies, record environment/configuration, use deterministic seeds where feasible, and preserve raw outputs.
- Do not execute retrieved code or instructions as trusted content.
- Require explicit permission for external writes, deployment, spending, credential use, or changes to protected branches.
- Require tests, threat review, rollback, and human approval for production or safety-critical changes.
- Separate secrets from logs; minimize personal data; preserve audit events.
- Use budgets, timeouts, concurrency limits, retry ceilings, and a kill switch.
- Quarantine malicious, malformed, unlicensed, or provenance-deficient material.

## 9. Integration with VAIXLNS

- **ZERO-LOSS INDEX:** canonical routing and source/lineage preservation.
- **Ω.000 Master Index:** stable navigation and canonical identity resolution.
- **VX:** sandboxed execution, replay, verification and runtime observation when available.
- **XV:** intelligence and synthesis bridge, subject to evidence gates.
- **VV:** discovery and knowledge interface.
- **ARC-X:** evidence, counterevidence, proof obligations and intent-to-reality review.
- **SEC/Governance:** policy, permission, provenance, privacy and approval controls.

These are integration boundaries, not proof that each named component is fully implemented or connected.

## 10. Metrics

Measure at minimum:
- source coverage by provider, domain, language, date and access class;
- retrieval success, freshness, hash integrity and provenance completeness;
- extraction precision/recall on a labeled benchmark;
- entity-resolution precision and unresolved/false-merge rates;
- citation support rate, contradiction detection and reviewer agreement;
- replication success and reproducibility failures;
- novelty-search coverage and false-novelty rate;
- time/cost per accepted finding and per verified result;
- security/privacy incidents, policy denials and rollback success;
- index coverage, lineage gaps and records with no source.

Every metric needs a definition, denominator, owner, window, and data-quality check.

## 11. Staged delivery

**R0 — Contract:** schemas, lifecycle, threat model, provider policy and test fixtures.  
**R1 — Local research core:** ingest user-authorized files/repositories; produce searchable atomic claims and citations.  
**R2 — Source adapters:** add approved APIs one at a time with rate limits and recorded coverage.  
**R3 — Evidence graph:** contradiction, dependency, lineage and claim-to-source navigation.  
**R4 — Experiment workbench:** reproducible notebooks/tests/simulations in isolated environments.  
**R5 — Multi-agent orchestration:** bounded tasks, shared event log, budget limits, failure recovery and independent audit.  
**R6 — Controlled engineering loop:** patch proposals, CI, review gates, staged rollout and rollback.  
**R7 — Continuous research operations:** freshness/drift monitoring, scheduled rechecks, evaluation sets and published coverage reports.

Each stage is admitted only when its acceptance tests pass. A written specification is not a running service.

## 12. Initial acceptance criteria

- Every extracted claim links to at least one exact source location or is marked unsupported.
- Re-running ingestion over unchanged inputs yields stable identities and deterministic outputs.
- Source updates create revisions; prior snapshots remain addressable.
- Conflicts and counterevidence are first-class records.
- Missing adapters and inaccessible sources appear in coverage reports.
- No silent source deletion, silent entity merge, or unsupported status promotion.
- CI tests tampering, malformed input, duplicate ingestion, partial failures, retries and rollback.
- No external write or production deployment occurs without an authorized gate.

## 13. Current status

This document establishes the architecture contract only. Before claiming a functioning global research system, implement the schemas, one end-to-end source adapter, retrieval snapshots, evidence-linked claims, evaluation fixtures, audit logging, and CI. Report the tested source set and known gaps explicitly.
