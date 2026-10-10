# Ω Economic Kernel v1 — Evidence-Bound Economics

Status: IMPLEMENTED_REFERENCE_SLICE; CI_PENDING; NOT_VERIFIED.

## Purpose

Provide a deterministic, reviewable reference model for recording task-level revenue and cost, separating realized from simulated results, checking budget arithmetic, and proposing bounded reinvestment from a realized net basis.

## Components

- `build_ledger(entries)`: validates entries, rejects duplicate IDs, sorts valid entries deterministically, and emits a SHA-256 digest for the snapshot.
- `summarize_economics(entries)`: separates REALIZED and SIMULATED totals and keeps currencies independent. Amounts are integer minor units.
- `evaluate_budget(...)`: determines whether a proposed cost fits a declared budget. Its result is not execution authority.
- `propose_reinvestment(...)`: calculates a percentage proposal from a nonnegative realized net basis and evidence references. It never transfers money.

## Entry contract

Each entry includes `entry_id`, `task_id`, `agent_id`, `kind`, `amount_minor`, `mode`, `currency`, and `occurred_at`.

- `kind`: REVENUE or COST.
- `mode`: REALIZED or SIMULATED.
- A REALIZED entry requires `evidence_ref` and `evidence_status=VERIFIED`.
- SIMULATED entries cannot claim `evidence_status=VERIFIED`.
- Supported currencies in this reference slice: SAR, USD, EUR, GBP. No currency conversion is performed.
- Amounts must be positive integer minor units; costs are positive entries subtracted from revenue in summaries.

## Invariants

1. SIMULATED and REALIZED results never aggregate into one total.
2. Currencies never aggregate without explicit FX conversion (not implemented here).
3. A realized entry without an evidence reference is INCOMPLETE.
4. Duplicate ledger IDs are rejected.
5. Budget admission never grants execution authority.
6. Reinvestment is proposal-only; transfer execution is always false.
7. Digests provide content integrity references, not source authenticity, signatures, append-only storage, or proof that a receipt represents settled funds.
8. The supplied evidence status is an assertion. A production design must independently verify source receipts, settlement status, reversals/refunds, taxes, chargebacks, accounting period, and currency precision.
9. This reference model does not connect to payment processors, banks, exchanges, wallets, procurement, live agents, or deployment systems.

## Tests and acceptance criteria

The dedicated suite covers realized/simulated separation, evidence requirements, duplicate IDs, integer amounts, currency separation, deterministic snapshot digest, budget bounds, no implicit execution authority, and reinvestment proposal limits.

## Not yet implemented

- Persistent append-only ledger or signed/Merkle checkpoints.
- Independent evidence verification and provider connectors.
- Idempotent ingestion across retries and external settlement reconciliation.
- Policy-enforced per-agent budgets, reservations, spend caps, and kill switches.
- Agent Foundry, commercial opportunity discovery, and live market connectivity.
- Tax/accounting treatment, refunds, chargebacks, FX conversion, and financial compliance.
- Real money movement or autonomous trading.

The next safe integration is read-only measurement of completed VX task receipts and metered provider usage. Do not wire this reference model directly to money-moving APIs.
