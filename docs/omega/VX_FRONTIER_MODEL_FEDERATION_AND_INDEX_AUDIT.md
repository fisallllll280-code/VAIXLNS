# VX Frontier Model Federation and Ω.000 Audit

**Snapshot date:** 2026-10-17  
**Status:** implementation proposal; provider connectivity has not been tested by this change.

## 1. What the current master index actually contains

A read of `registry/omega/omega-000-master-index.json` on the working branch found:

- `index_id = Ω.000`, declared `CANONICAL`
- 11 top-level records: 5 `SYSTEM`, 4 `CAPABILITY`, 1 `RUNTIME_SURFACE`, 1 `CONTROL`
- 40 evidence-reference entries
- no duplicate record IDs in this snapshot
- all 11 records have `id`, `type`, `lifecycle_state`, and `epistemic_state`

This is a compact control-plane index, **not** the complete atomic 0001–2750 legacy corpus. The repository's recovery status says the historical corpus is approximately 2,750 entries across 40+ families, but the full item-by-item source is not yet exposed as a complete atomic table. Do not infer complete recovery from the 11 records.

## 2. Audit behavior

`scripts/audit_omega_index.py` is a read-only audit. It checks required fields, duplicate IDs, parent references, evidence path safety and file presence, and state distributions. It emits a derived JSON report and does not rewrite the index or genome.

Run locally:

```bash
python scripts/audit_omega_index.py --root . --out build/omega-index-audit.json
```

Interpretation:
- `integrity_gate=PASS` means the checks enforced by this script passed; it is not a blanket project verification.
- `evidence_completeness=INCOMPLETE` flags unresolved local evidence paths or parent references.
- a report over a Git checkout cannot prove that external archives or unindexed historic records were recovered.

## 3. Candidate frontier models

The JSON registry records provider API candidates and routing roles from vendor documentation available on the snapshot date:

| Provider | Candidate model ID | Initial role | Source |
|---|---|---|---|
| OpenAI | `gpt-6-astra` | complex reasoning, architecture, coding | [OpenAI model catalog](https://developers.openai.com/api/docs/models) |
| Anthropic | `claude-opus-5` | long-horizon coding and synthesis | [Claude model overview](https://platform.claude.com/docs/en/models/overview) |
| Google | `gemini-4-argon` | large-context and multi-step analysis | [Gemini API model catalog](https://ai.google.dev/gemini-api/docs/models) |
| xAI | `grok-4.7` | alternative reasoning and coding | [xAI model catalog](https://docs.x.ai/developers/models) |
| Mistral | `mistral-large-4` | independent comparison and open-weight evaluation | [Mistral model catalog](https://docs.mistral.ai/models) |

Model names, aliases, access tiers, and endpoints can change. Verify exact model availability in each provider account before deployment. This list is a sourced candidate set, not an objective universal ranking; choose the winner by VAIXLNS task-specific evaluations.

Meta's newly announced Muse family is not included as an API-ready provider here because an accessible production API/model identifier was not established in this audit.

## 4. Execution design

1. **Fast path:** deterministic local checks and the lowest-latency model that passes task-specific evaluation.
2. **Deep path:** one frontier model plans; bounded specialist workers handle independent subtasks in parallel.
3. **Independent review:** a different provider or deterministic verifier checks critical outputs.
4. **Escalation:** disagreement, missing evidence, or high-risk changes go to a human.
5. **Evidence:** record provider, exact model ID, prompt/task hash, start/end times, outcome, test results, token/cost metadata when available, and evidence references. Never store secrets or hidden chain-of-thought.
6. **Bounds:** parallelism capped at five; no uncontrolled recursive agent spawning; no model can promote its own claim to `VERIFIED`.
7. **Repository writes:** proposed diffs only until CI passes and a human approves; never mutate `project.genome` or `Ω.000` through the model router.

## 5. What is not proven yet

- No live provider API calls were made by adding the registry.
- No API keys were read or created.
- No measured speedup is claimed for the complete VX execution cycle.
- The full historical index recovery remains unproven until the atomic source records and hashes are available and reconciled.
