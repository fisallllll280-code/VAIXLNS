# VAIXLNS Deep Agent Cognitive Engineering Register V1

**State:** SPECIFIED / PROPOSAL; research-informed engineering register, not a production-readiness claim.  
**Date:** 2026-10-10  
**Canonical authority:** `project.genome::v1.0.0` → `Ω0_GENESIS_CORE` → `Ω.000`.  
**Owner:** VAIXLNS.  
**Purpose:** Deepen the existing governed agent fabric using findings from Undermind literature searches, without replacing the current 13-role chain, inventing duplicate canonical systems, or equating role records with live model instances.

## 1. Executive determination

The next advancement is not “more agents.” It is **deeper, measurable, independently bounded specialist capability**.

The existing agent operating model already describes identity, role, contracts, evidence, authority scopes, handoffs, failure policy, telemetry, and governed evolution. The existing audit also records a 13-role typed handoff chain and distinguishes those records from live independent model sessions. This register therefore adds a research-derived depth layer over the existing fabric rather than another competing hierarchy.

The most important findings from the Undermind research portfolio are:
- Collaboration can improve some complex tasks but can also degrade strong single-agent performance; architecture selection must be measured against a matched baseline [Kim26] [She26c].
- Handoff topology can drop constraints and spread false beliefs; outcome-only scoring misses important collaboration failures [Maz26b] [Zhu25g].
- A reviewer may identify a defect without causing the next candidate to repair it. Critique uptake must be measured, not assumed [Yan26l].
- Structured DAG decomposition helps tasks with real dependencies, but blind retries can reproduce latent faults and deepen failure cascades [Don24] [Che26q].
- Security and cancellation cannot rely on prompt instructions or framework labels alone; the effect boundary must enforce policy independently [Buh25] [Kha26c] [Pal26].
- Agent workflows need traceable inputs, outputs, decisions, tool effects and provenance across handoffs [Sou25b].
- Benchmarks themselves can reward empty or weakly checked outcomes; use held-out tasks and adversarially strengthened acceptance tests [Zhu25b] [Yu26b].

These are literature-derived directions, not proof that a particular VAIXLNS implementation already has these properties.

## 2. Proposed synthesis: Cognitive Fabric with Evidence-Carrying Handoffs

The proposal combines the existing agent operating model with five specific control mechanisms:
1. **Adaptive topology selection:** choose solo, sequential, parallel subagents, debate, or independent audit according to task dependency, risk, uncertainty, expected coordination cost, and measured benefit.
2. **Constraint-preserving handoffs:** every handoff carries the original task invariants, required outputs, forbidden actions, unresolved questions, and provenance; the receiver explicitly acknowledges and validates those constraints.
3. **Evidence-separated cognition:** each agent labels claims as observed, inferred, hypothesized, contradicted, or unknown and attaches source/evidence references. Consensus cannot convert unsupported claims into facts.
4. **Critique uptake protocol:** when a reviewer rejects or challenges a result, the downstream candidate must either repair it with evidence or return a typed rebuttal that is checked by an independent verifier. Merely logging a criticism is not closure.
5. **Independent effect and completion gate:** an external gate—not the worker or the agent-generated result—enforces task budgets, cancellation, permissions, completion evidence, replay/idempotency requirements, and approval status before side effects.

This is a proposed VAIXLNS synthesis over prior art. Novelty is UNASSESSED until explicit comparison and technical testing establish what is genuinely differentiated.

## 3. Target agent topology

```text
Ω0 / CONSTITUTION / POLICY
          |
          v
INTENT + ACCEPTANCE CONTRACT
          |
          v
TASK / RISK / UNCERTAINTY CLASSIFIER
          |
          v
ADAPTIVE TOPOLOGY SELECTOR
  |            |             |             |
  v            v             v             v
SOLO       SEQUENTIAL      PARALLEL      HIGH-RISK
BASELINE   DEPENDENCY DAG  INDEPENDENT   INDEPENDENT
AGENT      SPECIALISTS     SUBAGENTS     AUDIT / RED-TEAM
  |            |             |             |
  +------------+-------------+-------------+
                       |
                       v
       CONSTRAINT-PRESERVING HANDOFF ENVELOPE
                       |
                       v
            CLAIM / EVIDENCE LEDGERS
                       |
                       v
        SYNTHESIS + CONTRADICTION RESOLUTION
                       |
                       v
        CRITIQUE-UPTAKE / REPAIR / REBUTTAL
                       |
                       v
    TESTS + ADVERSARIAL CHECKS + REPLAY EVIDENCE
                       |
                       v
       INDEPENDENT EFFECT / COMPLETION GATE
                       |
                +------+------+
                |             |
                v             v
           HOLD / REJECT   GOVERNED CANDIDATE
                              |
                              v
                 HUMAN-AUTHORIZED PROMOTION
```

The topology selector is allowed to reduce agent count. It should add collaboration only when expected quality, coverage, or risk reduction justifies its extra cost and latency.

## 4. Agent identity is not model identity

Every permanent logical agent must have a stable record including:
- `agent_id`, version, canonical owner, mission, and bounded scope;
- capabilities and explicit capability exclusions;
- input/output contracts and schema versions;
- allowed tools, data classifications, effects, and permission ceiling;
- required evidence and verification obligations;
- uncertainty representation, known failure patterns, and escalation target;
- memory read/write policy and expiration rules;
- model/provider identity per invocation when actually available;
- evaluation suite, last evidence revision, and observed performance distribution.

A role may be served by multiple approved models, and one model may serve several roles. Do not claim that named roles are distinct live minds unless run evidence demonstrates independent invocations and useful differentiated contributions.

## 5. Evidence-carrying handoff contract

Each handoff should carry a structured immutable envelope:
- task, parent task, source agent, target agent, and trace IDs;
- base revision and content digests of all input artifacts;
- intent, acceptance criteria, invariants, constraints, and prohibited effects;
- upstream claims with evidence references and epistemic state;
- unresolved conflicts, uncertainty, missing evidence, and prior failed attempts;
- allowed capabilities, data scope, deadline, retry ceiling, and compute/cost budget;
- expected output schema and verification obligations;
- receiver acknowledgement of constraints;
- completion state, tool trace, output digest, and failure/recovery status.

The receiver must reject malformed, stale, out-of-scope, or unverifiable envelopes. It must not silently discard a constraint. Constraint loss is recorded as a collaboration failure, even if the final answer appears plausible.

## 6. Adaptive topology policy

Select the least expensive topology likely to meet the task's acceptance contract:
- **Solo baseline:** use for bounded, well-understood tasks; also run as the comparison baseline for evaluation.
- **Sequential specialist chain:** use when one stage's typed artifact is a real prerequisite for the next stage.
- **Parallel subagents:** use for independent evidence gathering, independent test partitions, or separable alternatives with controlled merge contracts.
- **Debate / competing hypotheses:** use when multiple explanations fit the evidence; require explicit discriminating tests, not vote counting.
- **Independent verifier / red team:** use for security-sensitive, high-impact, uncertain, or canonical-promotion candidates.
- **Human escalation:** use for missing authority, irreconcilable conflicts, insufficient evidence, unexpected side effects, or risk above the declared threshold.

The router should record why it selected a topology and compare prediction with observed outcomes. Agent count and number of messages are not performance metrics.

## 7. Critique uptake and disagreement protocol

A reviewer output must be typed as `BLOCKER`, `MATERIAL_RISK`, `CORRECTION`, `QUESTION`, or `NON_BLOCKING`, with evidence and the affected acceptance criterion.

For a material finding, the next candidate must emit one of:
- `REPAIRED`: a changed artifact plus tests that directly address the finding;
- `REBUTTED`: a reasoned response with evidence and an independent adjudication path;
- `UNRESOLVED`: a remaining uncertainty that forces HOLD when it violates a hard gate.

The workflow records whether the critique changed the artifact and whether the correction actually eliminated the failure. Reviewer precision and downstream repair success are measured separately.

## 8. Independent gate and bounded execution

The execution/effect gate is outside the model-controlled worker. It must:
- authorize every consequential effect using task-scoped identity and current policy;
- pin the exact action, target, arguments, base revision and expected effect;
- enforce a global attempt and cost budget, deadlines, cancellation, and maximum concurrency;
- prevent sibling tasks from performing a rejected or paused action;
- use idempotency keys or explicit compensation when exactly-once effects cannot be guaranteed;
- fail closed on stale approval, changed action, unknown capability, malformed evidence, or unavailable authorization service;
- record append-only event/evidence references and distinguish intended effect from observed effect;
- require human approval for external publishing, privileged changes, canonical writes and irreversible operations.

A hash chain can reveal some tampering; it does not prove evidence truth, completeness, or the legitimacy of the actor.

## 9. Memory is a versioned evidence system, not shared chat

Use three logically distinct stores:
1. **Canonical facts and authority:** only governed source records; no agent self-promotion.
2. **Task working memory:** short-lived hypotheses and intermediate artifacts bound to task and revision.
3. **Experience / failure memory:** prior failures, minimized counterexamples, successful repair patterns and applicability limits.

Every memory entry records source, revision/hash, timestamp, epistemic state, scope, retention policy, and invalidation conditions. Similarity search may retrieve candidate memory, but cannot change it into truth. Contradictions remain visible and source-bound. Stale memory must be revalidated against the current repository/environment before it can influence an action.

## 10. Server and tool fabric

All agent/tool access goes through registered adapters with typed contracts, health checks, auth scopes, quotas, timeouts, data classification, and version pins.

- Default new integrations to read-only.
- Keep provider credentials outside agent-visible prompts and artifacts.
- Use isolated workers for code execution and restrict filesystem and network access.
- Keep long-running task state and evidence outside model context.
- Enforce a durable task lifecycle with bounded retries, cancellation and idempotency.
- Test partial outages, stale credentials, hung workers, duplicate delivery, race conditions, provider changes, and failed compensation.
- Treat tool discovery as inventory only; it is not connection, authentication, or production readiness.

## 11. Evaluation: prove each agent earns its cost

Every new agent or topology must be tested against a strong solo baseline with matched model/tool access, task set, time budget, token/compute budget, and evaluation oracle.

Measure:
- task acceptance rate and independently judged correctness;
- constraint-retention rate across each handoff;
- unsupported-claim rate and counterevidence coverage;
- reviewer finding precision, critique uptake, and verified repair rate;
- error cascade radius and recovery rate by injected failure mode;
- policy violations, unauthorized effects and scope expansion (target: zero);
- p50/p95 completion latency and queue delay;
- cost per accepted outcome, not cost per message;
- duplicate work, redundant context, and model/tool utilization;
- reproducibility, provenance completeness and held-out regression rate.

Use randomized or paired task assignments where practical, repeated runs for stochastic behavior, held-out tests, adversarial cases, and explicit oracle checks. Publish uncertainty intervals and the tested workload. Do not extrapolate task-specific gains to the whole system.

Suggested adoption rule: keep a topology only when it improves a predeclared quality/risk objective or offers a justified quality-latency trade-off without violating hard safety gates. Remove or downgrade agents that add cost without distinct measured capability.

## 12. Adversarial evaluation suite

At minimum, test:
1. **Constraint decay:** inject a critical requirement at the first stage and test whether every downstream stage preserves it.
2. **False-belief contagion:** seed one incorrect claim and measure whether later agents independently verify or merely repeat it.
3. **Minority evidence loss:** place decisive evidence in one parent branch and observe whether synthesis drops it.
4. **Critique ignored:** give the reviewer a valid counterexample and check that the next candidate repairs the defect or remains blocked.
5. **Prompt injection:** place malicious instructions in repository content, web results and tool output; verify effect controls hold.
6. **Stale authority:** invalidate a grant after planning but before commit; the side effect must not occur.
7. **Cancellation race:** pause or cancel a task while a parallel worker is poised to write.
8. **Duplicate/replay:** replay task events and prove that non-idempotent external effects are not silently duplicated.
9. **Budget exhaustion:** force a retry/repair loop and verify the independent global ceiling.
10. **Benchmark gaming:** include empty, partial, flaky and incorrect outputs that can accidentally satisfy weak success criteria.
11. **Memory poisoning/staleness:** introduce contradictory or outdated evidence and verify scope/lineage-aware retrieval.
12. **Single-agent comparison:** demonstrate that collaboration actually beats the matched baseline on this task class.

## 13. New VAIXLNS-specific candidate mechanisms

These are proposed combinations, not yet established novel inventions:
- **Constraint Survival Ledger (CSL):** a per-constraint trace from original intent to every consuming task, with explicit present/absent/changed status and a gate on missing critical constraints.
- **Critique-to-Repair Coupling (CRC):** an event-linked protocol that measures if a challenge was acknowledged, repaired, rebutted, or left unresolved, then verifies the resulting artifact.
- **Topology Fitness Controller (TFC):** selects solo/sequential/parallel/debate/audit using measured task-family outcomes, coordination cost and risk—not a fixed multi-agent pattern.
- **Independent Effect Guard (IEG):** a model-independent admission boundary for side effects, approvals, budgets, cancellation and idempotency.
- **Capability Contribution Ledger (CCL):** measures each role's marginal contribution by ablation or paired comparison and detects redundant roles, harmful interactions and capacity saturation.
- **Evidence-Carrying Cognitive Memory (ECCM):** stores task experience with source, revision, epistemic state, counterexamples and expiration/invalidation logic.

Before giving any candidate a “novel” or “VERIFIED” label, compare it with the cited literature, test an operational definition, build an independently checked prototype, and preserve counterevidence.

## 14. Implementation plan

### Phase A — Contract-only hardening
Add schemas for agent identity, handoff envelope, claims/evidence, critique disposition, and task budget. Validate round-trip serialization and fail-closed handling. Do not add live provider access yet.

### Phase B — Instrument the existing planner
Add explicit constraint manifests, topology-selection reasons, stable task IDs, evidence references and per-stage state transitions to the existing 13-role planner. Preserve its current public contract or version the change.

### Phase C — Build a collaboration benchmark
Create a small controlled suite of repository tasks covering independent discovery, dependency-constrained implementation, contradiction resolution, security review and recovery. Include solo, sequential, parallel and verifier variants under matched budgets.

### Phase D — Add the independent effect gate
Integrate with the existing action-control assurance work. Test cancellation, stale authorization, sibling effects, duplicate delivery, replay and budget exhaustion. A simulator alone is not a live-runtime verification.

### Phase E — Prove incremental benefit
Collect traces, quality judgments, cost and latency across repeated runs. Remove topologies that increase complexity without measurable benefit. Promote only through review and existing governance rules.

## 15. Definition of done

This fabric is not considered live or production-ready until:
- source and revision are pinned;
- agent/hand-off schemas are validated and versioned;
- live provider identity is recorded for every actual invocation;
- constraint retention and critique repair are measured across stage boundaries;
- independent gates enforce, rather than merely describe, budgets and side-effect policy;
- failure injection covers cancellation, retry, stale state, duplicate effects, and recovery;
- collaboration is benchmarked against a matched solo baseline;
- results include reproducible traces, test reports, cost/latency measurements, and limitations;
- external and canonical promotion remains human-authorized.

## 16. Literature trail from Undermind

Use bare cite keys in this repository and retain exact URLs/DOIs when generating the research bibliography:
- [Kim26] Capable language models can outgrow the benefits of collaboration — DOI: 10.1038/s42256-026-01268-y.
- [She26c] An Empirical Study of Multi-Agent Collaboration for Automated Research — DOI: 10.48550/arXiv.2603.29632.
- [Maz26b] AgentCollabBench: Diagnosing When Good Agents Make Bad Collaborators — DOI: 10.48550/arXiv.2605.08647.
- [Zhu25g] Auditing medical multi-agent AI reveals risks of false consensus — https://arxiv.org/abs/2510.10185.
- [Yan26l] Precise but Uncoupled: Reviewer Precision Does Not Guarantee Critique Uptake in Multi-Agent Math Reasoning — DOI: 10.48550/arXiv.2607.15388.
- [Che26q] OrchestraBench: Evaluating Multi-Agent Orchestration Failure Modes, Recovery, and Decomposition Quality — https://arxiv.org/abs/2608.05263.
- [Don24] VillagerAgent: A Graph-Based Multi-Agent Framework for Coordinating Complex Task Dependencies — DOI: 10.48550/arXiv.2406.05720.
- [Buh25] AgentBound: Securing Execution Boundaries of AI Agents — DOI: 10.1145/3808103.
- [Kha26c] Stop Means Stop: Measuring and Repairing the Enforcement Gap in Agent-Framework Control Primitives — DOI: 10.48550/arXiv.2607.14166.
- [Pal26] Formal Policy Enforcement for Real-World Agentic Systems — https://arxiv.org/abs/2602.16708.
- [Sou25b] PROV-AGENT: Unified Provenance for Tracking AI Agent Interactions in Agentic Workflows — DOI: 10.1109/eScience65000.2025.00093.
- [Zhu25b] Establishing Best Practices for Building Rigorous Agentic Benchmarks — DOI: 10.48550/arXiv.2507.02825.
- [Yu26b] SWE-ABS: Adversarial Benchmark Strengthening Exposes Inflated Success Rates on Test-based Benchmark — DOI: 10.48550/arXiv.2603.00520.
- [Hon23] MetaGPT: Meta Programming for Multi-Agent Collaborative Framework — DOI: 10.48550/arXiv.2308.00352.
- [Xia24] Agentless: Demystifying LLM-based Software Engineering Agents — DOI: 10.48550/arXiv.2407.01489.

The Undermind summaries were based on available abstracts and metadata for some works, not necessarily full-text review of every paper. Verify full text and study limitations before elevating a result to an implementation requirement.

## 17. Related VAIXLNS sources and integration boundary

- `docs/agents/VAIXLNS_AGENT_OPERATING_MODEL_V1.md` — existing role contracts and lifecycle.
- `docs/audits/VAIXLNS_DEEP_AGENT_AND_INNOVATION_AUDIT_2026-10-10.md` — current implementation versus live-execution boundary.
- `docs/innovation/VAIXLNS_DEEP_INNOVATION_RECOVERY_AND_READINESS_REGISTER_V1.md` — 97-item portfolio and non-promotion rule.
- `docs/engineering/AGENTIC_SOFTWARE_ENGINEERING_FABRIC_V1.md` and `docs/engineering/OMEGA_MIND_CONTROL_PLANE_V1.md` — open governed Ω Mind design PR lineage; verify their current merge status before depending on them.
- `docs/innovation/INNOVATION_OPERATION_INDEX.md` and `registry/innovation-operation-index.v1.json` — existing generated innovation projections; edit their source inputs, not generated outputs.
- PR #55 — VX Agent Action-Control Assurance registration; keep status PARTIAL unless its full gate and durable ledger integration are verified.
- PR #72 — integrated deterministic 13-role mission planner; planning success is not proof of live provider execution.

This document is a subordinate research/engineering register. It does not change `project.genome`, `Ω0_GENESIS_CORE`, or `Ω.000`, and does not enable provider calls, shell execution, production writes, financial actions, autonomous publishing, or agent self-promotion.
