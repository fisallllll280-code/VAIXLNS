# VX Financial Intelligence Mesh — One Agent per Tool v1

**Status:** PROPOSED / BRANCH ONLY. This contract does not claim any provider is connected, any model request has succeeded, or any financial outcome has been achieved.
**Canonical owner:** VAIXLNS
**Coordinator and execution gate:** VX
**Research and discovery:** NEXENT / approved research connectors
**Protected sources:** `project.genome` and `Ω.000` are out of scope and must remain unchanged.

## 1. Objective

Build one durable, named financial agent for each distinct tool/provider connector. Every agent must have a direct user-facing interaction surface, a narrow job contract, explicit permissions, measurable service levels, and an evidence trail. Agents must not be duplicated merely to increase apparent headcount. One connector identity maps to one canonical agent identity; specialist skills are capabilities of that agent, not duplicate agents.

The objective is not to claim that this is the world's strongest financial agent. The objective is to establish a testable system that can outperform a single-model workflow on defined financial research, analysis, risk, and execution-readiness evaluations.

## 2. Agent topology

`User ↔ Financial Command Console ↔ VX Financial Director ↔ one agent per registered tool`

- **VX Financial Director**: accepts the user's goal, breaks it into a dependency-aware task graph, chooses eligible agents, reconciles disagreement, tracks cost/time budgets, and returns one report with source-linked evidence and unresolved risks.
- **Provider agents**: one each for OpenAI, Anthropic/Claude, Google/Gemini, xAI/Grok, and Mistral, but only after each provider adapter is configured and live-tested. A provider agent is not considered online because its name or API-key variable exists.
- **Tool agents**: one each for authorized market-data, web/research, spreadsheet/calculation, repository/CI, document, and portfolio-data connectors when such connectors are actually installed and approved. Each tool agent can only invoke its registered connector operations.
- **Independent challenge pass**: at least one different eligible agent or deterministic checker attempts to falsify material assumptions and calculations. The originating agent cannot certify its own high-impact conclusion.
- **User-facing surface**: each agent returns status, questions, and results through the same console/session contract, with an explicit agent identity. This does not imply every external provider can independently message the user outside its supported interface.

## 3. Canonical identity and no-duplication rule

Each agent record must include:

- `agent_id`, `connector_id`, provider/tool, owner, version, role, and declared capabilities;
- lifecycle state, endpoint class, auth mechanism, permitted data classes, allowed operations, and denial rules;
- budget limits (calls, wall time, tokens, and cost where measurable);
- input/output schema versions, timeout, retry policy, cancellation support, and idempotency behavior where applicable;
- evaluation profile, last successful live probe, expiry time, and evidence-receipt references.

Enforce a unique constraint on `connector_id` for the canonical active agent registry. Multiple skills may exist under an agent, but must not create duplicate canonical agents for the same connector. If a connector has materially separate security principals or environments, represent them as explicitly scoped connector instances, not hidden duplicates.

## 4. Financial capability contract

The mesh may support these capabilities when their data sources and implementations are verified:

1. Financial statement and filing extraction with source citations.
2. Market, macroeconomic, sector, and company research with timestamps and source quality.
3. Valuation and scenario analysis (DCF, comparables, sensitivity analysis) with visible assumptions.
4. Portfolio exposure, concentration, correlation, liquidity, drawdown, and stress analysis when holdings/data are provided lawfully.
5. Unit economics, pricing, cash-flow planning, revenue experiments, and cost optimization.
6. Risk and counterevidence review, including downside cases, uncertainty ranges, data freshness, and conflicts of interest.
7. Reproducible calculations, spreadsheet/model generation, and testable data transformations.
8. Decision briefs with alternatives, expected benefits, downside, confidence, evidence gaps, and a next verification step.

Every material numerical claim must expose its inputs, units, formula or method, as-of time, and source. Forecasts must be labeled as estimates, not facts. Provider consensus is not independent evidence when providers rely on the same source or prompt.

## 5. Authority boundaries

- Default permissions are read-only and proposal-only.
- Agents may research, calculate, simulate, compare, draft, and prepare an action plan within approved scopes.
- No agent may autonomously trade, transfer money, move assets, borrow, sign contracts, purchase subscriptions, change production credentials, or publish externally.
- Any financial transaction or other high-impact action requires a separate explicit authorization for the exact action, amount/scope, destination, expiry, and idempotency key, plus the applicable human confirmation.
- No agent can grant itself authority, edit its own active policy, bypass the VX gate, or certify its own result as verified.
- Secrets must be injected by an approved secret manager and must never appear in prompts, source files, evidence artifacts, or logs.
- If identity, source freshness, permission, calculation, or evidence is missing or conflicting, return `HOLD` or `QUARANTINE`; never silently fall back to an unverified provider.

## 6. Routing and execution protocol

For each user request:

1. Create a stable `task_id` and classify intent, financial impact, sensitivity, deadline, and allowed data.
2. Build a task DAG with explicit dependencies and acceptance tests.
3. Resolve only connectors in `ACTIVE` state with fresh evidence and sufficient scope.
4. Dispatch the minimum set of agents required; add an independent challenger for material decisions.
5. Normalize outputs without erasing provider-specific caveats or uncertainty.
6. Run deterministic calculation checks and evidence/provenance validation.
7. Resolve disagreements by checking source lineage and methods, not by majority vote.
8. Produce one user-facing result with recommendation options, assumptions, downside, confidence, citations, execution boundary, and unresolved questions.
9. Store a redacted, hash-linked receipt; do not store raw secrets or unrestricted personal data.
10. Measure the outcome and update evaluations only through a versioned, reviewable change.

Each call must have a request ID, connector/agent/version identity, timeout, bounded retries, cancellation outcome, policy decision, timestamps, redacted content hashes, and an explicit terminal status.

## 7. Connector lifecycle

`UNREGISTERED → DISCOVERED → CONTRACTED → CONFIGURED → CONTRACT_TESTED → POLICY_REVIEWED → LIVE_PROBED → ACTIVE`

Failure, expired evidence, credential rotation, provider/model revision, schema change, or policy change must move the connector to `DEGRADED`, `QUARANTINED`, or `NOT_CONFIGURED` until revalidated.

Registration or tool discovery proves only that a tool is listed. Unit tests prove only tested local behavior. A live provider request proves only that specific request succeeded. Neither alone proves financial correctness or production readiness.

## 8. Required evaluations

Before an agent can be marked `ACTIVE`, test at least:

- source attribution, date/as-of handling, and stale-data rejection;
- arithmetic, unit consistency, rounding, and reproducibility;
- missing data, contradictory sources, malformed output, and unsupported claims;
- prompt injection and untrusted external content;
- unauthorized tool call and scope escalation attempts;
- provider timeout, rate limit, authentication failure, cancellation, duplicate request, and retry safety;
- cost/time budget enforcement and safe degradation when a connector fails;
- independent challenge pass and conflict-of-interest disclosure;
- no transaction/purchase/publication without explicit approval;
- replay from a sanitized evidence receipt.

Record accuracy, citation validity, calculation correctness, calibration, coverage, latency, cost, abstention quality, and failure recovery. Do not collapse them into a single score without publishing the weighting.

## 9. Acceptance gates

The first vertical slice is accepted only when all of the following are evidenced:

- [ ] The canonical registry contains exactly one agent identity per configured connector.
- [ ] Every registered agent has a user-visible identity and structured status/result contract.
- [ ] Unconfigured providers are shown as `NOT_CONFIGURED`, not simulated as connected.
- [ ] At least one real, low-risk request is successfully tested for each connector claimed as live.
- [ ] Deterministic finance calculations have unit and regression tests.
- [ ] A second agent or deterministic checker can challenge and reject a deliberately flawed result.
- [ ] Unauthorized financial action is denied and audited.
- [ ] Receipts can be replayed or independently inspected without exposing secrets.
- [ ] CI results, commit SHA, timestamps, and test artifacts are linked to the pull request.
- [ ] `project.genome` and `Ω.000` are unchanged; no merge to `main` occurs without review/approval.

## 10. Initial implementation order

**M0 — Inventory:** inspect the existing financial agent registry, model gateway, VX runtime, tests, and open financial PRs to avoid duplicating existing work.

**M1 — Contract and registry:** define JSON schemas and lifecycle/identity invariants; validate uniqueness and fail-closed behavior.

**M2 — One complete agent path:** implement one provider agent end-to-end through the approved gateway, with read-only research, bounded calculations, user-visible status, and evidence receipt.

**M3 — Independent challenge and finance tests:** add calculation fixtures, adversarial cases, citation checks, and disagreement handling.

**M4 — Add connectors one by one:** OpenAI, Claude, Gemini, Grok, Mistral, then approved data and productivity tools. Each remains unavailable until configured and live-tested.

**M5 — Console and orchestration:** expose agent status, task DAG, progress, evidence, cost/latency, failures, and approval requests. Do not create a dashboard that merely fabricates runtime state.

**M6 — Evaluation and release:** run CI and end-to-end tests, attach evidence, and request human review. Do not merge automatically.

## 11. Status vocabulary

Use only: `SPECIFIED`, `IMPLEMENTED`, `TESTED`, `LIVE_PROBED`, `ACTIVE`, `DEGRADED`, `QUARANTINED`, `NOT_CONFIGURED`, `BLOCKED`.

Every status transition must reference evidence. Never label an agent `ACTIVE` based solely on a document, registry entry, installed package, or environment variable.

## 12. Explicit non-claims

This document does not claim live access to any external model, brokerage, market-data service, bank, personal portfolio, or financial account. It does not promise returns or call the system objectively the strongest in the world. It defines the path to measurable superiority through reproducible evaluation and controlled execution.
