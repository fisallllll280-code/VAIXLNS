# VX Adaptive Cognitive Routing — Experimental v0.1

Status: IMPLEMENTED MODULE / LOCAL UNIT TESTED; NOT LIVE-CONNECTED; NOT VERIFIED FOR PRODUCTION.

## Scope
Add evidence-gated model ranking to the existing `intelligence_federation` package. Existing provider clients in `scripts/vx_model_federation.py` and the sovereign contract remain unchanged. This module does not call providers, train model weights, mutate index canon, or make automatic purchases.

## Decision
Only registry-admitted ACTIVE candidates with required capabilities, sufficient authorization, matching sovereignty and cost <= the explicit task budget are eligible. Returned selection is PROPOSED, not executed. All provider invocations must revalidate the actual runtime identity, policy, credential scope and provider health. Never trust caller-supplied ACTIVE without validating it against the authoritative admission registry.

Verified quality feedback with a non-empty evidence identifier changes ranking via a smoothed average; scores not independently verified are ignored. Current scores are model-level and not domain-specific. This is an initial prototype only. Before production, bind evidence to a specific task family, benchmark, version, identity, validity interval and verifier signature; deduplicate receipts and resist collusion and gaming.

## Next stages
1. Connect the authoritative provider registry and policy engine, with fresh signed admission receipts. Add read-only discovery of OpenAI, Anthropic, Gemini, xAI, Mistral, and approved local/MCP interfaces where APIs are supported.
2. Create per-task expert councils: proposer, challenger, formal methods reviewer, security reviewer, executor and independent evaluator. Agreement is not proof.
3. Build a permission-aware, provenance-preserving memory that learns from tested outcomes rather than copying all conversation contents. Include deletion and revoke propagation.
4. Route discovery hypotheses through NEXENT, model activation through VLNS as approved, and all invocation via VX; no bypass of VAIXLNS governance.
5. Run offline benchmarks, ablation studies, regression gates and cost/latency/quality comparisons before enabling adaptive selection. Roll back regressions.
6. Explicit approval for any real financial expense, repository merge, production release or cross-provider transfer of sensitive data.

## Tests
`python -m unittest -v tests/test_vx_adaptive_router.py` (or discover by pattern when tests is not an import package).
Seven tests were executed locally on 2026-10-21 against an equivalent standalone implementation. Repository CI and live provider connectivity are NOT claimed.

## Protected invariants
No changes to `project.genome` or `Ω.000`; no merge to main; spending ceiling is SAR 0 absent separate approval; no unverified promotion; No Proof = No Commit.
