# Ω Memory–Task–Innovation Kernel v1

**Parent:** VAIXLNS  
**Canonical authority:** `project.genome::v1.0.0` / `Ω0_GENESIS_CORE`  
**Index:** Ω.000 (no mutation from this branch)  
**State:** IMPLEMENTED in a proposal branch; runtime validation pending  
**Execution boundary:** local planning and memory primitives only; external effects disabled

## Why this kernel exists

The engineering system must be able to recover the context of prior work, distinguish decisions from hypotheses, compile a request into dependency-aware tasks, and propose new engineering approaches that can be tested. It must not rely on untraceable chat recollection or treat generated ideas as verified facts.

This implementation is additive. It must be reviewed against the existing Permanent Engineering Memory (#58), Ω Mind / engineering fabric (#78), and specialist orchestration work (#90) before any merge. It does not replace those systems, change the canonical genome, edit Ω.000, or delete/rename original records.

## Implemented local primitives

### 1. Append-only, hash-linked memory ledger

Each record stores:
- stable record ID, UTC timestamp, type, content, source reference, epistemic state, tags, related IDs;
- previous record hash and current SHA-256 digest;
- deterministic integrity verification and a fail-closed append/retrieval path if a mismatch is found.

**Important limitation:** a hash chain detects edits and reordering when compared with a trusted head. It does not prove truth, protect against a complete rewrite by an attacker who can replace the entire ledger and trusted head, or provide multi-writer concurrency control. Those require external signatures, protected checkpoints, and locking/transaction design.

### 2. Deterministic memory retrieval

The initial retrieval implementation ranks records by lexical token overlap and returns the matched record, score, source, tags, and retrieval method. It is reproducible and inspectable but is not semantic search and makes no guarantee of recall. Embeddings, graph expansion, contradictory-memory detection, time-aware ranking, and relevance benchmarks are future work.

### 3. Dependency-aware task planning

The task planner validates unique IDs, required goals, known dependencies, and acyclic task graphs. It returns a deterministic topological order, exposes blocked dependencies, and carries evidence requirements and risk labels. It does not execute commands or call remote systems.

### 4. Evidence-gated task completion

A task cannot transition to `DONE` without every required evidence type. Each evidence item must contain a source reference and digest. This checks the presence of evidence pointers, not the truth or adequacy of the evidence; a separate verifier must validate artifact content and test scope.

### 5. Innovation hypothesis generation

The kernel emits four explicitly unverified, testable hypotheses:
- evidence-linked memory retrieval;
- dependency-aware task execution;
- counterexample-driven engineering synthesis;
- memory-to-recovery replay.

Each hypothesis includes acceptance-test ideas and the memory IDs it was derived from. This is a deterministic seed catalog, not an autonomous discovery claim or proof of novelty. A literature/prior-art review and measurable baseline are required before claiming originality.

## Safety and governance

- No shell, network, cloud, GitHub, or production effects are invoked by this kernel.
- No credentials are read or stored.
- No component is promoted to `VERIFIED`.
- No canonical source or Ω.000 record is mutated.
- Failed integrity checks stop writes and retrieval.
- Unknown dependencies and cycles fail closed.
- Task completion requires evidence pointers.
- A passing unit test proves only the tested behavior in that environment.

## Test plan

Focused tests cover hash-chain integrity, tamper detection, fail-closed append, deterministic ranking, dependency ordering, cycle/missing-dependency rejection, legal task transitions, evidence-gated completion, and proposal-state boundaries. CI is configured; the workflow result must be inspected on this exact commit before reporting a pass.

## Next engineering increments

1. Reconcile data model and interfaces with the Permanent Engineering Memory, Ω Mind, and specialist orchestrator branches.
2. Add signed checkpoints, concurrency-safe append, schema versioning, and retention/recovery policy.
3. Add hybrid retrieval and evidence graph with contradiction surfacing, exact source spans, and benchmarked Recall@k/MRR.
4. Add task event log, idempotency keys, retry policy, checkpoint/resume, compensation, approval gates, and explicit effect receipts.
5. Add adversarial/mutation tests and independently authored acceptance tests.
6. Add memory compaction only as a derived view; never delete or silently overwrite original records.
7. Connect to VX only through an explicit capability contract and sandbox. Remote or consequential actions remain disabled until separate policy, security, and test gates pass.
8. Propose Ω.000 registration only after review, CI evidence, integration tests, and a canonical change request.

## Required benchmark before stronger claims

- Retrieval: Recall@5/10, MRR, citation/source-link accuracy, contradiction recall, stale-record rate.
- Recovery: replay agreement, missing-context detection, recovery time, duplicate task/effect rate.
- Planning: valid-DAG rate, cycle detection, blocked-task correctness, determinism across repeated runs.
- Innovation: baseline improvement, independent test pass rate, counterexample discovery, integration cost, prior-art coverage.
- Security: tamper detection, untrusted memory injection, secret leakage, unauthorized side-effect denial.

All numbers must be measured against a pinned dataset and environment. No benchmark result is claimed by this proposal.
