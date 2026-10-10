# Ω-FRONTIER-002 — Bounded Assurance Engines

Status: IMPLEMENTED_REFERENCE_SLICE; CI_PENDING; NOT_VERIFIED.

## Scope
This slice converts the seven research proposals into a small executable Python reference model. It is not a production authority service, a global model checker, a formal proof, or a connector to live repositories. Originality is not claimed; novelty requires a separate literature and prior-art review.

## Components and contracts

| Engine | Input | Output | Soundness boundary |
|---|---|---|---|
| Assurance Singularity Detector | Assurance-to-dependency map and optional criticality | Ranked shared-dependency candidates | Shared-node impact heuristic; not a global minimum cut unless the full dependency semantics are supplied and solved |
| Uncertainty-to-Action Compiler | Conditions, states, affected actions | Fail-closed blocked-action map | Unknown/unresolved conditions restrict only listed actions; this is not enforcement until every action adapter consumes the result |
| Hypothesis Competition | Hypotheses with support/refutation evidence IDs and discriminating tests | Per-hypothesis counts and unresolved/leading status | Counts evidence identifiers, not evidential quality, independence, likelihood, or causality |
| Forbidden-State Synthesizer | Initial state, finite transition adjacency, forbidden states, depth bound | Counterexample path or bounded no-counterexample result | No path is not a universal proof unless the model is complete and the search is exhaustive |
| Multi-History Reconciliation | Named histories, event IDs, content, explicit causal edges | Conflict, unobservable findings, shared events | Does not invent total order for concurrent events; does not infer wall-clock order |
| Proof-Preserving Refactoring | Old/new declared contracts and required property names | Preserved / regression / inconclusive | Declared observations are not semantic equivalence; production needs executable contract checks or formal refinement proof |
| Minimal Proof Surface | Required obligations and verified evidence-to-obligation coverage | Bounded minimum evidence subset | Exact set cover only over supplied eligible candidates; mandatory evidence is retained; complexity is exponential |
| Assurance Causality Map | Invariants, dependencies, evidence states | Per-invariant eligibility state | Informational map only; never grants authority or executes work |

## Shared state vocabulary
- `PROPOSED`: suggested, not tested.
- `INCOMPLETE`: required input/evidence/coverage missing.
- `UNRESOLVED`: competing explanations or uncertain evidence remain.
- `CONFLICTED`: incompatible observations or causal constraints were detected.
- `REJECTED`: an explicit required condition failed.
- `ELIGIBLE_FOR_NEXT_GATE`: supplied checks passed; this is not authorization.
- `VERIFIED`: reserved for a specific claim after reproducible verification evidence is attached. This reference slice and its architecture are not yet labeled VERIFIED.

## Core invariants
1. Missing evidence never implies absence.
2. A leading hypothesis is not a proven hypothesis.
3. A bounded search that finds no counterexample is not a universal proof.
4. Capability expansion during refactoring is a regression unless separately authorized.
5. Unknown, stale, or contradictory evidence must not silently become a positive assurance state.
6. No function in this module invokes external tools, grants authority, changes canonical state, or deploys code.
7. A digest binds supplied bytes; it does not prove their truth, origin, freshness, or independence.

## State transitions
```text
PROPOSED
  -> ANALYZED
  -> {ELIGIBLE_FOR_NEXT_GATE | INCOMPLETE | UNRESOLVED | CONFLICTED | REJECTED}
ELIGIBLE_FOR_NEXT_GATE
  -> AUTHORIZATION_PENDING
  -> AUTHORIZED_BY_EXTERNAL_GATE
  -> EXECUTION_RECEIPT_REQUIRED
  -> VERIFIED_ONLY_AFTER_EVIDENCE_REVIEW
```

The reference implementation stops at analysis. The latter transitions are architectural states only and must be implemented by separate enforcement components.

## Rust-facing interface proposal

The Rust interface is a contract proposal, not compiled Rust in this change:

```rust
pub enum AssuranceStatus {
    EligibleForNextGate,
    Incomplete,
    Unresolved,
    Conflicted,
    Rejected,
}

pub struct EvidenceRef {
    pub id: String,
    pub digest: String,
    pub source_id: String,
    pub verified: bool,
    pub freshness_policy: String,
}

pub struct ProofObligation {
    pub id: String,
    pub invariant_id: String,
    pub required: bool,
    pub evidence_refs: Vec<String>,
}

pub struct AssuranceDecision {
    pub status: AssuranceStatus,
    pub unresolved_obligations: Vec<String>,
    pub counterexample_paths: Vec<Vec<String>>,
    pub input_digest: String,
    pub decision_digest: String,
    pub authority_granted: bool, // must remain false in analysis-only engine
}
```

Rust implementation requirements: typed IDs; validated digest encoding; bounded search parameters; deterministic serialization/versioning; no implicit authority; explicit model-completeness declaration; testable overflow/size limits; serde schema compatibility tests; and property/fuzz tests.

## Adversarial acceptance matrix

- Duplicate event or hypothesis IDs cannot inflate evidence coverage.
- A shared clock, signing key, model, provider, or root certificate appears as a concentration candidate when declared as a common dependency.
- An unknown critical dependency produces an action restriction.
- A forbidden state reachable exactly at the depth bound is found; states beyond the bound remain unproven.
- Same event ID with incompatible payloads yields CONFLICTED.
- Causal cycles yield CONFLICTED; missing causal endpoints yield an unobservable finding.
- New capabilities in a refactor are reported as a contract regression.
- Missing required properties yield INCONCLUSIVE, not success.
- Unverified evidence is excluded from the minimal surface.
- Mandatory proof obligations cannot be removed by optimization.
- Too many candidates produce INCOMPLETE rather than unbounded exponential work.
- Assurance mapping never returns authority granted or execution performed.

## Research grounding
Fault-tree analysis and failure-mode analysis are established ways to trace hazards to shared causes; formal methods can produce counterexamples for bounded models, but the strength of the conclusion depends on model completeness and the proof assumptions. See NIST's formal-methods and assurance resources:
- https://csrc.nist.gov/Projects/automated-combinatorial-testing-for-software/autonomous-systems-assurance/formal-methods
- https://www.govinfo.gov/content/pkg/GOVPUB-C13-80299f9a3796882d21b5f7f636beafe7/pdf/GOVPUB-C13-80299f9a3796882d21b5f7f636beafe7.pdf

## Next steps
1. Run the GitHub Actions suite and fix any failures.
2. Add schema files and a versioned JSON interchange contract.
3. Integrate the uncertainty restrictions with actual VX adapter enforcement.
4. Add external signed/witnessed checkpoints and evidence independence metadata.
5. Implement and compile the Rust interface only after the Python contract is stable.
6. Add model-checking/formal refinement for selected high-risk invariants.
