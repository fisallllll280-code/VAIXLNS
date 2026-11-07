# VAIXLNS Integrated Project Order V1

**Date:** 2026-10-28  
**Status:** PROPOSED — documentation plan; not runtime evidence  
**Scope:** Repository federation, canonical indexes, architecture, execution, verification, dashboards, and governed evolution.

## 1. Objective

Establish one traceable navigation and execution order across the VAIXLNS project without silently deleting historical material, conflating proposals with implementations, or claiming services are live without evidence.

## 2. Canonical status vocabulary

Every registered component must carry one explicit status:

- `RECOVERED`: source material located and provenance recorded.
- `CANONICAL`: accepted as the authoritative project definition.
- `PROPOSED`: design or planned change; not implemented evidence.
- `IMPLEMENTED`: code or configuration exists at a pinned revision.
- `VERIFIED`: implementation passed named, reproducible checks with recorded evidence.
- `LIVE_VERIFIED`: authorized runtime evidence confirms the service is operating at a stated time and environment.
- `BLOCKED`: a dependency, identity, permission, or evidence gate is unresolved.
- `DEPRECATED`: superseded with a replacement and preserved lineage; never silently deleted.

## 3. Integrated order of work

### P0 — Inventory and source-of-truth reconciliation
1. Enumerate repositories, default branches, active branches, tags, and relevant commits.
2. Record repository role, ownership, visibility, source revision, and relationship to canonical VAIXLNS.
3. Reconcile the master navigation index, recovery status, archive source index, innovation index, federation index, repository layout, and runtime status.
4. Detect duplicate paths, conflicting definitions, missing links, unpinned sources, and historical gaps.
5. Preserve source material and report uncertainty explicitly.

**Exit gate:** a repository inventory and discrepancy report with source URLs and pinned revisions.

### P0 — Master registry and zero-loss indexes
1. Give every system, tool, innovation, interface, schema, service, and archive item a stable identifier.
2. Store source path, repository and commit, owner, status, dependencies, input/output contract, tests, and evidence links.
3. Keep machine-readable registries authoritative for generated views.
4. Generate indexes deterministically; validate links, identifiers, schema, duplicates, and source provenance.
5. Do not claim complete recovery of historical records until every record has been enumerated and reconciled.

**Exit gate:** repeatable build and validation reports, with unresolved records listed.

### P1 — Architecture and runtime dependency graph
Register the V-Kernel, VX/VV, XV/SCS, SUF, Intelligence Gateway, Collective Intelligence, agents/workers, APIs, databases, ledger, network integrations, simulation engines, and dashboards only where supported by source evidence. For each, distinguish conceptual description, implementation, tested integration, and live service.

**Exit gate:** typed dependency graph with explicit unknowns and blocked edges.

### P1 — Reproducible execution and verification
1. Identify entry points, supported environments, configuration, secrets boundaries, and dependency installation.
2. Run offline/static validation first, then unit tests, integration tests, and authorized runtime checks.
3. Record commit SHA, environment, command, exit code, timestamps, artifacts, and test results.
4. Fail closed when required identity, permission, signature, or evidence is absent.
5. Never interpret a passing static preflight as proof of live connectivity.

**Exit gate:** machine-readable verification receipts linked to exact revisions.

### P1 — Live operations dashboards
Dashboards must consume actual service health, test receipts, event streams, and timestamps. Label mock data and simulation distinctly. Show stale data, missing telemetry, blocked integrations, and last successful verification. A dashboard must not infer a service is live merely because its endpoint is configured.

**Exit gate:** documented data sources and freshness/error states for every displayed live metric.

### P2 — Governed improvement cycle
Observe → diagnose → propose → branch → test → review evidence → human approval → merge/release → monitor → rollback if needed. Automated agents may prepare changes and evidence but may not self-authorize canonical promotion or bypass security and release gates.

**Exit gate:** auditable change history, approval identity, verification evidence, and rollback procedure.

## 4. Required registry fields

Minimum record fields:

- `id`, `name`, `kind`, `status`, `owner`
- `repository`, `path`, `source_revision`
- `purpose`, `inputs`, `outputs`, `dependencies`
- `tests`, `evidence`, `last_verified_at`
- `known_gaps`, `supersedes`, `related_records`

Use `null` or an explicit `UNVERIFIED` value for unknowns; do not fill gaps with guesses.

## 5. Change safety rules

- No destructive cleanup during discovery or reconciliation.
- No repository merge based on name similarity alone.
- No credentials, tokens, or private data in indexes or evidence artifacts.
- No live service claim without timestamped environment-specific evidence.
- No canonical promotion without a reviewable change and passing required gates.
- Preserve historical identifiers and source lineage.

## 6. Deliverables

1. Repository federation inventory.
2. Source and duplicate discrepancy register.
3. Canonical index navigation with broken-link report.
4. Machine-readable component registry and dependency graph.
5. Reproducible test/verification receipts.
6. Runtime dashboard data-source contract.
7. Prioritized gap-closure backlog with owner, impact, dependencies, and acceptance criteria.

## 7. Acceptance criteria

The ordering is ready for adoption when every known repository has a documented role or an explicit unresolved classification; each canonical record has source provenance and status; generated indexes validate deterministically; tests are tied to pinned revisions; and no proposal, static configuration, or simulation is represented as a verified live capability.

**Boundary:** this document is a plan. Creating it does not mean these tasks have been executed, the full historical index has been recovered, or runtime services have been verified.
