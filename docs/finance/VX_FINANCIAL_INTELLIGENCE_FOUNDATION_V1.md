# VX Financial Intelligence — Foundation v1

Status: PROPOSAL / SPECIFICATION. No live market data feed, broker, exchange, or trading account is connected by this document.

## Mission

Create a separate, governed financial research and risk system inside the VAIXLNS/VX ecosystem. It covers equities and ETFs, crypto assets, FX, commodities, and—only where permissions and market data support it—derivatives. The first release is research-only and paper-trading only.

The objective is not to promise returns. It is to discover market information, test falsifiable hypotheses, estimate uncertainty and risk, and produce auditable research outputs.

## System boundary

- VAIXLNS / Ω remains the authority and evidence admission layer.
- VX is the orchestrator and runtime.
- Financial Intelligence is a bounded domain subsystem, not a replacement for VX or the canonical project genome.
- Keep this subsystem in a separate directory/package and use explicit contracts to integrate it.
- Do not modify project.genome, Ω.000, or the Omega master index in this initial slice.

## Modules

1. **Market Data Gateway** — provider adapters, timestamp and timezone normalization, corporate actions, symbol mapping, exchange calendars, data freshness, licensing, and missing-data flags.
2. **Asset and Venue Registry** — canonical asset IDs, symbols, venue, currency, instrument type, contract specifications, trading hours, and delisting status.
3. **Research Index** — price/volume data, fundamentals, filings, macro releases, on-chain metrics, funding/open interest where licensed, and source provenance.
4. **Feature Pipeline** — point-in-time feature generation; all transformations fit only on training data; versioned schemas and reproducible data snapshots.
5. **Hypothesis Lab** — strategies expressed as testable hypotheses with explicit rationale, assumptions, holding horizon, eligible universe, and invalidation criteria.
6. **Backtest Engine** — chronological splits, walk-forward evaluation, transaction costs, spread, slippage, latency assumptions, corporate actions, survivorship-bias checks, and prevention of look-ahead leakage.
7. **Model Evaluation** — baselines, out-of-sample metrics, calibration, stability across regimes, ablation tests, multiple-testing correction, and independent reproduction.
8. **Portfolio and Risk Engine** — exposure limits, concentration, volatility, drawdown, liquidity, leverage, gap risk, correlated positions, and stress scenarios.
9. **Paper Execution** — simulated orders, fills, fees, partial fills, rejected orders, positions, cash, reconciliation, and immutable event records. No real orders in v1.
10. **Monitoring and Alerts** — stale data, provider outages, drift, model degradation, risk threshold breaches, and unexplained P&L changes.
11. **Evidence Ledger** — dataset snapshot/hash, source, timestamp, code revision, configuration, random seed where relevant, experiment results, risk checks, and admission status.
12. **Human Review Gate** — review and explicit approval before any real-money integration, external publication, or change to risk limits.

## Initial asset coverage

- Equities and ETFs: exchange-listed instruments with licensed historical and point-in-time data.
- Crypto: spot first; derivatives only after venue-specific rules, funding, liquidation, and API risks are modelled.
- FX: spot/reference data first; broker-specific execution semantics are out of scope until reviewed.
- Commodities and futures: only after contract rolls, expiry, margin, settlement, and market calendars are modelled.
- Options and other derivatives: later phase; requires Greeks, exercise/assignment, volatility surfaces, and instrument-specific risk tests.

## Research contract

Every experiment must declare:
- experiment ID and hypothesis
- universe and point-in-time eligibility rules
- data source, coverage interval, timezone, adjustment policy, freshness, and license
- feature definitions and code/config revision
- training, validation, and untouched test periods
- baseline strategy and benchmark
- transaction cost, spread, slippage, financing, borrow/funding, and fill assumptions
- metrics: net returns, volatility, Sharpe/Sortino with caveats, max drawdown, turnover, exposure, tail loss, hit rate, capacity/liquidity limits, and uncertainty intervals
- sensitivity, regime, ablation, and stress results
- failure cases, limitations, and independent verification result

No experiment may be promoted based only on in-sample return, a single metric, or a cherry-picked time period.

## Mandatory safety and validity gates

1. Point-in-time data only for features and decisions; block look-ahead leakage.
2. Include delisted assets and corporate actions where relevant; explicitly measure survivorship bias.
3. Chronological train/validation/test separation; no random shuffling for time-series evaluation unless the method justifies it.
4. Include fees, spread, slippage, funding/borrow, market impact assumptions, and realistic order constraints.
5. Paper-trade before any real execution; compare simulated fills to observed market conditions.
6. Default to no leverage, no derivatives, no real orders, and no custody of funds in v1.
7. Secrets remain in a secret manager/environment and never enter prompts, logs, notebooks, or source control.
8. Market data and news are untrusted inputs; defend against prompt injection and poisoned data.
9. Use least privilege and read-only data credentials in research workers.
10. Any later live execution requires legal/compliance review for the target jurisdictions and venues, explicit user approval, independent risk sign-off, kill switch, exposure caps, reconciliation, and tested recovery.
11. Do not promise profit, guaranteed returns, or a win rate unsupported by an audited test.
12. Clearly label backtest, paper, and live results as different evidence classes.

## Lifecycle and evidence labels

- DISCOVERED: source or instrument identified.
- DATA_VALIDATED: schema, timestamps, gaps, provenance, and license reviewed.
- RESEARCHED: experiment completed with reproducible configuration.
- BACKTEST_PASSED: predeclared acceptance checks passed out of sample.
- PAPER_VALIDATED: paper trading reconciled over a declared observation period.
- LIVE_ELIGIBLE: review package exists; this is not permission to place orders.
- LIVE_AUTHORIZED: explicit approvals, legal review, secrets, kill switch, and execution controls verified.
- DEGRADED / BLOCKED: stale, invalid, unsafe, unlicensed, or failed checks.

Promotion must be evidence-backed. A simulated trade is not a real fill; a backtest is not a forecast; a profitable period is not proof of durable edge.

## v1 acceptance criteria

- Purely local/offline unit tests for instrument normalization, timestamps, missing data, return calculations, fees, position accounting, drawdown, and risk limits.
- Tests that deliberately introduce future-data leakage, survivorship bias, stale prices, duplicate bars, timezone errors, and missing corporate actions; the pipeline must detect or reject these cases.
- Deterministic experiment replay from a fixed dataset snapshot and config.
- Baseline comparison and out-of-sample report with costs included.
- Paper-order lifecycle tests: submit, partial fill, rejection, cancel, fees, reconciliation, and kill switch.
- No exchange/broker order endpoint in v1; tests must prove live execution is disabled by default.
- Evidence artifact linking dataset, code revision, config, results, and verifier.
- Do not mark the system verified until tests actually run in CI and outputs are inspected.

## Implementation sequence

Phase 0 — inventory current code and preserve canonical sources.
Phase 1 — add domain package, typed data contracts, synthetic fixtures, and offline tests.
Phase 2 — add one licensed/read-only market-data adapter and data-quality checks.
Phase 3 — implement reproducible backtest with realistic costs and leakage tests.
Phase 4 — add portfolio/risk engine and stress tests.
Phase 5 — add paper execution and monitoring.
Phase 6 — benchmark hypotheses on walk-forward/out-of-sample windows; independently reproduce results.
Phase 7 — review compliance, security, venue-specific execution, and operational controls before even considering live trading.

## Explicit non-goals for v1

- No automatic real-money trading.
- No API keys or exchange credentials committed to the repository.
- No leverage, guaranteed-profit claims, or uncontrolled agent autonomy.
- No broad refactor or deletion of existing project files.
- No modification of project.genome or Ω.000.
