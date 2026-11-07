# Ω Memory–Task–Innovation Kernel (MTIK) v1

**Parent:** VAIXLNS  
**Canonical authority references:** project.genome::v1.0.0 / Ω0_GENESIS_CORE  
**Master index:** Ω.000 (read-only; no mutation in this change)  
**State:** PARTIAL — reference implementation with focused CI pending  
**Execution boundary:** deterministic local operations; no external side effects

## Engineering intent

MTIK connects four steps in a single reproducible cycle:

1. Verify an ordered Permanent Engineering Memory (PEM) snapshot and recover context with explainable lexical matching.
2. Convert explicitly supplied engineering gaps into bounded innovation hypotheses tied to any matching memory records.
3. Compile candidate research/validation tasks into a deterministic directed acyclic graph, surfacing missing dependencies, capabilities, and memory prerequisites.
4. Allow only a pre-registered handler to run under caller-supplied capability grants; hold completion until provenance and independent evidence obligations are satisfied.

This is a child subsystem under VAIXLNS, not a new canonical root and not an autonomous general-purpose agent.

## Existing engineering work: integrate, do not duplicate

- PR #58, Permanent Engineering Memory, specifies an append-only record ledger and lexical retrieval. It is still an unmerged proposal branch; this MTIK code does not assume its module is present in main and does not write to its ledger.
- PR #78, Ω Mind / engineering fabric, specifies a larger governed planning fabric. MTIK provides a narrow memory-to-innovation-to-task cycle, not a replacement.
- PR #90, the specialist orchestration kernel, defines more complete identity, capability, authority, quarantine, independent verification, and admission transitions. MTIK does not launch remote agents and must be adapted to that kernel before consequential execution.
- The existing Innovation Master/Operation Index remains the catalog of record. MTIK does not overwrite those indexes or generate canonical IDs in them.
- ARC-X remains the independent evidence/admission boundary.

These PRs are not merged dependencies. The reference slice is independently testable; future integration needs contract checks against exact reviewed commits.

## Executable components

### scripts/omega_memory_task_kernel.py

- Canonical JSON and SHA-256 fingerprints.
- Verification of a complete ordered PEM snapshot, including unique record IDs, previous-record links, and record hashes.
- Deterministic lexical context recovery with matched terms, provenance, evidence references, score explanation, and an explicit no-match response.
- Deterministic topological sorting of task contracts; duplicate IDs, missing dependencies, and cycles fail closed.
- Explicit task blockers for missing capabilities and unavailable required memory IDs.
- Dry-run-first invocation of a caller-registered handler.
- External effects are always rejected. A sandbox mutation is held unless an explicit decision reference is supplied.
- Completion evaluator lists proof gaps and checks producer/verifier separation. It is a decision helper, not an identity service or canonical promotion authority.

### scripts/omega_engineering_cycle.py

- Runs memory recovery first from the supplied complete snapshot.
- Derives candidate hypotheses from explicit gap records; IDs and digests are deterministic.
- Links candidates to retrieved memory records when lexical terms overlap.
- Always sets novelty to UNASSESSED and originality to NOT_CLAIMED. This module does not perform prior-art research itself.
- Generates research/validation tasks with acceptance criteria and dependency links, then creates the deterministic plan and cycle digest.

### schemas/omega-memory-task-innovation.v1.schema.json and registry/omega/proposals/omega-memory-task-innovation-kernel.v1.json

Define the proposal contract, allowed state vocabulary, integration points, evidence limits, and non-mutating authority boundary. The schema is parsed and the manifest is structurally validated in CI; unless an explicit JSON Schema implementation is invoked, that step must not be described as a full JSON Schema conformance test.

## Example calling pattern

- Supply a complete ordered memory snapshot from a trusted PEM reader. A filtered search result cannot validate a full previous-hash chain.
- Supply an engineering goal and gap specifications with acceptance criteria.
- Supply only capabilities actually granted to the requesting principal.
- Inspect recovered context and the plan. A READY status means the plan prerequisites are present; it is not permission to deploy.
- Keep dry_run true by default. A caller may invoke an explicitly registered handler only after the appropriate capability checks. External effects remain disabled in this kernel.

The caller-provided handler registry is trusted code. This Python module does not isolate a handler in an OS/container sandbox and cannot prove that code labeled READ_ONLY has no side effects. For that reason, handler implementation, revision pinning, isolation, and policy enforcement remain external proof obligations.

## Integrity and truth boundaries

- A hash chain is tamper-evident relative to a trusted head, not tamper-proof. An actor able to rewrite the whole ledger and trusted head can recompute hashes.
- Lexical matching is deterministic but is not semantic understanding and does not guarantee high recall.
- Memory provenance identifies origin; it does not prove a claim is true.
- Scores are retrieval priorities only; they never update epistemic state.
- Generated candidates are research hypotheses. Novelty and superiority require prior-art review, a measured baseline, source traceability, and independent reproduction.
- Handler results are marked NOT_VERIFIED. Passing a unit test does not prove production operation.
- No remote agent, cloud service, Microsoft provider, or cross-repository memory store is connected by this proposal.
- project.genome and Ω.000 remain untouched. No canonical promotion is performed.

## Focused acceptance gates

1. Tampered memory and broken hash links fail closed.
2. Retrieval identifies source revisions, evidence references, and matched terms; no-match does not fabricate content.
3. Missing dependencies and cyclic plans are rejected.
4. Missing capability or memory prerequisites produce BLOCKED tasks.
5. Identical inputs produce deterministic plans, candidate IDs, and cycle digests.
6. Dry-run does not invoke handlers.
7. Missing handler/capability and handler exceptions cannot be represented as success.
8. External effects are rejected.
9. Completion remains on HOLD when proof fields are missing or producer/verifier identities are equal.
10. CI passes on the exact PR head before this reference behavior is called tested.

## Next integration increments

1. Align the adapter contract against reviewed/merged PEM, Ω Mind and specialist orchestration changes.
2. Add a read-only adapter that captures a full ledger snapshot and rejects stale or partial snapshots.
3. Persist task event receipts through the governed event/evidence store with task IDs, idempotency, failure, retry and resume semantics.
4. Add semantic retrieval and graph expansion only behind measured lexical baselines, provenance, contradiction surfacing, and recall benchmarks.
5. Test stale revisions, memory injection, cycles, duplicate task dispatch, interrupted execution, and handler boundary violations.
6. Add a real isolated executor only after OS/container isolation, scoped capabilities, idempotency, rollback, and auditable authority decisions are tested.
7. Propose canonical Ω.000 registration separately after review and source-bound CI evidence.

## Required benchmark before stronger claims

- Retrieval: Recall@5/10, MRR, source-link accuracy, contradiction recall, stale-record rate.
- Recovery: missing-context detection, replay agreement, retrieval time, loss rate.
- Planning: valid-DAG rate, cycle/missing-dependency detection, determinism.
- Innovation: prior-art coverage, measured baseline improvement, independent test pass rate, counterexample discovery, integration cost.
- Security: tamper detection, poisoned-memory resistance, secret leakage tests, unauthorized side-effect denial.
- Operations: interrupted-run recovery, duplicate-task handling, resource budget enforcement, audit completeness.

All measurements must identify a pinned dataset/environment. No benchmark result or production-readiness claim is made by this proposal.