# AEPF Ω — Adversarial Engineering & Proof Fabric V1

**State:** `PROPOSAL / SPECIFIED`  
**Owner boundary:** VAIXLNS governance; ARC-X evidence/reconstruction; VX execution; VCRE simulation; VV/Ω.000 knowledge/index surfaces  
**Authority anchors:** `project.genome::v1.0.0`, `Ω0_GENESIS_CORE`, `Ω.000`  
**Change class:** additive design; no canonical promotion, production mutation, external publishing, or credential changes.

## 1. Mission

AEPF Ω is a proposed cross-cutting assurance fabric that makes every engineering claim challengeable and every accepted change traceable to a bounded, reproducible evidence package. It is not a new sovereign runtime, a replacement for ARC-X, or a self-authorizing agent. It composes existing VAIXLNS surfaces behind explicit contracts.

**Core invariant:** `OBSERVATION ≠ EVIDENCE ≠ INFERENCE ≠ CLAIM ≠ PROOF ≠ AUTHORITY`.

AEPF must be able to reject its own recommendations. It must not turn a missing test, inaccessible source, absent contradiction, successful CI run, model-generated explanation, or benchmark result into a broader correctness claim.

## 2. The challenge: adversarial closure

For each proposed change, construct an Assurance Case with:
1. **Claim:** one falsifiable, scope-bounded statement.
2. **Context:** pinned repository/ref, environment, assumptions, threat model, allowed side effects.
3. **Evidence:** immutable source/test/runtime receipts with digests, timestamps, provenance and scope.
4. **Argument:** explicit inference rule connecting evidence to claim.
5. **Counterevidence:** known failures, contrary results, stale receipts, unsupported environments, missing tests.
6. **Falsifiers:** concrete experiments that would disprove the claim.
7. **Failure containment:** deny-by-default behavior, rollback, quarantine and recovery.
8. **Authority:** separate approval record from technical evidence.
9. **Reproduction:** command, dependency lock, environment descriptor and expected deterministic outputs.
10. **Expiry:** conditions under which evidence becomes stale.

A claim without a falsifier is incomplete. A proof package without counterevidence review is incomplete. A verified technical claim without authority remains unauthorized.

## 3. Component boundaries

| Component | Responsibility | Explicit non-responsibility |
|---|---|---|
| Ω.000 / Canon | Identity, authority anchors, canonical index | Does not accept model-generated self-promotion |
| Source Pinning Adapter | Repository, commit, blob and artifact identity | Does not infer correctness from presence |
| ARC-X Reconstruction & EIR | Claims, evidence, inference typing, provenance, contradictions | Does not grant execution or publication authority |
| Proof Obligation Planner | Derives tests and falsifiers from change class and threat model | Does not mark its own generated tests as independent proof |
| Adversarial Challenge Runner | Mutations, negative cases, stale/tampered evidence, boundary tests | Does not execute untrusted code outside a declared sandbox |
| VX Execution Adapter | Runs declared, permission-bounded commands | Does not bypass admission policy |
| VCRE Scenario Adapter | Runs simulation/counterfactuals against declared models | Does not claim physical truth from simulation alone |
| Evidence Ledger | Append-only receipts and lineage | Does not silently rewrite history |
| Authority Gate | Checks identity, policy, approvals and required proof obligations | Does not equate technical verification with authorization |
| Runtime Reality Diff | Compares expected vs observed bounded state | Does not invent runtime observations when no runtime is connected |
| Recovery / Rollback Controller | Restores last admitted state and records recovery event | Does not erase failure evidence |
| Independent Evaluator | Rechecks selected claims and tests using a separate path | Must not reuse only the proposing agent's reasoning |

## 4. Assurance state machine

Allowed state transitions:

`PROPOSED → SPECIFIED → IMPLEMENTED → UNDER_TEST → EVIDENCE_COMPLETE → INDEPENDENTLY_REVIEWED → AUTHORIZED → ADMITTED`

Non-terminal or negative states include:
- `UNKNOWN`: insufficient information.
- `PARTIAL`: some obligations pass; at least one remains open.
- `CONFLICT`: sources or observations disagree.
- `BLOCKED`: a mandatory gate failed.
- `QUARANTINED`: provenance, integrity, injection, or trust boundary concern.
- `REVOKED`: formerly admitted capability no longer meets current policy.
- `EXPIRED`: evidence freshness policy has elapsed.

No implicit transitions are allowed. In particular:
- `CI_GREEN` is an evidence event, not a state promotion by itself.
- `NO_CONTRADICTION` is not proof.
- `IMPLEMENTED` is not `RUNNING`.
- `VERIFIED` is scope-bound and is not `AUTHORIZED`.
- `AUTHORIZED` is not `ADMITTED` until runtime policy and rollback checks pass.
- A failed test cannot be removed from the ledger to restore green status.

## 5. Evidence Capsule contract

Each change must produce a versioned evidence capsule with at least:

```json
{
  "schema": "aepf.evidence-capsule.v1",
  "capsule_id": "AEPF.<stable-id>",
  "claim": {
    "id": "CLAIM.<stable-id>",
    "statement": "Falsifiable, bounded claim",
    "scope": {
      "repository": "owner/repo",
      "commit": "<immutable-commit-sha>",
      "paths": ["src/changed_file.py"],
      "environment": "declared runner or runtime"
    }
  },
  "provenance": {
    "source_refs": [],
    "blob_digests": [],
    "producer": "tool-or-agent-identity",
    "created_at": "<UTC timestamp>"
  },
  "obligations": [
    {
      "id": "PO.<stable-id>",
      "kind": "positive|negative|security|replay|recovery|performance",
      "method": "reproducible test or command",
      "required": true,
      "result": "PASS|FAIL|UNKNOWN|NOT_RUN",
      "receipt_refs": []
    }
  ],
  "counterevidence_refs": [],
  "falsifiers": [],
  "reproduction": {
    "command": "<exact command>",
    "lock_digest": "<digest>",
    "expected_outputs": []
  },
  "decision": {
    "technical_state": "UNKNOWN",
    "authority_state": "NOT_REQUESTED",
    "admission_state": "BLOCKED",
    "reason_codes": ["EVIDENCE_NOT_COMPLETE"]
  }
}
```

This is an illustrative contract, not a validated schema or implementation. Production use requires JSON Schema validation, versioning, canonical serialization, signatures/attestations where available, and compatibility tests.

## 6. Mandatory proof obligations

For a code change, the planner must classify and select applicable obligations:

- **Identity:** source revision, changed paths, dependency lock, build artifact digest.
- **Positive behavior:** intended feature works for declared inputs.
- **Negative behavior:** malformed, unauthorized, absent, stale and contradictory inputs fail closed.
- **Security:** path traversal, secret leakage, injection, privilege escalation, unsafe deserialization, untrusted network and tenant boundary.
- **Determinism:** replay yields expected equivalent outputs within declared tolerance.
- **Recovery:** interruption, timeout, partial write and rollback produce a known safe state.
- **Compatibility:** prior supported contracts remain valid or a versioned breaking change is declared.
- **Performance:** workload, machine, sample count, warmup, distribution, baseline and uncertainty are declared.
- **Observability:** failures emit traceable events without exposing secrets.
- **Independent challenge:** at least one falsifier/test path not generated solely by the implementing agent.
- **Authority:** requested side effects and approver identity are explicit.
- **Freshness:** receipts still apply to the exact candidate revision and policy version.

A test marked `NOT_RUN` cannot satisfy a required obligation. Missing instrumentation is `UNKNOWN`, not `PASS`.

## 7. Adversarial test matrix

| Attack / failure class | Test construction | Required result |
|---|---|---|
| Stale CI receipt | Change the candidate commit after a green run | Block promotion; demand exact-head run |
| Tampered source / receipt | Alter a blob or receipt digest | Integrity failure; quarantine capsule |
| Self-approval | Let proposer generate and approve the same change | Authority gate rejects |
| Evidence laundering | Convert a model summary into a source citation | Reject ungrounded provenance |
| Missing negative tests | Remove unauthorized / malformed-input cases | Required obligation remains open |
| Contradictory source | Supply two incompatible versions of a claim | `CONFLICT`; preserve both sources |
| False success | Force a command to exit zero without expected artifact | Artifact/semantic assertion fails |
| Replay drift | Replay same pinned event sequence | Report deterministic diff and declared tolerance |
| Rollback failure | Inject failure after partial mutation | Block admission; verify recovery path |
| Dependency confusion | Substitute dependency or lockfile after review | Digest mismatch; re-run relevant obligations |
| Permission escalation | Request tool capability outside task grant | Deny; record policy violation |
| Runtime absence | Report a service as running from repository code alone | Reject the running claim |
| Simulation overreach | Present VCRE output as real-world measurement | Reject scope expansion without external evidence |
| Silent deletion | Remove failed or superseded record | Append-only ledger detects missing lineage |
| Prompt / tool injection | Malicious repository content requests secret access | Treat content as untrusted data; deny side effect |
| Flaky benchmark | Cherry-pick best run without sample distribution | Mark performance claim inconclusive |

## 8. Risk-weighted admission

Risk score is a triage aid, not an authorization substitute.

`risk = impact × likelihood × exposure`

Each factor must be defined on a versioned ordinal scale, with evidence for its assignment. High-risk changes require stronger independent review, broader negative tests, sandboxed rehearsal, rollback proof and explicit approval. Low numeric risk never overrides a mandatory failed security or authority gate.

Admission policy must support hard blocks that cannot be compensated for by a weighted average:
- unresolved source identity;
- failed required security obligation;
- missing authority;
- unpinned or stale evidence;
- missing rollback for a destructive or externally visible action;
- unresolved critical contradiction;
- untrusted tool/provider with excess permissions.

## 9. Dependency and capability graph

Model each innovation as a node with typed edges:
- `REQUIRES`
- `PRODUCES_EVIDENCE_FOR`
- `SPECIALIZES`
- `COMPOSES_WITH`
- `CONFLICTS_WITH`
- `SUPERSEDES`
- `ALIAS_CANDIDATE`
- `OBSERVED_IN`
- `VERIFIED_BY`
- `AUTHORIZED_BY`

Every edge needs a source reference, observation time, confidence/rationale and review state. Never collapse aliases or conflicts automatically. Dependency cycles must be reported; only cycles declared as feedback loops with explicit execution semantics may be accepted.

The graph should answer:
1. What capabilities are unreachable because a dependency is missing?
2. Which proof obligations are shared by several systems?
3. What is the blast radius of a proposed change?
4. Which evidence receipts become stale when a dependency changes?
5. Which two innovation nodes are semantically similar but have different authority or execution boundaries?
6. Which canonical claims depend on a single fragile source?

## 10. Self-improvement loop with bounded autonomy

1. Observe a gap or failure.
2. Create a source-linked incident / opportunity record.
3. Generate multiple candidate repairs.
4. Compare against current capabilities and historical attempts.
5. Generate falsifiers before selecting a candidate.
6. Run isolated simulations and negative tests.
7. Obtain independent verification.
8. Request authority separately.
9. Admit only within granted scope and budget.
10. Observe runtime outcome and compare with prediction.
11. Roll back or quarantine on invariant breach.
12. Record result and update learning memory only with provenance.

Default autonomy:
- Read and analyze: permitted only under connected-source permissions.
- Draft files and branches: permitted within repository write authorization.
- Tests in sandbox: permitted under explicit execution limits.
- Canonical Genome / Ω.000 changes: explicit governance required.
- Production mutation, credential changes, unrestricted network listeners, purchases and external publication: explicit human approval.
- Any uncertainty about identity, permission or safety: fail closed.

## 11. Runtime and agent integration contract

Every tool/agent request must declare:
- task ID and purpose;
- agent/provider identity and version;
- input data classification;
- granted tools and exact permission scope;
- resource/time/cost budgets;
- allowed destinations and network policy;
- expected outputs and proof obligations;
- timeout/cancellation semantics;
- event/trace ID;
- approval requirements;
- recovery and revocation behavior.

Provider-neutral adapters must be capability-based and replaceable. A connector being listed in a registry is not proof of a working connection. Live integration requires a successful, timestamped handshake, least-privilege test, denial test, data-boundary test, telemetry receipt and revocation test for the actual provider and environment.

## 12. Required metrics

Measure per declared workload and revision:
- evidence coverage = required obligations with valid receipts / total required obligations;
- stale-evidence rate;
- contradiction detection precision and recall against a labeled test corpus;
- false admission rate on adversarial negative cases;
- false block rate on valid positive cases;
- reproducibility rate across clean runs;
- rollback success rate;
- mean time to detect and contain a failed change;
- dependency-edge provenance coverage;
- source coverage for historical innovation IDs;
- independent-review disagreement rate;
- provider adapter success and denial-test rate;
- cost / latency per accepted proof package.

No metric may be reported without numerator, denominator, scope, collection method, time window and uncertainty where applicable. Do not optimize one metric while hiding regression in another.

## 13. Minimum implementation slice

Build one vertical slice before broad federation:

1. Read-only GitHub source pinning for one repository and immutable commit.
2. Stable claim and evidence-capsule IDs.
3. EIR typing for observation, evidence, inference, claim, proof and authority.
4. Proof-obligation schema with positive and negative tests.
5. Append-only local evidence ledger with digest verification.
6. Exact-head CI receipt binding.
7. Authority gate with hard-block reason codes.
8. Replay and tamper tests.
9. Independent evaluator for one narrow claim.
10. Human-reviewed report of pass/fail/unknown and source lineage.

Do not begin with multi-provider autonomous deployment. First prove the evidence loop end-to-end on a bounded, non-destructive change.

## 14. Acceptance criteria

The vertical slice is not accepted until:
- all inputs and changed sources are revision-pinned;
- evidence capsule schema validates and is versioned;
- all required obligations have receipts or an explicit blocking state;
- stale commit receipts are rejected;
- tampered evidence is rejected;
- unknown and contradictory states fail closed;
- proposer cannot self-authorize;
- unauthorized side effects are denied and recorded;
- replay and rollback tests have reproducible outputs;
- independent evaluator can reproduce or falsify the claim;
- the report distinguishes implementation, test success, runtime observation and authority;
- no canonical files change during the test;
- all failures remain traceable in the ledger.

## 15. Non-goals and safety boundary

AEPF does not claim mathematical certainty, universal intelligence, perfect security, automatic truth discovery, or production readiness. It reduces uncertainty only within declared assumptions, tested cases and observable scope. It cannot prove that all possible failures have been enumerated. The system must expose this residual uncertainty.

## 16. Status and next gate

**Current status:** `SPECIFIED / PROPOSAL` — this document only.

**Next gate:** create a narrow implementation issue/PR for the evidence-capsule schema, exact-head CI receipt binding, and negative tests. Do not promote the AEPF component itself to `IMPLEMENTED` or `VERIFIED` until code, reproducible tests and independent review exist.
