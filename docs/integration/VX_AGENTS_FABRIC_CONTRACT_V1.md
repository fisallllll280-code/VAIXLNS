# VX Agents Fabric — Canonical Integration Contract v1

Status: PROPOSED_NOT_ADMITTED  
Owning authority: VAIXLNS  
Execution boundary: VX  
Discovery/design boundary: NEXENT

## Purpose

Provide a versioned specialist-agent fabric with three routed teams (research intelligence, financial intelligence and engineering intelligence) plus an Ω Parent Multi-Mind council. The fabric coordinates work; it does not replace canonical VAIXLNS identity, Nexus, proof, governance or release authority.

## Routing contract

Every task must carry workflow ID, task ID, agent role/version, goal, stage, input artifact IDs, required output schema, authority scope, budget, deadlines and evidence obligations. Providers return an artifact carrying its identity, exact agent/version, input lineage, evidence references, limitations and content digest.

The coordinator may automatically route routine research, analysis, design, sandbox implementation, tests and recovery steps only through configured adapters. If an adapter is missing, its status is NOT_CONFIGURED and the workflow remains HOLD.

## Parent multi-mind contract

Five separately connected reviewers assess:
- systems architecture and constraints;
- research provenance, contradictions and uncertainty;
- financial viability, costs and downside risk;
- adversarial/security failures;
- proof obligations and reproducibility.

A reviewer is recorded as reviewed only if its provider actually ran and returned a valid review. Missing review, failed hard gate, absent evidence or invalid event chain cannot be overridden by consensus. Parent output is a candidate recommendation only.

## Version and provenance contract

- Role IDs are stable; each implementation version is immutable.
- Multiple versions coexist; exact versions are pinned for reproducible releases.
- Aliases cannot collide across canonical roles.
- No source record is silently overwritten or merged.
- All artifacts link to the input artifacts from which they were derived.
- Provider/model IDs, tool versions and environment fingerprints must be added when adapters become real.

## Financial domain restrictions

Financial intelligence can research markets, build scenarios, estimate unit economics, evaluate costs, propose pricing and identify compliance questions. It cannot move money, access accounts by default, make an executable trade or represent its result as licensed financial advice. Any later transaction capability requires a separate licensed/authorized integration contract and the applicable approvals.

## Production boundary

The default adapter policy denies canonical mutation, production deployment, destructive source changes, payments, fund transfers, trades and irreversible publishing. No role is production-admitted by this specification alone.

## Required admission evidence

The candidate must pass the VAIXLNS universal integration lifecycle: quarantine; identity/contract inspection; isolated sandbox; functional and negative tests; failure/recovery; replay; independent verification; fresh proof; causal-impact/resource review; explicit authority; admission; continuous revalidation.

The present repository has a green unit-test workflow on its feature branch. Live provider connectivity, durable VAIXLNS Event/Ledger binding, sandbox containment, cross-repository replay, Ω-RAC proof integration and production admission remain unproven and are not to be marked complete.

## Recovery and information-loss prevention

Persist checkpoints outside process memory. Every exception, timeout, missing adapter, conflict, model/version mismatch and verification failure must be emitted to an append-only event ledger with a stable task ID and artifact lineage. Resume from the last verified checkpoint; never reconstruct missing facts silently. A durable VAIXLNS ledger adapter and replay tests are required before production operation.


## Provider adapter status update — 2026-10-09

The implementation in \`vx-agents-fabric\` main now includes an **opt-in OpenAI-compatible chat adapter** for specialist roles and parent minds. It supports family-level defaults, role overrides and exact role/version overrides, plus explicit bindings for each parent mind. See [the provider binding implementation](https://github.com/fisallllll280-code/vx-agents-fabric/tree/main/src/vx_agents_fabric/providers).

This means provider binding code is available; it does **not** mean provider endpoints, model names, credentials or live inference are connected in this VAIXLNS deployment. The adapter is not itself a browser/search engine, GitHub repository client or code sandbox. Those integrations need separate, least-privilege adapters and must pass the universal integration gate.

Current disposition remains \`PROPOSED_NOT_ADMITTED\`. The durable canonical Event/Ledger binding, crash-safe replay, full live integration verification, fresh proof and production admission remain outstanding. Missing model configuration must yield \`NOT_CONFIGURED/HOLD\`, never fabricated research or a claimed success.
