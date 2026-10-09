# Engineering Agent Fabric v1

**State:** IMPLEMENTED PLANNER + GATED RECIPE EXECUTOR / LIVE AGENT DISPATCH NOT VERIFIED  
**Parent system:** VAIXLNS  
**Federation boundary:** VAIXLNS + VLNS + VX + NEXNET

## Mission

Turn a project, repository, specification, or partial implementation into a structured path toward executable and verifiable behavior. The fabric extracts repository evidence, assigns specialist engineering work contracts, identifies conservative build/test candidates, and produces a reproducible plan. It must never equate generated code with a running system.

## Specialist agents

1. Project Archaeology — inventory, entry points, history.
2. Requirements Recovery — requirements, assumptions, acceptance criteria.
3. Canon & Provenance — hashes, immutable references, lineage.
4. Semantic Modeling — entities, interfaces, state machines, invariants.
5. Reverse Engineering — evidence-based behavior reconstruction.
6. Dependency & Build — toolchains, dependencies, reproducible recipes.
7. Implementation Engineer — minimal, reviewable changes.
8. Test & Replay — regression, negative, boundary, replay tests.
9. Security Adversary — trust boundaries, secrets, unsafe execution.
10. Performance & Cost — measurable runtime/cost constraints.
11. Independent Verifier — counterevidence and independent reproduction.
12. Release & Recovery — rollback, migration, release evidence.

These are deterministic task contracts, not a claim that twelve live model agents have been provisioned. Actual dispatch adapters remain separate and must report their own health, provider, model/version, task ID, input fingerprint, and result fingerprint.

## Lifecycle

```text
INPUT (repo/spec/design)
        |
        v
Inventory + file hashes + pinned revision
        |
        v
Requirements / semantics / dependencies extraction
        |
        v
Specialist work packets + unknowns register
        |
        v
Implementation patch proposal
        |
        v
Approval gate + exact allowlisted recipe
        |
        v
Bounded execution in isolated CI/sandbox
        |
        v
Captured logs + exit code + revision + receipt hash
        |
        v
Independent verification and governed promotion
```

## Run a plan

```bash
python scripts/engineering_agent_fabric.py \
  --root . \
  --output build/engineering-execution-plan.json
```

The plan fingerprints inventoried files and the current Git revision, then reports specialist tasks and candidate recipes. Planning never executes discovered project scripts.

## Explicitly approved execution

The optional executor only accepts exact built-in recipe IDs and requires an approval JSON whose `repository_revision` exactly matches the inspected Git HEAD. Example format:

```json
{
  "repository_revision": "PINNED_GIT_COMMIT_SHA",
  "authorized_by": "AUTHORIZED_REVIEWER_ID",
  "approval_ref": "CHANGE_OR_APPROVAL_RECORD",
  "recipe_ids": ["python-unittest"]
}
```

Then:

```bash
python scripts/engineering_agent_fabric.py \
  --root . \
  --output build/engineering-execution-plan.json \
  --execute-approved approval.json \
  --receipt build/engineering-execution-receipt.json
```

The approval file is an explicit gate input, not cryptographic proof of a person's identity or repository permissions. Execution uses fixed argument vectors, `shell=False`, a 600-second timeout, and captured output. The built-in recipes are Python unittest, Python pytest, Cargo workspace tests, and Go tests; each must also be detected in the inspected project. Do not treat this as a general sandbox for hostile code. Run untrusted builds only in a separately isolated runner with network, filesystem, CPU, memory, and credential restrictions.

## State semantics

- `PLANNED_NOT_DISPATCHED`: work contract exists; no live agent is claimed.
- `CANDIDATE_NOT_EXECUTED`: a build/test recipe was inferred from file presence.
- `EXECUTION_PASSED` / `EXECUTION_FAILED` / `EXECUTION_TIMED_OUT`: actual command result was captured.
- `runtime_verified=true`: only if every explicitly requested recipe completed with exit code zero for the exact pinned revision. This does not prove product correctness, security, novelty, or production readiness.
- `VERIFIED` and `CANONICAL` remain separate governed states and cannot be granted by the executor.

## Security invariants

- No `shell=True`; no arbitrary command text or agent-generated command is executed.
- No production deployment, privileged operation, secrets injection, or automatic canonical merge.
- Revision mismatch, unknown recipe, or non-detected recipe is rejected.
- Preserve all source records and historical IDs; hash inventory and receipt.
- Treat files, prompts, and agent outputs as untrusted data, not instructions.
- CI runs the planner and tests only; it does not invoke the approved executor.

## Known limitations

This v1 creates plans and a constrained execution mechanism. It does not yet dispatch live AI agents, connect to VLNS/VX/NEXNET runtime endpoints, autonomously implement arbitrary requirements, or execute every possible language/build system. New recipe adapters require tests, security review, and explicit governance.
