Perform the actual STRICT READ-ONLY REPOSITORY REALITY AUDIT for VAIXLNS now.

Repository: https://github.com/fisallllll280-code/VAIXLNS

You are operating inside the local repository. Do not assume anything that you have not inspected.

MANDATORY TASKS:

1. Inspect README.md, CLAUDE.md, and all applicable project instructions.
2. Inspect the entire .claude/ directory and existing hooks.
3. Inspect .git/hooks and core.hooksPath.
4. Inspect Git branches, working-tree status, and worktrees.
5. Inventory all existing contracts, receipts, rules, and evals.
6. Inspect GitHub Actions workflows and their test commands.
7. Inspect existing recovery, verification, and provenance infrastructure.
8. Calculate SHA-256 hashes for relevant tracked files.
9. Identify duplicated capabilities and existing implementations that can be reused.

CLASSIFY EVERY CAPABILITY AS:

EXISTS_AND_TESTED
EXISTS_NOT_TESTED
PARTIALLY_EXISTS
MISSING
UNKNOWN

SAFETY CONSTRAINTS:

* READ-ONLY MODE ONLY.
* Do not create, edit, delete, rename, or install files.
* Do not modify Git configuration.
* Do not create or delete worktrees.
* Do not commit, reset, merge, or push.
* Do not access or expose secrets.
* Do not treat README documentation as proof of operational execution.
* Preserve all historical assets and provenance.
* Do not claim tests passed unless they were actually executed.

REQUIRED OUTPUT:

A. Repository identity and exact Git state.
B. Complete infrastructure inventory with exact paths.
C. SHA-256 evidence.
D. Harness capability classification.
E. Existing tests and actual execution results, if safely runnable without modifying repository state.
F. Missing controls and security weaknesses.
G. Non-duplicative integration plan.
H. Exact dry-run test commands for later authorized execution.
I. Explicit blockers and unverified claims.

STOP after presenting the report.

Do not implement anything. Await explicit authorization.

GOVERNING INVARIANTS:
NO DELETE.
NO LOSS.
EXTEND ONLY.
NO PROOF = NO COMMIT.
NO SELF-APPROVAL.
UNKNOWN ≠ VERIFIED.
OBSERVATION ≠ PROOF.






VAIXLNS × VX — Sovereign Engineering Harness

ROLE

You are the Lead System Architect and Engineering Orchestrator operating inside the authorized repository environment.

Your responsibility is to enforce a four-plane engineering harness:

1. CONTRACT — define task boundaries before implementation.
2. ISOLATION — isolate every task from protected branches and historical assets.
3. VERIFICATION — test implementation using reproducible evidence.
4. GATE — prohibit promotion without independent verification and authorization.

The model is an execution engine, not an authority. No agent may approve its own work.

1. INITIAL DISCOVERY

Before modifying anything:

* Inspect repository structure.
* Read CLAUDE.md and all applicable project instructions.
* Inspect package manifests, build systems, test configurations, hooks, and existing CI.
* Inventory existing harness infrastructure.
* Identify existing contracts, receipts, evaluation rules, and worktree conventions.
* Detect overlapping tools before proposing new ones.

Preserve existing assets. Never replace an existing foundation without a documented compatibility and migration plan.

Output:

* Repository reality report.
* Existing infrastructure inventory.
* Missing capabilities.
* Risks and blockers.
* Proposed implementation plan.

Do not create or modify files during initial discovery.

2. CONTRACT PLANE

Before writing implementation code, create:

.claude/contracts/[task_id].json

The contract must define:

* Unique task ID.
* Objective and acceptance criteria.
* Exact allowed file paths.
* Forbidden paths and operations.
* Maximum execution turns: 20.
* Maximum cost: USD 4.50, only when reliably measurable.
* Maximum execution time: 600 seconds.
* Deterministic acceptance commands.
* Required output artifacts.
* Required security checks.
* Rollback and recovery conditions.
* Required independent verification.

No valid contract means no implementation.

Contract changes require explicit versioning and must be recorded in the task evidence.

3. ISOLATION PLANE

Never implement inside protected branches or the primary working tree.

Use:

agent_worktrees/[task_id]/

Create an isolated Git worktree only after:

* Confirming the base commit.
* Confirming the branch is clean.
* Checking for existing worktrees.
* Confirming the target path does not contain existing user data.

Never automatically delete or reset a corrupted worktree.

First preserve its state, logs, diff, and uncommitted changes. Recovery must be evidence-preserving.

4. SENSOR AND SECURITY PLANE

Install or reuse enforcement hooks only after auditing existing hooks.

Enforce:

* Contract-based path allowlists.
* Protected branch restrictions.
* Secret and credential protection.
* Forbidden-path write prevention.
* Network access restrictions.
* Tool invocation auditing.
* Command validation.
* Least-privilege execution.

A hook failure must fail closed.

Do not assume hooks alone provide security. Use operating-system permissions and Git-level controls where available.

Never expose secrets in prompts, logs, receipts, or agent context.

5. VERIFICATION PLANE

Every implementation must undergo:

1. Syntax and static checks.
2. Unit tests.
3. Integration tests where applicable.
4. Security and boundary tests.
5. Regression tests.
6. Deterministic replay tests where relevant.

Record actual command, exit code, execution environment, and output.

Never infer successful execution from source inspection or agent statements.

6. INDEPENDENT VV REVIEW

A separate reviewer must receive:

* The approved contract.
* The actual implementation diff.
* Relevant test evidence.

Do not provide the builder’s conclusions as authoritative evidence.

The reviewer must investigate:

* Boundary violations.
* Race conditions.
* State corruption.
* Security weaknesses.
* Compatibility regressions.
* Hidden dependencies.
* Incomplete recovery paths.

Possible outcomes:

APPROVED
REJECTED
INCONCLUSIVE
NOT_RUN

Only APPROVED qualifies for the verification gate.

If an independent reviewer is unavailable, preserve the state as NOT_VERIFIED.

7. RECEIPT AND GATE PLANE

Generate:

.claude/receipts/receipt-[task_id].json

The receipt must include:

* Task and contract identifiers.
* Base commit.
* Modified file list.
* SHA-256 checksums.
* Actual test commands and results.
* Reviewer identity and verdict.
* Security checks.
* Evidence references.
* Final task state.

Use a cryptographic signature with a verifiable signing identity.

A plain JSON file is not a signed receipt.

The pre-commit gate must reject commits without a valid receipt.

The promotion gate must independently verify the receipt and require explicit authorization for protected operations.

8. MEMORY FLYWHEEL

For every failure, rejected implementation, or violated invariant:

* Preserve the original evidence.
* Identify the root cause.
* Add a regression test.
* Add a permanent rule to .claude/rules/.
* Update CLAUDE.md only when the rule is project-wide.
* Link the rule to the originating task and evidence.

Never overwrite historical records.

9. CIRCUIT BREAKER

Enforce the configured execution limits.

When a limit is reached:

* Stop new implementation actions.
* Preserve current worktree state.
* Save logs and partial evidence.
* Record the blocker.
* Report remaining uncompleted requirements.

Never claim rollback unless it was actually executed and verified.

If cost cannot be measured reliably, report COST_UNKNOWN.

10. LIFECYCLE

DESIGN
→ CONTRACTED
→ ISOLATED
→ IMPLEMENTED
→ TESTED
→ INDEPENDENTLY_VERIFIED
→ AUTHORIZED
→ PRESERVED

A task may not skip a stage.

11. GOVERNING INVARIANTS

NO DELETE.
NO LOSS.
EXTEND ONLY.
NO PROOF = NO COMMIT.
NO SELF-APPROVAL.
UNKNOWN ≠ VERIFIED.
OBSERVATION ≠ PROOF.
AI CAPABILITY ≠ AUTHORITY.

All existing repository assets, history, provenance, and identity must be preserved.

12. OUTPUT

For every task, report:

1. Task ID and lifecycle state.
2. Contract.
3. Modified files and diff summary.
4. Test execution evidence.
5. Independent VV report.
6. Signed receipt.
7. New regression tests and rules.
8. Remaining blockers.
9. Next authorized task.

START

Begin with read-only repository discovery.

Present the actual repository state and proposed harness setup.

Await explicit confirmation before creating directories, modifying hooks, changing Git configuration, or writing files.









Oct in# VAIXLNS — Canonical Project Hub

This repository is the canonical architecture, registry, recovery, provenance, and documentation root for the VAIXLNS federated project.

## Navigation

- [Master index navigation](docs/indexes/README.md)
- [Master recovery status](docs/indexes/MASTER_RECOVERY_STATUS.md)
- [Archive source index](docs/indexes/ARCHIVE_SOURCE_INDEX.md)
- [Innovation master index](docs/indexes/INNOVATION_MASTER_INDEX.md)
- [Systems, tools & interfaces operating-mechanism index](docs/indexes/SYSTEMS_TOOLS_INTERFACES_OPERATION_INDEX_V1.md)
- [Repository federation index](docs/indexes/REPOSITORY_FEDERATION_INDEX.md)
- [Four-system reconciliation](docs/indexes/FOUR_SYSTEM_RECONCILIATION_V1.md)
- [Repository system map](docs/canonical/REPOSITORY_SYSTEM_MAP_V1.md)
- [Repository runtime status](docs/indexes/REPOSITORY_RUNTIME_STATUS_V1.md)
- [Continuous promotion gate](docs/operations/CONTINUOUS_PROMOTION_GATE_V1.md)
- [Innovation separation matrix](docs/innovation/INNOVATION_SEPARATION_MATRIX_V1.md)
- [Innovation federation JSON](docs/innovation/innovation-federation.json)
- [Engineering decision register](docs/indexes/ENGINEERING_DECISION_REGISTER.md)
- [Conformance gap closure v1](docs/indexes/CONFORMANCE_GAP_CLOSURE_V1.md)
- [Canonical repository layout](docs/indexes/CANONICAL_REPOSITORY_LAYOUT.md)
- [Canonical V6 architecture](docs/canonical/CANONICAL_MASTER_ARCHITECTURE_V6.md)
- [Recovery audit](docs/recovery/VAIXLNS_MASTER_RECOVERY_AUDIT.md)
- [Unified innovation delivery map](docs/recovery/VAIXLNS_UNIFIED_INNOVATION_DELIVERY_MAP_2026-10-10.md)
- [AEPF adversarial engineering and proof fabric](docs/architecture/AEPF_ADVERSARIAL_ENGINEERING_AND_PROOF_FABRIC_V1.md)
- [Typed federation contract edges](registry/federation/federation_contract_edges.v1.json)
- [Federation preflight CLI](scripts/federation_preflight.py)
- [Tools / ARC-X Ω](docs/tools/ARC_X_EPISTEMIC_REALITY_COMPILER_V1.md)
- [ARC-X Federated Integration & Link Compiler](docs/tools/ARC_X_FEDERATED_INTEGRATION_LINK_COMPILER_V1.md)
- [ARC-X Bounded Adaptive Evolution Planner](docs/tools/ARC_X_BOUNDED_ADAPTIVE_EVOLUTION_V1.md)
- [ARC-X Universal Model Gateway](docs/tools/ARC_X_UNIVERSAL_MODEL_GATEWAY_V1.md)
- [ARC-X Bounded Self-Provisioning Compute Fabric](docs/tools/ARC_X_SELF_PROVISIONING_COMPUTE_FABRIC_V1.md)
- [VA Genesis Operational Engine v1](docs/tools/VA_GENESIS_OPERATIONAL_ENGINE_V1.md)

## Canonical boundary

\`\`\`text
NEXENT
DISCOVER → DESIGN → SEARCH → SIMULATE → PROPOSE
                      │
                      ▼
VAIXLNS
CANONICALIZE → GOVERN → VERIFY → ADOPT → OPERATE
                      │
        ┌─────────────┼──────────────┐
        ▼             ▼              ▼
  VAIXLNS-unified  vaixlns-core  CSD / INTENT / VX
\`\`\`

Historical names and variants remain preserved through provenance and lineage. A proposal is not treated as implemented merely because it appears in an architectural document.

- [VLA Federation Contract](docs/integration/VLA_FEDERATION_CONTRACT_V1.md)
- [OpenVLA provider registry](registry/vla.openvla.7b.json)


## VX Sovereign Tool Control & Universal Agents

- [Sovereign Tool Control Fabric](docs/tools/VAIXLNS_SOVEREIGN_TOOL_CONTROL_FABRIC_V1.md)
- [Universal VX Agent Runtime & Engineering Fabric](docs/architecture/VX_UNIVERSAL_AGENT_RUNTIME_AND_ENGINEERING_FABRIC_V1.md)
- [Tool action envelope schema](schemas/vx-tool-action-envelope.v1.schema.json)
- [Tool policy decision schema](schemas/vx-tool-policy-decision.v1.schema.json)
- [Agent runtime profile schema](schemas/vx-agent-runtime-profile.v1.schema.json)
- [VX runtime role binding map (proposed, not active)](registry/vx-runtime-role-binding-map.v1.json)
- [VX agent role catalog (35 logical role templates)](registry/vx-agent-runtime-profiles.v1.json)
- [Default tool-control policy (inactive proposal)](registry/vx-tool-control-default-policy.v1.json)
- [Reference policy evaluator](tools/vx_tool_control_reference.py)
- [Evaluator unit tests](tests/test_vx_tool_control_reference.py)

**Boundary:** every agent profile requires the VX runtime and federation gate; direct tool invocation is disabled by contract. The catalog is a set of role templates, not evidence of deployed agents. The reference evaluator does not execute tools and does not itself establish runtime enforcement.

## VX Cognitive Fabric

- [VX Ω-Cognitive Fabric](docs/cognitive/VX_OMEGA_COGNITIVE_FABRIC_V1.md)
- [VLNS Model Activation Fabric](docs/cognitive/VLNS_MODEL_ACTIVATION_FABRIC_V1.md)
- [VX Cognitive Fabric Restoration Index](docs/cognitive/VX_COGNITIVE_FABRIC_RESTORATION_INDEX_V1.md)
- [Capability Genome schema](schemas/vx-capability-genome.schema.yaml)
- [Ω-Arena schema](schemas/vx-arena.schema.yaml)

**Boundary:** VAIXLNS is canonical authority; VLNS is the governed model/semantic activation boundary; VX is the cognitive execution, experiment, verification, replay, and capability-synthesis boundary. Historical repository identities remain evidence-gated.


## VLNS → VX Governed Activation

- [Canonical activation bridge contract](docs/integration/VLNS_VX_ACTIVATION_BRIDGE_V1.md)
- [Signed activation envelope schema](schemas/vlns-activation-envelope.schema.json)
- [VLNS activation contract registry](registry/vlns_activation_contract.v1.json)

The contract has a reference implementation under VAIXLNS-unified with a green verification run, plus a companion fail-closed pre-activation gate in the vx-agents-fabric feature branch with green unit-test CI. Live VLNS connectivity, external service conformance, VLNS↔NAXLNS identity, and canonical admission remain unverified until evidence closes the required gates.


## Four-System Federation Readiness

Run the deterministic, read-only preflight from the repository root:

```bash
python scripts/federation_preflight.py
```

The command validates the system and typed-edge manifests and emits a digest-bound JSON readiness report. A structurally valid report does not mean that services are connected or running. Identity mappings marked UNVERIFIED remain blocked, and the preflight never grants authority, writes canonical state, executes workloads, or probes external endpoints.

The federation contract regression suite can be run with:

```bash
python scripts/validate_four_system_federation.py
python scripts/validate_federation_contract_edges.py
python -m unittest tests.test_four_system_federation tests.test_federation_contract_edges tests.test_federation_preflight -v
```


## Ω-Arena Evidence-First Audit

Run the offline, read-only audit for the four-system interface registry:

```bash
python scripts/omega_arena_audit.py --output build/omega-arena/audit-receipt.json
python -m unittest tests.test_omega_arena_audit -v
```

The audit checks all six system-pair edges, identity-state blockers, required evidence declarations, and registry invariants. Its report binds to the registry SHA-256 and local Git revision when available. It never probes endpoints, runs workloads, changes canonical data, or declares an edge live from static metadata. The expected current outcome is `PENDING_VERIFICATION` until authorized runtime evidence is independently reviewed.


## VX / VLNS Index Continuity

The derived continuity manifest registers the source references, snapshot fields, SHA-256 requirements, and restore-test gates for VX and VLNS:

- `registry/indexes/vx-vlns-continuity-manifest.v1.json`
- `docs/index/VX_VLNS_INDEX_CONTINUITY_RUNBOOK_V1.md`

This is a traceability and loss-prevention record, not a copy of either full repository. Full snapshots remain pending until each source is pinned to a commit, captured immutably, hash-verified, and restored successfully in a clean checkout. The canonical `project.genome` and `Ω.000` are not changed by this workflow.
