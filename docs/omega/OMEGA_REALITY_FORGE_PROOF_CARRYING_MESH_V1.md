# Ω Reality Forge — Proof-Carrying Agent Mesh v1

Status: **PROPOSAL / executable prototype; not production-verified**  
Authority: derived capability under VAIXLNS. Canonical files are read-only.

## The invention

Reality Forge is an evidence-gated coordination kernel, not a chat dashboard. Each proposed task carries:
- a declared owner agent and dependency graph;
- required evidence kinds;
- hash-checked evidence payloads;
- a deterministic admission state;
- an append-only hash-linked decision receipt;
- an explicit human-approval boundary.

The distinguishing mechanism is **proof-carrying scheduling**: dependencies are not released because an agent says “done.” They become reviewable only when required evidence is present and its bytes match the supplied digest. Missing or tampered evidence fails closed. A reviewable task is still not VERIFIED and never authorizes execution.

## Prototype contract

Input plan schema: `vaixl.omega.reality-forge.plan.v1`  
Input evidence: `{"evidence":{"TASK-ID":{"artifacts":[{"kind":"test-log","payload":"...","sha256":"...","state":"TESTED"}]}}}`  
Output receipt schema: `vaixl.omega.reality-forge.receipt.v1`

States:
- `PENDING_VERIFICATION`: evidence missing or invalid.
- `BLOCKED_DEPENDENCY`: one or more dependencies have not reached review.
- `READY_FOR_REVIEW`: required evidence hashes match; a human still must review.
- receipt status remains `PENDING_HUMAN_REVIEW`.

## Run locally

```bash
python -m unittest tests.test_omega_reality_forge -v
python scripts/omega_reality_forge.py --plan plan.json --evidence evidence.json --output build/reality-forge/receipt.json
```

## Security boundary and non-claims

This version does not execute agent commands, connect to model providers, authenticate evidence signers, verify the truth of test claims, or prove a real repository restore. Hashes establish byte integrity only. Production use requires signed attestations, trusted identities, policy evaluation, sandbox isolation, replay tests, key management, threat modeling, and integration tests. No external agent may mutate `project.genome` or `Ω.000` through this prototype.

## Acceptance gates

1. Unit tests for missing, tampered, dependency-blocked, and deterministic inputs.
2. CI execution on the proposed branch.
3. Security review of parser, evidence trust model, event-chain replay, and dependency cycles.
4. Explicit human approval before any runtime, publication, or canonical-index mutation.
5. Update Ω.000 only after the implementation is reviewed and the relevant tests/evidence exist; this PR intentionally does not edit canonical records.
