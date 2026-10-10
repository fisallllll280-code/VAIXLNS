# Evidence-Gated Self-Evolution Governance v1

## State

- Specification status: SPECIFIED
- Runtime implementation status: PARTIAL
- Production deployment status: NOT DEPLOYED
- Automatic merge status: DISABLED
- External side effects: DISABLED unless explicitly authorized per integration

This document defines the control contract for incremental self-improvement. It does not claim that an autonomous self-evolution loop is already running.

## Lifecycle

1. **Discover** — collect repository state, test failures, benchmark results, dependency drift, open issues, and user-approved goals.
2. **Form a proposal** — create a bounded change proposal with affected paths, expected outcome, risks, rollback strategy, and measurable acceptance criteria.
3. **Isolate** — implement on a dedicated branch. Never edit canonical genome or index records as a side effect of ordinary optimization.
4. **Validate** — run targeted tests, regression tests, security checks, schema/contract checks, and benchmark comparisons as applicable.
5. **Evaluate evidence** — record commit SHA, commands, exit codes, logs/artifact links, baseline, candidate result, environment, and timestamp.
6. **Request human approval** — open a pull request with a concise evidence report. Publishing, production deployment, repository-wide changes, and external side effects require explicit human approval.
7. **Merge and observe** — merge only after approval and required checks pass. Observe regressions and preserve a rollback path.
8. **Learn** — store the result as an auditable event. Failed attempts remain visible; they are not rewritten as successes.

## Evidence states

- PROPOSAL: an idea not yet implemented.
- SPECIFIED: requirements and acceptance criteria exist.
- IMPLEMENTED: code or configuration exists.
- TESTED: named tests passed in a recorded environment.
- VERIFIED: deterministic evidence is reproducible and satisfies the relevant proof obligations.
- PARTIAL, BLOCKED, MISSING, CONFLICT: incomplete or contradictory evidence must remain explicit.

A passing unit test alone does not establish performance improvement, production readiness, or cross-repository integration.

## Mandatory gates

- No direct push to the protected default branch for generated improvements.
- No automatic merge.
- No deletion or overwrite of existing artifacts without a reviewed migration plan.
- No claim of cross-system integration without tests against each identified repository and a versioned contract.
- No performance claim without repeated baseline/candidate measurements under documented conditions.
- No external publishing without human approval of the exact content and destination.
- No secrets in source, logs, pull requests, or prompts. Use platform-managed secrets and least privilege.
- External actions remain disabled by default.
- Rollback instructions and responsible owner are required for operational changes.

## Core metrics

- CI pass rate and regression count
- Change lead time: proposal to reviewed merge
- Benchmark throughput (jobs/second), p50/p95 job latency, failure rate
- Resource use where available (CPU, memory, storage I/O)
- Reopen/rollback rate
- Human approval turnaround
- Customer funnel: qualified visits, demo requests, partner conversations, conversion, and revenue where tracked

## Initial implementation boundary

The current innovation server provides a local SQLite-backed job queue and bounded worker pool. It is not a distributed execution fabric, a production deployment, or a fully autonomous engineering loop. Further stages must add evidence collection, benchmark automation, approval queue management, and monitored execution incrementally.
