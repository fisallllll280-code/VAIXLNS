# VAIXLNS Ω-CAP — Financial Intelligence Engine v1

**State:** SPECIFIED / initial implementation proposed  
**Execution mode:** Research and paper-trading only  
**Canonical authority:** `project.genome` and `Ω.000` remain unchanged  
**Risk notice:** This software is not investment advice, does not promise returns, and must not place real orders.

## Purpose

Ω-CAP provides a repository-owned foundation for source-traceable market research, portfolio exposure checks, scenario evaluation, and deterministic paper-trade records. It is not a broker, custodian, exchange, or financial adviser.

## Architecture

1. **Data boundary:** Market observations must carry a source, observation time, retrieval time, currency, and validation state. Missing or stale data must not silently become a zero.
2. **Research:** Strategies produce hypotheses and explicit assumptions. Historical results are not treated as guarantees.
3. **Risk gate:** Validate weights, concentration limits, available-cash constraints, and configured risk budgets before a paper order is accepted.
4. **Simulation:** Include transaction costs and slippage assumptions; keep in-sample and out-of-sample results distinct. Avoid look-ahead and survivorship bias.
5. **Evidence ledger:** Record the input snapshot identifier, strategy version, configuration hash, decision, and reason.
6. **Approval boundary:** Live execution is out of scope. No broker credentials, exchange keys, withdrawals, or real-order adapters are included in v1.

## Lifecycle

`PROPOSED → SPECIFIED → IMPLEMENTED → TESTED → VERIFIED`

A code commit alone does not imply `VERIFIED`. Verification requires repeatable tests, known test inputs, recorded outputs, and review of relevant failure modes. Financial performance cannot be inferred from unit tests.

## Minimum acceptance criteria

- Reject non-finite, negative, or malformed monetary values.
- Reject portfolio weights outside the configured policy.
- Reject paper orders when the configured cash/risk budget is exceeded.
- Produce deterministic decisions for identical inputs and configuration.
- Preserve a reason for each accepted or rejected decision.
- Test missing data, stale data, invalid values, concentration breaches, and cost assumptions.
- No external financial action occurs from this package.

## Future work (not implemented by this specification)

- Provider-specific market-data adapters with documented licensing and freshness semantics.
- Point-in-time datasets and reproducible backtest manifests.
- Portfolio-level risk models validated against reference implementations.
- User-approved integrations with appropriately authorized financial institutions, only after legal, security, and independent review.

## Repository integrity

This change is additive. It must not modify `project.genome`, `registry/omega/omega-000-master-index.json`, or existing canonical artifacts without explicit approval.
