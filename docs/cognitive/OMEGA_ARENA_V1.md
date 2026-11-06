# Ω-Arena v1 — Capability Tournament

**Status:** SPECIFIED
**Authority:** project.genome::v1.0.0
**Canonical Owner:** VAIXLNS
**Runtime Owner:** VX
**Activation Fabric:** VLNS

## 1. Objective
Ω-Arena is a controlled evaluation environment in which provider adapters, model compositions, tools, and capability strategies compete on the same admitted problem under identical governance, reproducibility, and evidence rules.

The Arena does not crown a universally superior model. It identifies the best verified capability composition for a task, context, constraints, and evidence standard.

## 2. Immutable evaluation boundary
Before execution, VX freezes: arena_id and evaluation window; task corpus and hidden tests; capability contract; permitted tools and permissions; provider adapter versions; runtime/environment fingerprint; scoring rubric and weights; judge policy/version; security policy; evidence schema; replay requirements.

Participants cannot modify these inputs after admission.

## 3. Arena lifecycle
DRAFT → ADMITTED → FROZEN → READY → RUNNING → VERIFYING → SCORED → AUDITED → PROMOTION_REVIEW → CLOSED
Failure paths: QUARANTINED, INVALIDATED, REJECTED.

## 4. Match unit
Each match contains: problem specification; candidate composition; isolated execution context; observations/events; outputs/artifacts; verification tests; adversarial attacks; replay package; score breakdown; evidence chain; verdict.

## 5. Tournament modes
- Single-task: one task, multiple providers/compositions.
- Cross-domain: same capability contract across independent domains.
- Adversarial: deliberate attacks for correctness, security, robustness, hallucination, specification drift, and failure recovery.
- Repair: bounded repair opportunities, scoring initial quality and recovery quality.
- Composition: VLNS may compose multiple providers/minds; the composition is evaluated as one candidate while preserving component lineage.

## 6. Seven-day operating window
Day 0 — freeze corpus, contracts, environments, and scoring.
Day 1 — baseline providers and adapter conformance.
Day 2 — capability and reasoning trials.
Day 3 — engineering/execution trials.
Day 4 — adversarial and security trials.
Day 5 — repair, recovery, and composition trials.
Day 6 — replay, cross-validation, and independent judge audit.
Day 7 — final scoring, promotion review, and evidence package.

A provider may be removed or quarantined during the window for safety or integrity violations; such action is itself an Evidence Event.

## 7. Judge separation
A candidate must never be its own authoritative judge. VX separates candidate execution, deterministic validators, independent judges, evidence aggregation, and governance admission.

Where an LLM judge is used, deterministic tests and evidence remain authoritative for mechanically verifiable claims.

## 8. Promotion principle
The Arena promotes capabilities, not model brands.

A candidate result may produce REJECTED, OBSERVED, CANDIDATE, VERIFIED, or ADOPTED states. VERIFIED requires a deterministic/reproducible proof chain; ADOPTED additionally requires governance approval.

## 9. Required evidence
Every scored match references an immutable evidence bundle containing input hash, adapter/version, environment fingerprint, event hashes, artifact hashes, validator outputs, score calculation, judge records, replay status, and final verdict.

No evidence bundle means no authoritative score.