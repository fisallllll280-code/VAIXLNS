# ARC-X Bounded Adaptive Evolution Planner v1

**Status:** SPECIFIED + reference implementation on a feature branch; not an autonomous production updater.

## Purpose

Evaluate whether a proposed change is worth considering for one system while preserving that system's identity, boundary digest, allowed capability set, and independent evidence requirements. The planner adds a controlled evolution stage to ARC-X's reconstruction and federation-link planning.

## Input contract

A system declaration supplies:
- stable `system_id`;
- a SHA-256 digest for the current boundary contract;
- an explicit list of allowed local capability identifiers.

Each proposal supplies:
- proposal/system/capability identities;
- the exact boundary digest it was evaluated against;
- a bounded local change class;
- finite benefit and risk scores in [0, 1];
- evidence records with a 40-character source revision, SHA-256 evidence digest, and independent-validation flag.

Scores are comparative screening signals, not scientific truth or proof. They must be calibrated by a domain-specific measurement contract before operational use.

## Decision states

- `BLOCKED`: invalid identity, boundary mismatch, capability escape, forbidden change class, invalid scores, or malformed evidence.
- `PENDING_EVIDENCE`: evidence is absent or lacks independent validation.
- `REJECTED_LOW_NET_VALUE`: evidence is structurally sufficient, but benefit minus risk is not positive.
- `PENDING_HUMAN_REVIEW`: local and in-boundary candidate with positive net score and independent evidence.
- Plan-level `READY_FOR_REVIEW` means only that at least one candidate can be reviewed; it does not authorize execution.

## Non-negotiable boundaries

This planner is pure local analysis. It does not execute proposals, modify a system, call networks, alter canonical registries, change authority, or approve cross-system writes. Cross-system changes, production mutation, canonical changes, and authority changes must use their separate governed workflows. No proposal is applied automatically.

## Intended loop

`OBSERVE → RECONSTRUCT → PROPOSE → SCORE → VERIFY INDEPENDENTLY → HUMAN/GOVERNED REVIEW → APPLY VIA AUTHORIZED RUNTIME → MEASURE OUTCOME`

The last two stages are outside this planner and require their own authorization and execution evidence. Failed or regressed proposals should be retained as lineage and never silently erased.

## Verification

Unit tests cover boundary escape, evidence integrity, independent validation, net-value screening, deterministic output, and the non-execution guarantee. The feature is not considered integrated until CI is observed for the exact commit and the PR is reviewed.
