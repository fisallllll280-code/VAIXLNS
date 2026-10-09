# Agentic Clean-Change Engineering Fabric (ACCEF) v1

**Document ID:** `VAIXLNS-ACCEF-0001`  
**Status:** `PROPOSAL`  
**Authority:** VAIXLNS / `project.genome`  
**Execution boundary:** VX  
**Knowledge and source discovery:** VV / VLNS  
**Registry and lineage:** VI / Ω.000 / Zero-Loss Index  
**Assurance:** ARC-X + Ω-Arena  
**Version:** 1.0.0  
**Research cutoff:** 2026-10-09

> This is a proposed engineering contract and architecture. It does not claim that the mechanisms in this document are implemented, activated, novel worldwide, or independently verified. Existing repository assets must be inventoried before duplicate components are built.

## 1. Executive decision

Build a **governed clean-change factory**, not a fixed swarm of code-writing agents. It should select the smallest effective execution topology for each task, ground work in repository and historical evidence, isolate edits, constrain the permitted change surface, challenge tests and patches independently, and admit a change only with a reproducible evidence capsule.

The central product is the **Ω Change Capsule**: a version-bound, machine-checkable package describing the task contract, source revision, allowed paths, exact diff, structural/API impact, tests, security findings, verification environment, recovery plan, and final admission decision. A code patch is a candidate; the capsule is the review and admission object.

The proposed synthesis combines established software-engineering controls with emerging agent-runtime research. It must not be represented as a claim that any individual mechanism is globally unprecedented. Potential differentiation lies in the composition, measurable outcomes, and its integration with VAIXLNS zero-loss lineage and governed authority.

## 2. Evidence-grounded findings

### 2.1 Agent count is a decision, not a quality metric

Controlled research comparing single-agent and multi-agent systems finds task- and architecture-dependent outcomes rather than a universal multi-agent advantage. Therefore, the orchestrator must estimate whether independent work actually exists and compare performance to a matched single-agent baseline before increasing the team size.

- Kim et al., *Capable language models can outgrow the benefits of collaboration*, Nature Machine Intelligence (2026): https://doi.org/10.1038/s42256-026-01268-y
- Geng and Neubig, *Effective Strategies for Asynchronous Software Engineering Agents* (2026): https://arxiv.org/abs/2603.21489

The CAID work motivates dependency-aware delegation, isolated Git worktrees, structured task assignments, and serialized integration. Its results are benchmark-specific and have coordination/cost trade-offs; they do not prove that arbitrary multi-agent teams improve every repository task.

### 2.2 Tests should drive repair, but passing tests is not a complete proof

TDFlow demonstrates a test-driven multi-agent workflow where patch proposals are repeatedly evaluated against reproduction and regression tests. Its paper also discusses failed or invalid generated reproduction tests, benchmark execution constraints, test-hacking review, and the distinction between test resolution and broader code quality.

- Han et al., *TDFlow: Agentic Workflows for Test Driven Development*, EACL 2026: https://aclanthology.org/2026.eacl-long.70/

The factory must therefore validate the test suite itself, preserve the original test set, inspect attempts to weaken tests, and add contract, property-based, mutation, differential, or integration tests where justified. “Green” is necessary for many changes, not by itself sufficient evidence of correctness.

### 2.3 Security must be enforced at effect boundaries

AgentDojo provides a dynamic evaluation environment for tool-using agents exposed to prompt injection from untrusted external data. Its reported suite contains 97 realistic tasks and 629 security test cases. Its central lesson is that instructions and prompt-level defenses alone do not constitute a reliable security boundary.

- Debenedetti et al., *AgentDojo: A Dynamic Environment to Evaluate Attacks and Defenses for LLM Agents*: https://arxiv.org/abs/2406.13352

Emerging agent-runtime studies further investigate pause/cancel/timeout enforcement gaps, replay-related duplicate effects, and task-level transaction boundaries. These are promising but bounded research results, not blanket production guarantees.

- Khan, *Stop Means Stop* (2026 preprint): https://arxiv.org/abs/2607.14166
- Li, *Where Does Exactly-Once Live?* (2026 preprint): https://arxiv.org/abs/2609.29095
- Chen et al., *Cordon: Semantic Transactions for Tool-Using LLM Agents* (2026 preprint): https://arxiv.org/abs/2606.17573

For VAIXLNS, every mutating operation must pass through a policy-enforced broker; network, repository, filesystem, package-manager, and deployment effects need explicit mediation. A timed-out write is an **unknown outcome**, not proof that the write failed. Use stable idempotency keys when the target service supports them, and block or escalate when safe resolution is impossible.

### 2.4 Reproducibility and provenance are part of the artifact

Use established mechanisms where possible rather than inventing substitute formats:

- SLSA provenance describes how an artifact was produced and supports verification and rebuilding: https://slsa.dev/spec/v1.2/
- OpenTelemetry correlates traces, metrics, and logs across components: https://opentelemetry.io/docs/
- CodeQL supports data-flow and taint analysis for applicable languages: https://codeql.github.com/docs/
- Hypothesis provides property-based input generation for Python: https://hypothesis.readthedocs.io/
- Mutmut is one available Python mutation-testing tool: https://github.com/boxed/mutmut
- OpenHands provides a composable agent SDK and isolated execution options: https://github.com/OpenHands/software-agent-sdk

Tool adoption must be based on language coverage, license, security posture, integration cost, and repository needs. Listing a tool here does not imply it is installed in VAIXLNS.

## 3. Proposed system map

```text
USER INTENT
  |
  v
[1] Intent & Change-Contract Compiler
  |  request, scope, acceptance criteria, non-goals, risk class
  v
[2] Evidence / Zero-Loss Context Retrieval
  |  source IDs, revisions, hashes, lineage, unresolved conflicts
  v
[3] Repository Reality Graph
  |  symbols, tests, dependencies, configs, interfaces, impact closure
  v
[4] Adaptive Topology Router
  |  single agent / serial specialists / isolated parallel workers
  v
[5] VX Isolated Execution Broker
  |  per-task worktree/container, capability-bound tools, effect gate
  v
[6] Candidate Patch + Ω Change Capsule
  |  exact diff, impact graph, test delta, dependency delta, provenance
  v
[7] Independent Verification Fabric
  |  tests, static analysis, contracts, property/mutation/differential tests
  v
[8] ARC-X Adversarial Challenge + Ω-Arena Referee
  |  attacks, counterexamples, policy and evidence validation
  v
[9] Evidence Admission Gate
  |  PASS / FAIL / BLOCKED / INCONCLUSIVE; no self-awarded verdict
  v
[10] Human / policy authorization → reviewed merge → post-merge replay
  |
  v
Append-only event & evidence record → proposed Zero-Loss Index projection
```

### Ownership boundaries

- **VAIXLNS / Genome:** governing identity, invariants, approval rules, and epistemic status vocabulary.
- **VV / VLNS:** retrieve authorized sources and historical material; supply source-bound facts and unresolved conflicts, not canonical authority.
- **VI / Ω.000:** identity, typed relationships, lineage and registry projections; indexing must not silently canonicalize.
- **XV:** task analysis, plan options, tool/agent selection recommendations and uncertainty.
- **VX:** isolated execution, state transitions, mediated tool effects, event traces and replay.
- **ARC-X:** evaluate claims against explicit proof obligations and evidence quality.
- **Ω-Arena:** independent adversarial roles and a referee; the implementation agent cannot decide its own final verdict.

Names describe intended boundaries. Integrations must be checked against existing repository components before implementation.

## 4. Innovation candidates for VAIXLNS

All candidates below are **proposed VAIXLNS-specific syntheses**. Prior-art search has not established worldwide novelty. Each must compete against a simpler baseline.

### Ω-1. CleanDelta Governor — minimal, scoped code change

**Problem:** Agents often produce broad refactors, formatting churn, unrelated dependency changes or edits outside the request. A patch can pass tests while increasing review cost or introducing hidden scope.

**Mechanism:**
1. Compile the request into an explicit change contract with allowed and forbidden paths, expected symbols/interfaces, behavior assertions, non-goals and change budget.
2. Capture a baseline manifest before edits: commit SHA, dirty-tree state, file hashes, test configuration, dependency lock state and current public API signatures where available.
3. Compare the final diff with the declared scope using file paths, AST/symbol changes and dependency changes—not line count alone.
4. Reject unexplained files, unrelated formatting, test weakening, authority/index changes and new dependencies unless the task contract explicitly authorizes them.
5. Offer an explicit scope-expansion request when investigation shows that a broader change is truly required.

**Output:** a machine-readable scope report and a minimal-diff candidate.

**Acceptance:** zero unexplained touched paths; zero unapproved protected-file changes; all scope expansions explicit and reviewable.

### Ω-2. Repository Reality Graph — cross-file impact before edits

**Problem:** A local-looking change can affect callers, tests, schemas, generated code, configuration, runtime behavior or another repository.

**Mechanism:** Maintain a revision-bound typed graph. Suggested nodes include files, symbols, tests, packages, interfaces, schemas, workflows, environment variables, runtime commands, repository commits, source records and external-tool contracts. Suggested edges include imports, calls, reads/writes, schema-conformance, test-covers, generates, configures, depends-on, source-reference, supersedes and lineage.

Each edge has an origin label:
- `OBSERVED_STATIC`
- `OBSERVED_RUNTIME`
- `DECLARED_CONTRACT`
- `INFERRED_CANDIDATE`
- `HUMAN_CONFIRMED`

Do not promote mentions or embeddings into dependency facts. Compute an impact frontier from the changed symbols/files using supported graph edges. Use uncertainty-aware fallbacks: when language analysis or dynamic behavior is opaque, expand verification rather than pretending the dependency graph is complete.

**Output:** an impact graph and a scoped verification plan.

**Acceptance:** each selected test maps to a changed or dependent unit with a recorded reason; unknown edges remain visible; graph revisions are bound to the source commit.

### Ω-3. Adaptive Agent Topology Router — collaboration only when justified

**Problem:** Fixed agent counts waste cost and create synchronization failures. A supposedly “50-agent” design may be many wrappers around one model or redundant prompts rather than distinct useful capabilities.

**Mechanism:** Start with a task classifier and single-agent baseline. Estimate:
- task modularity;
- dependency density and cycles;
- separation of file/symbol ownership;
- need for independent assurance;
- risk and irreversibility;
- expected cost and integration overhead;
- measured capability evidence for available agents.

Use a simple agent for a narrow, low-risk task; serial specialists for sequential work; isolated parallel workers only when dependency boundaries permit it; and a separate verifier for changes above an explicit risk threshold. Select topology by measured marginal benefit, not agent count. An agent becomes a “specialist” only when its tools, access scope, evaluation history and incremental contribution are recorded.

**Output:** routing rationale, expected budget, task decomposition and agent-capability references.

**Acceptance:** compare single-agent and selected-topology results on held-out tasks with matched model, tool and total compute budgets. Report quality, cost, duration, regression rate and review effort. Do not label an agent independent based only on its name or prompt.

### Ω-4. Ω Change Capsule — proof-carrying candidate patch

The capsule is the primary integration object. Proposed fields:

```json
{
  "capsule_id": "CHANGE.<stable-id>",
  "status": "PROPOSAL",
  "task_id": "<task-id>",
  "source_repository": "<owner/repository>",
  "base_commit": "<immutable-sha>",
  "candidate_commit": "<immutable-sha-or-null>",
  "contract_ref": "<change-contract-id>",
  "source_refs": [],
  "allowed_paths": [],
  "changed_paths": [],
  "diff_sha256": "<sha256>",
  "impact_graph_ref": "<artifact-or-null>",
  "api_and_schema_delta_ref": "<artifact-or-null>",
  "test_manifest": {
    "baseline_digest": "<sha256-or-null>",
    "candidate_digest": "<sha256-or-null>",
    "test_source_changes_authorized": false
  },
  "environment": {
    "runtime": "<version>",
    "dependency_lock_digest": "<sha256-or-null>",
    "container_digest": "<digest-or-null>"
  },
  "checks": [],
  "security_findings": [],
  "unresolved_items": [],
  "recovery_plan_ref": "<artifact-or-null>",
  "evidence_refs": [],
  "verifier_identity": "<separate-principal-or-null>",
  "admission_decision": "BLOCKED"
}
```

This is illustrative; implement against a versioned JSON Schema before using it as an API. A digest binds bytes, not truth; evidence also needs source identity, run/commit identity, checker version, exit status and result payload.

### Ω-5. Regression Crucible — try to break the patch and its tests

**Problem:** Passing current tests is weak evidence if the tests miss the modified behavior or can be manipulated.

**Mechanism:**
1. Run the pre-change baseline and save the test manifest and outcomes.
2. Protect test and workflow files from silent edits. Any authorized test changes must be shown as a separate diff with rationale.
3. Run targeted tests, regression tests and the required repository suite.
4. Use static analysis, type checks, schema/contract checks and security scanning according to language and risk.
5. Generate property-based cases for declared invariants; use mutation testing to determine whether critical assertions can detect seeded behavioral faults.
6. Where a reference behavior exists, run differential tests against the previous release or a trusted implementation.
7. Add adversarial tests for path traversal, prompt injection through repository content, secret flow, unapproved network egress, tool-call replay, stale authority and cross-task state leakage.
8. Re-run the clean candidate in a fresh isolated environment; retain first failure, counterexample, diff and environment.

**Output:** evidence matrix; mutation survivors and uncovered obligations stay visible rather than being hidden behind a single green check.

### Ω-6. Effect Gate — task-scoped staging, commit, and recovery

**Problem:** A task can partially write files, call external services, publish a message or update a repository before verification finishes. A timeout may leave the outcome ambiguous.

**Mechanism:** Use two phases where feasible:
- **Prepare:** stage local writes in an isolated worktree/shadow state and external effects in an outbox. Capture intent, caller identity, target, operation digest, idempotency key, policy decision and recovery classification.
- **Admit:** verify the final composite task effect and release only the explicitly authorized operations. On rejection, discard staged local changes and suppress unreleased effects. For already-externalized effects, use a documented compensation path where one genuinely exists; do not falsely claim rollback.

Mutating operations need stable intent IDs across retries. Unknown outcomes remain `INCONCLUSIVE` until resolved through a safe read-back, idempotent replay, reconciliation or human decision. Complete mediation is a deployment obligation: a broker that can be bypassed does not provide a security guarantee.

### Ω-7. Zero-Loss Engineering Memory — learn without erasing history

**Problem:** Context compression, summaries or evolving agent prompts can forget the source, remove conflicting history or turn repeated claims into apparent truth.

**Mechanism:** After every completed, failed or aborted run, append an evidence-linked record of the intent, source revision, agent/tool identities, choices, diff, tests, failures, resolution and unresolved questions. Build retrieval projections from this history while preserving the raw source and the distinction among `SOURCE`, `ATOMIC`, `CANONICAL`, `IMPLEMENTED` and `VERIFIED`.

Similar records become `ALIAS`, `VARIANT`, `REVISION`, `MERGED` or `SUPERSEDES` candidates only when supported by source evidence. Never create legacy IDs or promote the record merely because a model says it is correct. Index synchronization is a separately reviewed projection, not an incidental side effect of code generation.

## 5. Change contract and lifecycle

### 5.1 Required task envelope

Every implementation task should carry:

- immutable task ID and parent request;
- source repository and base commit;
- purpose, expected behavior and explicit non-goals;
- acceptance criteria and tests that can establish each criterion;
- allowed paths and protected paths;
- public API/schema compatibility requirements;
- dependencies and order constraints;
- risk class, allowed tools, network policy and secret access policy;
- time, token, tool-call and retry budgets;
- required test/assurance profile;
- abort rules and recovery method;
- references to historical context and unresolved conflicts.

If a critical field is missing, classify the task as `BLOCKED` or `UNRESOLVED`; do not fill it with a guess.

### 5.2 State machine

```text
DISCOVERED
 -> CONTEXT_BOUND
 -> CONTRACT_READY
 -> PLAN_REVIEWED
 -> AUTHORIZED
 -> ISOLATED
 -> PATCH_PROPOSED
 -> SCOPE_VALIDATED
 -> TESTED
 -> ADVERSARIAL_REVIEWED
 -> REPLAY_OR_REPRODUCIBILITY_CHECKED
 -> EVIDENCE_ADMITTED
 -> HUMAN_OR_POLICY_APPROVED
 -> MERGED
 -> POST_MERGE_VERIFIED
 -> INDEX_PROJECTION_PROPOSED
```

At any point, the run can be `BLOCKED`, `FAILED`, `INCONCLUSIVE`, `QUARANTINED` or `ABORTED`. Terminal failure records remain queryable. Retries produce new attempts linked to the original task rather than overwriting earlier evidence.

### 5.3 Role separation

| Role | Allowed responsibility | Must not do |
|---|---|---|
| Context archaeologist | Retrieve sources and prior decisions | Invent missing legacy facts |
| Contract compiler | Convert intent to acceptance criteria and change boundaries | Authorize its own broadening |
| Planner / router | Model dependencies and choose topology | Execute external effects |
| Implementer | Modify allowed files in an isolated workspace | Change protected files or final verdict |
| Test engineer | Add and run authorized tests | Secretly weaken existing tests |
| Security challenger | Try to violate the task/policy boundary | Approve its own remediation |
| Independent verifier | Re-run checks against the exact candidate | Trust an unbound `PASS` claim |
| Referee / admission gate | Evaluate evidence against criteria | Infer missing evidence as success |
| Registry publisher | Propose a source-linked index projection | Mutate canonical authority without approval |

Roles may reuse a foundation model, but independent assurance requires separation of decision path, permissions, or checking mechanism—not merely different names in a prompt.

## 6. Verification matrix

| Risk level | Minimum checks | Admission rule |
|---|---|---|
| Low: docs/local non-executable | Scope/path check, link/format validation, diff review | No unexplained scope drift; evidence recorded |
| Medium: routine code | Baseline + targeted + regression tests, lint/type/static checks, diff review | All required checks pass; no unresolved high-severity finding |
| High: API, schema, storage, auth, execution or multi-file behavior | Medium checks + compatibility/contract tests, mutation or property checks where applicable, adversarial review, replay/reproducibility check | Separate verifier and explicit human/policy approval |
| Critical: secrets, supply chain, canonical authority/index, deployment, destructive or irreversible action | High checks + protected environment, independently authorized effect gate, signed/attested evidence where supported, tested recovery or explicit non-reversibility plan | Fail closed; never auto-promote on model judgment alone |

Exact checks are language- and project-specific. The policy must state which checks apply and why; “no relevant test exists” is not equivalent to a pass.

### Required test-integrity checks

- Capture a digest of baseline test/workflow files.
- Compare test changes separately from implementation changes.
- Flag deletion, skipping, assertion weakening, environment-based bypasses, or changes to the test runner.
- Run protected tests in an environment the implementation agent cannot rewrite.
- For high-risk logic, inject selected faults/mutations to test whether assertions detect them.
- Record flaky outcomes and repeat counts; do not simply discard inconvenient failures.

### Evidence record

Each checker result binds:
- task and capsule IDs;
- repository URL and exact commit/tree digest;
- check name, tool/version and configuration digest;
- environment/container and dependency-lock digest;
- exact command or action identity;
- start/end timestamps and exit code;
- result artifact digest, logs/traces and failed assertions;
- checker identity and policy version.

Hashes help detect artifact changes; they do not by themselves prove authority, completeness, correctness or independent review.

## 7. Clean-code and operational metrics

Report a profile, not a single unqualified score:

1. **Behavior:** acceptance-criterion completion; verified regression count; compatibility results.
2. **Scope:** unexplained changed paths, unrelated lines, protected-file violations, unapproved dependency changes.
3. **Quality:** lint/type/static-analysis deltas, maintainability signals, duplicated logic, API/schema complexity.
4. **Test strength:** targeted/regression pass rate, mutation score where applicable, property failures, test quality review, flaky-test rate.
5. **Security:** privilege violations, prompt-injection success, secret-flow findings, blocked forbidden effects, supply-chain/provenance gaps.
6. **Reproducibility:** repeated-run result agreement, environment pinning, artifact verification, replay divergence.
7. **Operations:** end-to-end success, recovery success, repeated side effects, timeout/cancellation behavior, mean time to diagnosis.
8. **Economics:** total model/tool/runtime cost, wall-clock duration, reviewer minutes, rework, change-failure rate.
9. **Memory/lineage:** percentage of records with source digest and lineage, unresolved-gap count, unbound claims, projection drift.

Targets must be calibrated on representative VAIXLNS tasks. Do not set a universal mutation threshold or quality score without observing language, domain and test-baseline behavior.

## 8. Threat model and failure handling

### Threats to design against

- hostile instructions inside README/issues/code comments/dependencies/test fixtures;
- confused-deputy behavior across tool identities;
- write operations outside assigned paths;
- stolen or over-broad credentials;
- test hacking and evaluator leakage;
- replayed or duplicated external effects;
- stale repository base or dependency graph;
- concurrent conflicting edits;
- incomplete process/state recovery;
- hidden cross-repository dependencies;
- false success claims, missing evidence and fabricated provenance;
- attempts to mutate `project.genome`, `Ω.000` or protected workflow files without authority.

### Safe responses

- Unknown authority, unclear scope, missing required evidence or an unmediated effect: `BLOCKED`.
- Test failure, scope violation or policy breach: `FAILED` or `QUARANTINED`, preserving the candidate and logs.
- Ambiguous remote effect or inconclusive test result: `INCONCLUSIVE`; don't blindly retry.
- Recoverable local failure: return to last known-good isolated state and create a new attempt.
- Security-relevant violation: stop affected capabilities, preserve evidence, rotate/revoke access through the proper operator, and require independent review.
- Registry mismatch: preserve both versions and emit a conflict record; do not auto-merge.

## 9. Build plan for the first vertical slice

### Slice A — Read-only repository diagnosis

1. Inspect existing VX/VAIXLNS task runners, schemas, test harnesses, admission gates and evidence formats.
2. Build an inventory of existing mechanisms and ownership; reuse or extend rather than duplicate.
3. Produce a source-bound repository graph and an explicit unresolved-gap report.
4. Add regression tests for no unapproved writes and no status promotion during indexing.

### Slice B — One clean, low-risk code change

1. Accept one tightly scoped issue and compile a task envelope.
2. Pin base commit and baseline hashes.
3. Use one isolated branch/worktree; no canonical registry, secret, workflow or deployment changes.
4. Produce one patch and Change Capsule.
5. Run lint/type/static checks, targeted tests, repository regression tests and independent diff/scope review.
6. In a separate clean checkout, rerun relevant checks and verify the capsule hashes.
7. Open a draft PR; preserve all evidence and failures.

### Slice C — Adversarial and reliability validation

Inject:
- tool timeout after a write may have committed;
- duplicate task delivery and replay;
- cancellation during an outstanding action;
- a stale base commit;
- a task requiring two dependent files;
- a malicious instruction in a repository fixture;
- an unauthorized edit to a protected path;
- a deliberately weakened test;
- a missing test oracle;
- an interrupted run and resume from a checkpoint.

Each scenario must have an expected terminal state and assertion. Where no reliable recovery exists, the expected result is a safe block or `INCONCLUSIVE`, not simulated success.

### Slice D — Selective parallelism

Only after Slice B is reproducible, compare a single-agent baseline against two isolated workers on a task with demonstrably independent modules. Use equal total budgets, record integration cost and conflicts, and reject parallelization if marginal benefit does not exceed overhead.

### Slice E — Controlled federation

Add repo-specific adapters and evidence contracts for each authorized repository. Only after local verification should the system propose cross-repository index projections. The canonical Genome and Ω.000 remain governed assets, not auto-generated outputs.

## 10. Proposed acceptance tests

- **AC-01 Scope fence:** any write outside an allowed path is blocked and recorded.
- **AC-02 Baseline integrity:** the run pins a specific source commit and reports pre-existing dirty state.
- **AC-03 Test integrity:** unauthorized test weakening or test-runner modification causes failure.
- **AC-04 Separate verdict:** the implementation identity cannot submit the accepted final verdict.
- **AC-05 Dependency readiness:** a dependent task is not scheduled before prerequisites integrate.
- **AC-06 Isolation:** concurrent workers cannot overwrite one another's workspace state.
- **AC-07 Idempotency:** duplicate task/action delivery does not repeat the same external effect where an idempotency contract is available.
- **AC-08 Ambiguous effect:** unresolved timeout/late-commit outcomes remain `INCONCLUSIVE`.
- **AC-09 Adversarial input:** repository-provided malicious instructions cannot widen the tool capability envelope.
- **AC-10 Evidence binding:** evidence for a different commit, run or environment is rejected.
- **AC-11 Replay:** repeated validation of the same pinned input yields equivalent declared results, or records the nondeterministic discrepancy.
- **AC-12 Zero-loss history:** failed, superseded or unresolved candidates remain retrievable with their source lineage.
- **AC-13 Canonical protection:** automatic indexing and implementation agents cannot promote or mutate Genome/Ω.000.
- **AC-14 Post-merge:** the integrated commit is re-verified; pre-merge success is not reused as proof for a different tree.

These are test requirements, not claims that tests currently exist or pass.

## 11. Integration with the current VAIXLNS repository

The repository already contains a Zero-Loss Index contract, taxonomy, atomic-record schema, builder, regression tests and read-only workflow. This proposal is complementary, not a replacement.

- Zero-Loss Index: `docs/indexes/VAIXLNS_ZERO_LOSS_INDEX_V1.md`
- Taxonomy: `registry/indexes/zero-loss-index-taxonomy.v1.json`
- Atomic record schema: `schemas/zero-loss-atomic-record.schema.json`
- Builder: `scripts/build_zero_loss_index.py`
- Index workflow: `.github/workflows/zero-loss-index.yml`
- Agentic fabric base proposal: `docs/engineering/AGENTIC_SOFTWARE_ENGINEERING_FABRIC_V1.md`

Before implementing a new graph, gate, task runner or evidence format, perform a source and API inventory of these and related existing files. Reuse stable schemas where semantically appropriate; if a change is needed, make a versioned, backward-compatible proposal and tests.

## 12. Non-goals and truth boundary

This proposal does not:
- claim universal autonomy or error-free generated code;
- prove that adding agents improves quality;
- equate passing tests with formal correctness;
- infer that all dependencies or external side effects are observable;
- silently auto-merge, delete archives, mutate canonical authority, publish secrets or deploy to production;
- claim the global novelty of the synthesis;
- claim the described components are implemented or verified.

A release report must distinguish `PROPOSED`, `SPECIFIED`, `IMPLEMENTED`, `TESTED`, `VERIFIED`, and `DEPLOYED`, with evidence references for every state transition.

## 13. Research references

1. Kim et al. (2026), *Capable language models can outgrow the benefits of collaboration*. https://doi.org/10.1038/s42256-026-01268-y
2. Geng & Neubig (2026), *Effective Strategies for Asynchronous Software Engineering Agents*. https://arxiv.org/abs/2603.21489
3. Han et al. (2026), *TDFlow: Agentic Workflows for Test Driven Development*. https://aclanthology.org/2026.eacl-long.70/
4. Debenedetti et al. (2024), *AgentDojo: A Dynamic Environment to Evaluate Attacks and Defenses for LLM Agents*. https://arxiv.org/abs/2406.13352
5. Khan (2026), *Stop Means Stop: Measuring and Repairing the Enforcement Gap in Agent-Framework Control Primitives*. https://arxiv.org/abs/2607.14166
6. Li (2026), *Where Does Exactly-Once Live? Model, Harness, and Tool-Contract Effects on Duplicate Side Effects in LLM Agents*. https://arxiv.org/abs/2609.29095
7. Chen et al. (2026), *Cordon: Semantic Transactions for Tool-Using LLM Agents*. https://arxiv.org/abs/2606.17573
8. SLSA, Build Provenance specification. https://slsa.dev/spec/v1.2/
9. OpenTelemetry specifications and documentation. https://opentelemetry.io/docs/
10. CodeQL data-flow and taint tracking documentation. https://codeql.github.com/docs/
11. Hypothesis property-based testing. https://hypothesis.readthedocs.io/
12. OpenHands Software Agent SDK. https://github.com/OpenHands/software-agent-sdk

Research maturity varies. Preprints, benchmark results and vendor/tool documentation must be re-evaluated against pinned versions and target workloads before adoption.
