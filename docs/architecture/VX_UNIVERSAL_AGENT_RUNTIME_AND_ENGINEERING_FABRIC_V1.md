# VX Universal Agent Runtime & Engineering Fabric V1

**Status:** Proposed engineering contract; runtime admission pending  
**Canonical authority:** VAIXLNS  
**Discovery / innovation:** NEXENT  
**Universal agent execution boundary:** VX Runtime + VX Federation Gate  
**Registry:** `registry/vx-agent-runtime-profiles.v1.json`  
**Control envelope:** `schemas/vx-tool-action-envelope.v1.schema.json`

## 1. Non-negotiable architecture decision

**Every agent runs as a VX-governed agent. No agent is allowed to call tools directly.**

A “VX agent” is a logical agent identity and capability profile running through the VX execution boundary. Specialized names such as VX-Code, VX-Systems, VX-Math, VX-Research or VX-Security denote profiles/specializations; they do not automatically imply separately deployed servers or provider connections.

Every request to a tool—including requests originating from another agent—must be converted into an action envelope and evaluated by the VX Tool Control Gate. The gate checks authenticated identity, registered tool/version, capability, target scope, authority intersection, policy version, budgets, proof freshness, approval and stop state. The adapter may execute only the exact allowed action.

```text
VAIXLNS CONSTITUTION / CANONICAL GOVERNANCE
                    │
                    ▼
              NEXENT DISCOVERY
          research • gap detection • design
                    │ candidate only
                    ▼
            VX ENGINEERING ORCHESTRATOR
         task DAG • routing • bounded parallelism
                    │
          ┌─────────┼──────────┬────────────┐
          ▼         ▼          ▼            ▼
       VX-CODE   VX-SYSTEMS  VX-MATH     VX-RESEARCH ...
          │         │          │            │
          └─────────┴──────────┴────────────┘
                    │
          VX FEDERATION GATE
                    │
          ACTION ENVELOPE + POLICY
                    │
         AUTHORITY / SCOPE / BUDGET
                    │
         APPROVED VX TOOL ADAPTER ONLY
                    │
       SANDBOX / BRANCH / READ-ONLY TARGET
                    │
          EVENTS • STATE • EVIDENCE
                    │
       TESTS • REPLAY • INDEPENDENT REVIEW
                    │
       ARC-X / ASSURANCE / FINALITY GATES
                    │
        GOVERNANCE-APPROVED ADOPTION ONLY
```

The diagram is the intended architecture, not proof that the entire runtime is already deployed.

## 2. Universal agent wrapper

Every agent role MUST bind to the same core contract:

- **Identity:** stable agent ID, role, version, owner, status and provenance.
- **VX binding:** runtime boundary, federation identity and the same action-envelope contract.
- **Capabilities:** only registered capabilities with typed input/output contracts.
- **Authority ceiling:** explicit maximum tier; never inherited from the model, prompt, task priority or parent request.
- **Tool access:** named tool classes and configured adapter IDs; no unrestricted tool namespace.
- **Scope:** exact repositories, branches, paths, APIs, data classes, environments and network destinations.
- **Budget:** wall time, retries, parallelism, network calls, write volume, token/compute use and spend.
- **Context:** source artifacts, assumptions, uncertainty, task/dependency IDs and retention rules.
- **Evidence:** inputs, output digests, tool versions, event references, tests, verifier identity and limitations.
- **Stop/recovery:** timeout, abort, quarantine, checkpoint, replay and re-admission behavior.
- **Lifecycle:** ROLE_TEMPLATE → CONFIGURED → TESTED → VERIFIED → ADMITTED → MONITORED, with HOLD/QUARANTINED/REVOKED/DEPRECATED paths.

An agent is not admitted because its profile exists. Missing provider/tool configuration yields `NOT_CONFIGURED/HOLD`. Secrets stay in secret managers and are never inserted into prompts, tool output or audit logs.

## 3. Agent roster and extension rule

The initial role catalog defines 35 logical role templates for the common engineering path:

- Orchestration and architecture
- Research and innovation discovery
- Software implementation and systems/runtime engineering
- Mathematics, physics and numerical simulation
- Compilers, languages and intermediate representations
- Data, databases, infrastructure and cloud plans
- Hardware/robotics simulation and safety review
- Index/registry and provenance curation
- Prompt/skill engineering
- Prototype implementation and branch delivery
- QA, adversarial testing and independent verification
- Security, release preparation and operations/recovery
- Cost/resource analysis and technical writing

Add new specialties by creating a versioned profile that conforms to `schemas/vx-agent-runtime-profile.v1.schema.json`. A new profile must not create a bypass or new authority root. The catalog’s 35 entries are role templates only; they do not claim 22 live agents or configured provider connections.

## 4. Engineering task graph — optimize speed without weakening assurance

Represent a request as a DAG of small, typed work packages. Every node includes:
`task_id, parent_id, goal, acceptance_criteria, non_goals, inputs, dependencies, required_capability, target_scope, risk, budget, tools, outputs, checks, evidence_requirements`.

Execution rules:

1. Normalize intent and acceptance criteria once; ask for missing high-impact facts only where a safe default does not exist.
2. Reuse the canonical index, repository maps, source hashes, prior verified artifacts and cached test results only when their version/freshness conditions still match.
3. Split independent tasks and run them in parallel within the global and per-agent concurrency budgets.
4. Execute dependent tasks only after dependency outputs pass their declared contracts.
5. Route tasks to the narrowest qualified VX profile; do not send every task to every agent.
6. Have the orchestrator aggregate outputs by artifact identity, not by fluent summary; preserve conflicts instead of hiding them.
7. Run fast deterministic checks first (schema, formatting, static validation, unit tests), then integration, negative/adversarial, replay and independent review as required by risk.
8. Use incremental testing when dependency and scope analysis proves the cache valid; otherwise rerun affected gates.
9. On failure, stop only the impacted branch of the DAG where safe, preserve evidence, and continue independent branches if policy permits.
10. Use bounded retries and a checkpoint. Never remove safety gates to meet a speed target.

**Latency model:** `Total time ≈ critical-path duration + dispatch/merge overhead`, not the sum of all independent task durations. Parallelism is limited by tool quotas, resource budgets, dependency edges and review capacity.

## 5. Unified engineering lifecycle

```text
INTAKE
→ NORMALIZE INTENT + ACCEPTANCE
→ SOURCE / INDEX / LINEAGE LOOKUP
→ BUILD TASK DAG
→ CAPABILITY + AGENT MATCH
→ VALIDATE AUTHORITY / SCOPE / BUDGET
→ EXECUTE VIA VX GATE
→ BUILD / SIMULATE / TEST
→ COLLECT ARTIFACTS + EVENT RECEIPTS
→ VERIFY CONTRACTS + FAILURE CASES
→ INDEPENDENT REVIEW
→ PR / RELEASE PREPARATION
→ EXPLICIT GOVERNANCE APPROVAL
→ CONTROLLED PROMOTION
→ MONITOR / REPLAY / REVALIDATE
```

Discovery and proposal may be automated. Merge to protected branches, canonical policy changes, deployment, financial transactions, destructive operations, public irreversible publishing and physical actuation remain separately gated and denied by default.

## 6. Cross-agent contract

Every handoff contains:
`workflow_id, task_id, sender_agent_id/version, recipient_agent_id/version, requested_capability, goal, inputs, expected_schema, dependencies, assumptions, uncertainty, evidence_refs, risk, budget, target_scope, requested_authority, deadline, idempotency_key`.

The recipient may accept, refuse or return HOLD. It cannot expand inherited task scope. The caller cannot mark a reviewer as having run unless a real adapter response, identity/version, artifact digest and receipt exist. Consensus does not override a failed hard gate.

## 7. Operating modes for fast but controlled execution

| Mode | Allowed behavior | Blocked behavior |
|---|---|---|
| READ_ONLY | Search/index/read approved artifacts | Any mutation |
| ADVISORY | Parallel research, analysis, design and patch proposals | Tool side effects |
| SANDBOX | Bounded build/code/data simulation in isolated workspace | External production changes |
| BRANCH_WORK | Explicit branch/path writes and PR preparation | Protected-branch merge or release |
| RELEASE_PREPARATION | Reproducible candidate, manifest, SBOM, rollback plan | Publish/deploy |
| PRODUCTION | Only a separately admitted, target-bound action | Any action outside the approved envelope |

Changing modes is itself an authorized policy action. An agent cannot switch the system into a more permissive mode.

## 8. First implementation slice

Implement a narrow, auditable vertical slice before connecting every possible tool:

1. Validate agent-profile and action-envelope schemas.
2. Load a trusted actor profile, admitted tool profile and policy version.
3. Compute effective authority as the intersection of actor ceiling, tool ceiling, task scope, environment policy and valid approval.
4. Return a deterministic `ALLOW/HOLD/QUARANTINE/REJECT` decision with reason codes.
5. Execute only through one harmless, read-only test adapter.
6. Persist request, decision and result receipt, and prove unknown tools fail closed.
7. Add sandbox mutation only after isolation and budget tests pass.
8. Add branch writes only after target allowlists, idempotency, diff review and CI evidence pass.
9. Connect the existing event/ledger/replay and assurance facilities through explicit contracts.
10. Admit additional adapters one at a time; do not mark them live from registry entries alone.

## 9. Acceptance conditions

The VX agent fabric is not admitted until tests show that:
- every agent-to-tool path crosses VX;
- no direct bypass route exists in the configured runtime;
- missing or unknown adapters remain HOLD/NOT_CONFIGURED;
- delegated tasks cannot widen parent scope or authority;
- expired approvals, stale proofs and changed action digests stop execution;
- budget overruns and emergency stops halt the relevant work;
- task outputs preserve their source and version lineage;
- agent self-approval and automatic canonical promotion are impossible;
- separate verifiers actually run for claims that require independence;
- replay and recovery preserve event history;
- integration tests prove the behavior beyond this specification.

## 10. Status boundary

This document and the linked registry/schema files establish a proposed contract and role catalog. They do not establish runtime enforcement, provider connectivity, agent deployment, server availability, production readiness or successful end-to-end execution. Those claims require the corresponding code, tests, runtime observations and admission decision.
