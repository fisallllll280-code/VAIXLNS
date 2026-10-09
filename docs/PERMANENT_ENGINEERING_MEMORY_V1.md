# Permanent Engineering Memory (PEM) v1

Status: **SPECIFIED; implementation is an initial local-ledger slice, not a distributed production service.**

## Objective

Make each engineering cycle start from the best verified state already available, preserve what was learned, and require evidence before claiming that a new design is deeper or better than its predecessor.

This capability follows the existing VAIXLNS principles: Genome First, Event First, Knowledge First, Governance First, Determinism First, Verification Before Execution, and Controlled Evolution. Existing epistemic states remain authoritative.

## Components

1. **Capture adapter** — imports discoveries, decisions, source references, code revisions, tests, failures, benchmarks, and operator-approved conclusions.
2. **Provenance envelope** — binds each record to repository, revision, path, source content SHA-256, actor where known, and observation time.
3. **Append-only memory ledger** — stores immutable JSONL records with a deterministic record hash and previous-record hash. Corrections are new records with lineage.supersedes; historical claims are not rewritten.
4. **Retrieval and lineage** — begin with deterministic lexical retrieval; semantic/vector retrieval and cross-repository federation remain adapter work, not claimed in this slice.
5. **Evidence and promotion gate** — keeps proposal, specification, implementation, verification, partial evidence, missing items, and conflicts distinct.
6. **Engineering comparison** — a candidate claiming improvement must name its predecessor, baseline, metrics, test conditions, counter-evidence, and reproducible evaluation. Newer or more complex does not mean better.
7. **Governance boundary** — memory may inform plans but cannot grant permissions, execute external actions, promote itself, or override the sovereign constitution.

## Record contract

The canonical schema is schemas/permanent-engineering-memory-record.schema.json.

Each record contains:
- stable record_id, memory_type, subject, summary, and lifecycle/epistemic states;
- provenance with repository, revision, path, and source content digest;
- evidence references with SHA-256 digests;
- verification method/result and reproduction command where applicable;
- lineage (derived_from, supersedes, related);
- ledger-chain fields (previous_record_hash, record_hash).

Do not store credentials, API tokens, private keys, session tokens, or unnecessary personal data. Store a secret-manager reference only where authorized; never store secret values.

## Promotion rules

- PROPOSAL means an idea exists; it is not a capability.
- SPECIFIED means the contract and acceptance criteria are explicit; it is not proof of implementation.
- IMPLEMENTED means code or a concrete artifact exists; it is not proof of correctness or deployment.
- VERIFIED requires a passing verification result, at least one digest-bound evidence item, and a reproduction command.
- PARTIAL, MISSING, and CONFLICT remain visible and must not be silently promoted.
- RECOVERED records reconstructed knowledge and must retain recovery provenance; it is not equivalent to independently verified truth.
- A record cannot grant itself authority. Canonical promotion remains an explicit governance decision supported by verified evidence.

## Engineering-depth gate

For a proposed successor to claim improvement over a predecessor, require:
1. a stable predecessor record or explicit no-baseline declaration;
2. an objective, measurable acceptance criterion;
3. a reproducible baseline and candidate evaluation under comparable conditions;
4. regression, security, failure-mode, and resource-cost checks appropriate to the change;
5. counter-evidence and known limitations;
6. an explicit decision: ACCEPT, REJECT, or INCONCLUSIVE, with authority and evidence references.

If no baseline or reproducible evidence exists, the outcome is INCONCLUSIVE, not best-in-the-world.

## Integrity and operational limits

The Python ledger helper is a single-writer local JSONL baseline with fsync and hash-chain verification. A hash chain is tamper-evident, not tamper-proof: an administrator able to rewrite the whole file can recompute hashes. Production deployment still needs protected storage, access control, backups, restore drills, concurrency coordination, audit retention, and independent evidence anchoring.

Do not use this local ledger as the sole source of truth for cross-repository or multi-node coordination. Those require a governed backend and verified integration tests.

## Initial implementation

- scripts/permanent_engineering_memory.py: validation, append, integrity verification, deterministic lexical search.
- tests/test_permanent_engineering_memory.py: core contract tests.
- schemas/permanent-engineering-memory-record.schema.json: interchange schema.

Run tests from the repository root with:

    python -m unittest tests.test_permanent_engineering_memory -v

This release does not automatically close, merge, or rewrite existing pull requests. Existing work must be classified by evidence and reviewed before any closure action.
