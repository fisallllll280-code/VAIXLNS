# VAIXLNS Mother Language and Compiler Gate v1

**Status: SPECIFIED / grammar, compiler and conformance evidence pending.** This is a proposal, not a canonical language release.

## Why the language fabric exists

VAIXLNS needs machine-readable semantics that preserve intent, declared capability, authority, behavior, security policy, simulation, verification, evidence, recovery and evolution across distributed systems. This is a semantic/control layer, not a demand to replace Python, Rust, Go, C++, WASM or other implementation technologies.

Ordinary and new languages coexist under one VAIXLNS semantic contract. Source text alone grants no authority.

## Proposed semantic layers

- **VSL — Specification Language:** intent, requirements, constraints and expected outcomes.
- **VCL — Capability Language:** declared operations, typed inputs/outputs and resource needs.
- **VAL — Authority Language:** identities, permission scope, approvals and delegation rules.
- **VXL — Execution Language:** bounded action plans and deterministic state transitions.
- **VVL — Verification Language:** assertions, invariants, test obligations and acceptance criteria.
- **VEL — Evidence Language:** provenance, hashes, receipts, test results and counterevidence.
- **VML — Modeling/Simulation Language:** simulation assumptions, scenarios, limits and predicted outcomes.
- **VIL — Intelligence Language:** hypotheses, planning proposals and model-generated candidates, always marked as untrusted until verified.
- **VGL — Governance Language:** policy, admission, audit, retention and controlled evolution.
- **Ω-GUARD:** security semantics embedded across the fabric, not an independent authority that bypasses the canonical governance plane.

These names and boundaries must be reconciled against historical indexes before canonical promotion.

## Compiler and execution pipeline

`SOURCE → PARSE → TYPED SEMANTIC IR → IDENTITY/CAPABILITY VALIDATION → POLICY CHECK → SIMULATION/ADVERSARIAL TEST → EVIDENCE CAPTURE → INDEPENDENT VERIFICATION → GOVERNED ADMISSION`

The canonical Semantic IR must have a versioned schema, deterministic canonicalization, explicit unknown-field behavior, source mapping, content digest and reproducible compiler version. Invalid or ambiguous programs fail closed. Compilation does not authorize execution.

## Mandatory security invariants

1. Declared capabilities are intersected with granted permissions; declaration never grants permission.
2. Runtime-observed behavior that exceeds declared or granted capabilities triggers denial, quarantine and an auditable incident.
3. Authority is derived from authenticated identities and policy decisions, never from model text or source annotations alone.
4. Every external action has a typed contract, scoped authorization, deadline, budget, correlation ID and evidence receipt.
5. Simulation and static analysis are not represented as real-world execution.
6. Verification and admission are separate from generation and execution; no worker can approve its own output.
7. Compiler, schemas, policies and adapters are version-pinned and covered by conformance tests.
8. Recovery preserves prior records, lineage and content hashes; conflicts are recorded rather than silently overwritten.

## Minimum implementation sequence

1. Recover and reconcile all existing language/index records; preserve aliases and historical drafts.
2. Define grammar and JSON Schema for VSL intent plus VCL capabilities and Ω-GUARD policy references.
3. Build a deterministic parser/IR validator with golden fixtures and mutation tests.
4. Add negative tests for forged authority, undeclared capability, schema drift, prompt injection, replay and missing evidence.
5. Add a reference backend that emits plans only; no tool execution.
6. Connect the IR to the VX governed supervisor after the runtime/action-envelope contract is verified.
7. Promote language specifications only through canonical review and reproducible evidence.

## Non-goals

- No claim that these language layers are already compiled or executed in production.
- No replacement of canonical `project.genome` or `Ω.000`.
- No autonomous permission escalation, self-approval, direct unrestricted tool access or automatic production publishing.
