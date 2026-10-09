# Agentic Software Engineering Fabric (ASEF) v1

**Document ID:** VAIXLNS-ASEF-0001  
**Status:** PROPOSAL  
**Authority:** VAIXLNS / `project.genome`  
**Execution boundary:** VX  
**Knowledge and discovery boundary:** VV / VLNS  
**Registry boundary:** VI / Ω.000  
**Assurance boundary:** ARC-X + Ω-Arena  
**Version:** 1.0.0

> This document specifies a target architecture. It does not claim that agents, integrations, runtime controls, or tests described here are already implemented or verified.

## 1. Purpose

Build a governed multi-agent software engineering system that can discover repositories and prior work, recover provenance, understand dependencies, propose architecture, implement changes in isolated workspaces, execute tests, challenge its own results, and publish evidence-backed outcomes.

The system must preserve historical ideas and canonical authority. It must not confuse generated plans, source code, successful API responses, or passing isolated tests with end-to-end verification.

## 2. Non-negotiable invariants

1. **Canonical authority:** `project.genome` and the approved canonical registry define authority. A worker agent cannot rewrite its own authority.
2. **Evidence before status:** `VERIFIED` requires reproducible execution evidence tied to an exact revision and environment.
3. **No self-awarded success:** the implementation agent cannot issue the final verdict for its own work.
4. **Fail closed:** missing identity, policy, provenance, permission, required evidence, or verification results block promotion.
5. **Least privilege:** each agent receives only the tools, repository scopes, secrets, and write permissions needed for its assigned task.
6. **Simulation before mutation:** inspect, plan, diff, and test before merge, release, deployment, or destructive operation.
7. **No silent loss:** every superseded, rejected, recovered, or archived idea retains an identity, lineage, disposition, and reason.
8. **Deterministic records:** canonical inputs, policy version, tool versions, environment digest, output hashes, and event sequence are recorded where available.
9. **Human approval gates:** production deployment, secret access expansion, repository deletion, irreversible migration, and authority changes require explicit approval.
10. **Bounded autonomy:** an agent may act only within a signed task envelope, resource budget, time limit, and allowed action set.

## 3. Logical architecture

```text
VAIXLNS Constitution + project.genome + Ω.000
                     |
          Identity / Policy / Admission
                     |
        VV + VLNS: Discover and Retrieve
                     |
        VI: Project and Capability Registry
                     |
        XV: Planning and Agent Coordination
                     |
       VX: Isolated Execution and Event Fabric
                     |
      Test / Replay / Security / Adversarial Review
                     |
             ARC-X Evidence Gate
                     |
       Ω-Arena Independent Verdict / Score
                     |
        Proposed Patch -> Human Review -> Merge
                     |
          Provenance, Index and Memory Update
```

This is a logical boundary map, not a claim that each component currently exists as a deployed service. Existing implementations must be discovered and assessed before creating duplicate components.

## 4. Agent roles and authority boundaries

| Agent role | Responsibility | Permitted outputs | Must not do |
|---|---|---|---|
| Discovery Agent | Search authorized repositories, docs, issues, workflows, and history | Source map, citations, candidate links | Treat search snippets as canonical proof |
| Recovery / Provenance Agent | Reconstruct lineage, duplicate candidates, supersession, and missing history | Recovery ledger with confidence and evidence | Delete or silently rewrite recovered material |
| Architect Agent | Produce component boundaries, dependency graph, ADRs, contracts, and migration plan | Versioned design proposal | Claim implementation or verification |
| Task Decomposer | Split work into dependency-aware, bounded tasks | Task DAG with acceptance criteria | Assign conflicting writes without coordination |
| Implementation Agent | Make scoped changes in a branch or disposable workspace | Patch, tests, change manifest | Push directly to protected main or expand scope |
| Test / Replay Agent | Run unit, integration, contract, regression, and deterministic replay checks | Raw logs, exit codes, environment manifest | Edit expected results to make tests pass |
| Security / Adversarial Agent | Probe trust boundaries, prompt injection, permissions, secrets, supply chain, and failure paths | Reproducible findings and severity | Access unapproved secrets or systems |
| Independent Referee | Compare evidence to acceptance policy and issue a verdict | PASS / FAIL / INCONCLUSIVE with reasons | Implement the change it is judging |
| Release / Admission Agent | Check branch policy, approvals, artifacts, provenance, and rollout conditions | Release recommendation or blocked decision | Bypass required human approval |
| Memory / Index Agent | Update registry and engineering memory from accepted, sourced outcomes | Append-only event and index proposal | Convert speculation into canonical truth |

A deployment may combine roles only when separation-of-duties policy allows it. The final referee must be independent of the implementation attempt.

## 5. Task contract

Every task must carry a validated envelope with at least:

- `task_id`, `parent_task_id`, `goal`, `acceptance_criteria`
- `canonical_source`, `repository`, `base_revision`, `target_branch`
- `authorized_paths`, `allowed_tools`, `denied_actions`
- `agent_role`, `policy_version`, `approval_requirements`
- `input_artifact_hashes`, `environment_digest`, `dependency_lock_digest`
- `budget`, `deadline`, `retry_limit`, `idempotency_key`
- `required_tests`, `security_profile`, `evidence_requirements`
- `result_state`, `event_ids`, `artifact_hashes`

Reject unknown authority fields, invalid states, out-of-scope paths, expired tasks, and missing required hashes. A schema validates structure; a separate policy engine validates authority and permissions.

## 6. Controlled lifecycle

```text
DISCOVERED
  -> CONTEXT_RECOVERED
  -> SPECIFIED
  -> PLAN_REVIEWED
  -> AUTHORIZED
  -> IMPLEMENTED_IN_SANDBOX
  -> TESTED
  -> ADVERSARIAL_REVIEWED
  -> REPLAY_VERIFIED
  -> EVIDENCE_ADMITTED
  -> HUMAN_APPROVED
  -> MERGED
  -> POST_MERGE_VERIFIED
```

Any stage may transition to `BLOCKED`, `FAILED`, `INCONCLUSIVE`, or `QUARANTINED` with a reason and event record. A retry creates a new attempt linked to the previous attempt; it does not erase failure history. Only the policy engine may permit a transition, and only evidence satisfying the configured acceptance contract may advance assurance state.

## 7. Engineering execution protocol

### Phase A — Discover and recover

1. Read the canonical genome and master index first.
2. Inventory relevant repositories, branches, commits, workflows, schemas, tests, issues, and prior decisions.
3. Record exact source references and revision identifiers.
4. Classify each claim as `PROPOSAL`, `SPECIFIED`, `IMPLEMENTED`, `PARTIAL`, `VERIFIED`, `MISSING`, or `CONFLICT`.
5. Preserve conflicting evidence; do not silently resolve it.

### Phase B — Model and plan

1. Build a dependency graph and identify single sources of truth.
2. Detect overlap with existing implementations before adding new modules.
3. Write acceptance criteria and negative tests before implementation.
4. Define rollback, failure containment, data migration, and compatibility strategy.
5. Require human review for high-impact architecture or authority changes.

### Phase C — Implement in isolation

1. Pin the base revision and dependencies.
2. Use a disposable workspace/container with restricted network, filesystem, and credentials.
3. Enforce path allowlists, resource limits, timeouts, and bounded tool calls.
4. Produce a minimal diff and machine-readable change manifest.
5. Never expose secrets in prompts, logs, test artifacts, or agent-to-agent messages.

### Phase D — Verify independently

Run applicable checks in this order:

1. Syntax, formatting, static analysis, and schema validation.
2. Unit tests and negative/adversarial tests.
3. Contract and integration tests.
4. Regression suite and compatibility tests.
5. Security and dependency/supply-chain checks.
6. Reproducibility or replay from a clean environment.
7. Independent review of diff, evidence, and acceptance criteria.

A green unit test is not sufficient evidence for system-level verification.

### Phase E — Admit and learn

1. Bind evidence to commit SHA, environment digest, toolchain, test command, exit status, and artifact hashes.
2. Let the independent referee return `PASS`, `FAIL`, or `INCONCLUSIVE`.
3. Require human approval for protected-branch merge and consequential operations.
4. After merge, run post-merge checks against the merged revision.
5. Append the decision, provenance, lessons, and index update; preserve previous versions.

## 8. Evidence record

An evidence bundle should contain:

- Evidence ID and schema version.
- Task ID, attempt ID, repository, commit SHA, and changed-path list.
- Claim under test and acceptance-criterion IDs.
- Exact command, toolchain versions, environment digest, and relevant dependency hashes.
- Start/end timestamps, exit code, raw log/artifact references, and SHA-256 hashes.
- Test coverage of positive, negative, and adversarial cases.
- Known limitations, skipped checks, flaky checks, and external dependencies.
- Referee identity/version, verdict, rationale, and policy version.
- Signature or trusted provenance attestation where infrastructure supports it.

Do not store secret values in evidence. Redact sensitive data while retaining verifiable references to the controlled source.

## 9. Ω-Arena integration

Use the existing `schemas/vx-arena.schema.yaml` as the initial specified contract, not as proof of an operational arena.

Required arena behavior:

1. Freeze task corpus and environment identifiers before a contest.
2. Require independent solution attempts and immutable submission references.
3. Execute each submission in a separately isolated environment.
4. Evaluate correctness, reproducibility, security, completeness, contradiction resistance, evidence quality, robustness, and innovation using versioned metric definitions.
5. Run adversarial cases and repair/re-execution cycles.
6. Keep metric calculation separate from the participant agent.
7. Produce a verdict with evidence references, uncertainty, and explicit failed gates.
8. Do not rank a candidate as the winner when mandatory gates fail or evidence is inconclusive.

Scores must not allow a high innovation score to compensate for a critical security or correctness failure. Define hard gates before any weighted aggregate score.

## 10. Security and resilience controls

- Repository and branch allowlists; protected branches; short-lived credentials.
- No agent-controlled privilege escalation or policy self-modification.
- Prompt-injection defenses for repository files, issues, web pages, tool output, and test fixtures; treat retrieved content as untrusted data.
- Egress restrictions, secret scanning, dependency pinning, artifact provenance, and audit logs.
- Per-task resource budgets, concurrency limits, cancellation, and circuit breakers.
- Idempotent operations and deduplication keys for retries.
- Backup and recovery procedures for registries and evidence stores.
- Quarantine suspicious artifacts and isolate failed agents.
- Two-person or explicit owner approval for destructive or production-impacting actions.
- Emergency stop that halts execution without deleting event history.

## 11. Observability and scorecard

Track at minimum:

- Task success rate by acceptance criteria, not agent self-report.
- First-pass verification rate and regression escape rate.
- Reproducible replay rate.
- Security findings by severity and time to remediation.
- Mean time from discovery to evidence-backed decision.
- Human intervention and override rate.
- Duplicate-work rate and canonical-index drift.
- Cost per accepted change, token/tool consumption, and runtime.
- Percentage of claims with source lineage and evidence.
- Rollback rate and post-merge failure rate.

Metrics must use documented denominators, time windows, and event sources. Never optimize only for code volume, number of agents, or raw task throughput.

## 12. Failure handling

| Condition | Required behavior |
|---|---|
| Missing or conflicting canonical source | Block promotion and request reconciliation |
| Acceptance criteria not testable | Return to specification |
| Tool timeout or partial output | Mark attempt incomplete; preserve logs |
| Test flakiness | Repeat under bounded policy; report instability |
| Security critical finding | Quarantine candidate and block merge |
| Evidence hash mismatch | Reject evidence bundle |
| Agent exceeds scope | Terminate or suspend task; record policy violation |
| Replay differs | Mark not reproducible; investigate environment or nondeterminism |
| Referee disagreement | Return `INCONCLUSIVE`; require independent adjudication |
| Index update fails | Keep engineering result distinct from registry synchronization status |

## 13. Rollout plan

### Stage 0 — Inventory (no writes to protected branch)

Map existing schemas, runtime code, agent implementations, CI workflows, evidence stores, and index writers. Identify duplicate systems and current test coverage.

### Stage 1 — Contract and validator

Specify a versioned task envelope, agent capability declaration, state-transition policy, and evidence record. Add positive and negative schema/policy tests.

### Stage 2 — One vertical slice

Run one low-risk repository task through discovery, isolated implementation, tests, adversarial review, replay, independent verdict, and a draft pull request.

### Stage 3 — Multi-agent coordination

Add dependency-aware task DAGs, concurrency controls, message provenance, retry semantics, and conflict detection. Do not allow concurrent writes to the same path without an explicit lock or merge strategy.

### Stage 4 — Ω-Arena

Connect independently executed submissions to hard-gated metrics and evidence-backed verdicts. Test dishonest scores, missing evidence, replay mismatch, and referee failure.

### Stage 5 — Governed federation

Extend to additional repositories only after the vertical slice is verified. Keep repository-specific adapters behind explicit contracts; never infer interoperability from matching names alone.

## 14. Definition of done

The fabric may be called `VERIFIED` only when all required criteria pass:

- Canonical source and authority checks pass.
- Task envelopes and state transitions reject invalid cases.
- Agents cannot exceed their declared permissions in tested adversarial scenarios.
- A complete task can be replayed or its nondeterministic boundaries are explicitly documented and bounded.
- Independent referee decisions are reproducible from the evidence bundle.
- Failed and inconclusive runs remain visible.
- Protected-branch and human-approval policies are enforced.
- Registry and provenance updates are checked for consistency.
- CI evidence references the exact commit tested.
- Operational limits, failure recovery, and known limitations are documented.

Until then, the correct status is `PROPOSAL`, `SPECIFIED`, or `PARTIAL` according to the evidence available.

## 15. Immediate repository work items

1. Audit the existing agent/runtime code before creating parallel abstractions.
2. Add a dedicated task-envelope schema and validator.
3. Add an evidence-bundle schema with commit and environment binding.
4. Add a policy-controlled lifecycle transition validator.
5. Add tests for missing evidence, invalid transitions, scope escape, replay mismatch, and self-awarded verdicts.
6. Connect these checks to the canonical conformance workflow.
7. Register this document as a proposal in the appropriate canonical index only after validating the registry's current schema and update procedure.
8. Promote no status without test logs and reproducible evidence.

---
**End of specification.**

## Related engineering specification

For a deeper implementation contract covering clean diffs, dependency-aware routing, proof-carrying patch capsules, effect mediation, regression challenge and acceptance criteria, see [`AGENTIC_CLEAN_CHANGE_ENGINEERING_V1.md`](AGENTIC_CLEAN_CHANGE_ENGINEERING_V1.md). This is a proposal and must not be read as evidence that those controls are deployed.
