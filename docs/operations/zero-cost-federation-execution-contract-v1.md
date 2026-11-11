# VAIXLNS Zero-Cost Federation Execution Contract

- Contract ID: VX-ZCF-2026-11-11-001
- State: CONTRACTED / IMPLEMENTATION NOT STARTED
- Base repository: fisallllll280-code/VAIXLNS
- Base branch: main
- Base commit: 73e5419ee34cf6d0020aeb9eeeb66275d462df8e
- Work branch: vx/zero-cost-federation-2026-11-11
- Cost ceiling: USD 0 / SAR 0
- Execution mode: isolated, evidence-first, simulation-first

## Objective

Prepare a complete, non-duplicative integration and verification program for the existing VAIXLNS ecosystem. Reuse existing implementations; do not create parallel ghost systems. This contract covers VAIXLNS, VAIXLNS-unified, VX-runtime, NEXENT, VAIXLNS-Intent-to-Reality, and documented VLNS integration boundaries.

## Protected invariants

1. Never modify `project.genome` or the canonical `registry/omega/omega-000-master-index.json` (`Ω.000`).
2. Never delete, overwrite, rename, or rewrite historical assets or provenance.
3. No writes to `main`; all changes remain on the isolated work branch until independently reviewed and explicitly authorized.
4. No merge, deployment, publication, external connection, paid API call, subscription, credit purchase, or spending.
5. No secrets, tokens, credentials, private user data, or external service payloads in source, logs, prompts, or evidence.
6. Do not treat documentation, static manifests, generated mock data, or an agent claim as runtime proof.
7. Unknown/inaccessible is not missing. Classify each capability as EXISTS_AND_TESTED, EXISTS_NOT_TESTED, PARTIALLY_EXISTS, MISSING, or UNKNOWN.
8. No proof = no commit to protected branches; no self-approval.

## Zero-cost boundary

Permitted: GitHub repository reads and isolated branch documentation/code changes using already-authorized free repository access; local/offline deterministic checks that require no paid compute or external services.

Forbidden: Replit Agent runs until the account's remaining included allowance and billing safeguards are confirmed; paid model/API calls; hosted compute; paid databases; paid deployment; usage-based external services; automatic top-ups; any action that could trigger a charge when the zero-cost condition cannot be guaranteed.

If a tool cannot prove that an operation stays within the zero-cost boundary, stop before invoking it and report COST_UNKNOWN / BLOCKED.

## Work sequence and acceptance gates

### G0 — Repository reality and provenance inventory
- Record current default branches and immutable base commit SHAs for all in-scope repositories.
- Inventory existing architecture, contracts, schemas, agents, memory, simulation, security, recovery, CI, tests, and deployment configuration.
- Read all applicable repository instructions before editing.
- Record exact paths and evidence references.
- Preserve the canonical genome and omega index hashes.

Acceptance: inventory is source-backed; unknowns are explicitly marked; no protected asset changed.

### G1 — Capability and duplication map
- Map each capability to its existing canonical implementation and owning repository.
- Identify duplicate implementations, adapters, and missing interfaces.
- Reuse existing VX control plane, cognitive fabric, VLNS activation bridge, federation preflight, Ω-Arena audit, and continuity infrastructure where they exist.
- No new subsystem is proposed until overlap analysis is complete.

Acceptance: each capability has one proposed owner, contract, and evidence state.

### G2 — Integration contracts
- Define typed, fail-closed contracts for repository identity, tool invocation, agent identity, memory boundaries, event provenance, policy decisions, and evidence receipts.
- Preserve the NEXENT discovery/design/proposal boundary and VAIXLNS canonical governance boundary.
- Require explicit authorization for privileged actions.

Acceptance: schemas validate offline and reject malformed, unknown, or unauthorized actions.

### G3 — VX runtime and agent fabric
- Reconcile role catalogs, tool envelopes, policy evaluators, activation gates, and runtime handlers.
- Ensure every tool-specific agent is subordinate to the sovereign VX policy layer.
- Keep unconfigured providers disabled; never fabricate credentials or live connectivity.

Acceptance: deterministic offline tests cover allow/deny, fail-closed, replay, idempotency, and policy bypass attempts.

### G4 — Memory, knowledge, and innovation
- Separate operational memory from innovation/research memory with provenance and retention rules.
- Preserve source identity, hashes, timestamps, lineage, and uncertainty.
- Keep candidate innovations in proposal/quarantine until evidence and independent review exist.
- No automatic licensing, promotion, or external publication.

Acceptance: traceable source-to-claim links and reproducible evaluation fixtures.

### G5 — Simulation and verification
- Reuse existing simulation and test harnesses.
- Add only missing deterministic tests after gap analysis.
- Cover unit, integration-contract, regression, security-boundary, replay, recovery, and adversarial cases.
- Record exact commands, environment, exit codes, and outputs. Do not claim execution if not run.

Acceptance: all executed checks have captured evidence; unexecuted checks remain NOT_RUN.

### G6 — TITAN FORTRESS and recovery
- Audit backup, snapshot, hash, restore, anti-tamper, access-control, and incident evidence.
- Use non-destructive restore drills in disposable/offline fixtures only.
- No destructive repair, live device operation, or secret rotation.

Acceptance: restore is considered verified only after an isolated restore and checksum comparison succeed.

### G7 — Interfaces and operator experience
- Reuse existing VAIXLNS-unified interfaces and control-plane screens.
- Surface status distinctions: PROPOSED, IMPLEMENTED, RUNNING, VERIFIED, BLOCKED, NOT_RUN, UNKNOWN.
- UI must never imply a service is live based only on static metadata.

Acceptance: accessible, responsive UI backed by actual read-only status data or clearly labeled fixtures.

### G8 — Independent review and promotion
- Independent reviewer inspects contract, diff, test evidence, security boundaries, and rollback.
- Any inconclusive or missing evidence blocks promotion.
- No merge to main, deployment, external integration, or spending without separate explicit approval.

Acceptance: review verdict APPROVED; user authorization recorded; all gates satisfied.

## Initial allowed paths

- `docs/operations/zero-cost-federation-execution-contract-v1.md` (this contract only)
- Additional paths require a versioned task contract and explicit allowlist update before implementation.

## Initial forbidden paths and operations

- `project.genome`
- `registry/omega/omega-000-master-index.json`
- All history, archive, provenance, and recovery source records
- Main/default branches
- Secrets, credentials, billing settings, deployments, external accounts
- Deletion, force push, history rewrite, merge, publish, paid execution

## Execution limits

- Maximum execution turns per task: 20
- Maximum wall time per task: 600 seconds
- Maximum spend: USD 0 / SAR 0
- If cost cannot be measured or guaranteed: STOP, report COST_UNKNOWN.

## Rollback and recovery

No destructive rollback is permitted. Preserve branch state, commits, diffs, and evidence. If a change is invalid, stop and create a forward corrective change on the isolated branch after review; never reset or rewrite history.

## Current evidence

- VAIXLNS repository metadata read; default branch is main.
- Main base commit recorded above.
- `project.genome` read and its canonical hash recorded in the repository; file is protected and untouched.
- README identifies `registry/omega/omega-000-master-index.json` as `Ω.000`; it is protected and untouched.
- Existing architecture already documents federation preflight, Ω-Arena audit, VX sovereign tool control, VX cognitive fabric, VLNS activation bridge, and VX/VLNS index continuity. These must be inspected and reused rather than duplicated.
- No runtime tests were executed by this contract operation.
- No Replit Agent, paid API, deployment, external connection, or hosted compute was invoked.

## Lifecycle

CONTRACTED -> ISOLATED -> IMPLEMENTED -> TESTED -> INDEPENDENTLY_VERIFIED -> AUTHORIZED -> PRESERVED

Current state: CONTRACTED. No implementation or runtime capability is claimed.
