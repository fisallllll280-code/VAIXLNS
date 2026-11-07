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



## Ω.000 decomposition

`scripts/decompose_omega_index.py` creates a deterministic, read-only graph of the current master index:
- **Nodes:** one per record, with owner, type, lifecycle, epistemic state, and evidence-reference count.
- **Edges:** parent and evidence relationships, including external evidence URLs.
- **Findings:** duplicate IDs, missing required fields, unsafe or unresolved local evidence paths, partial implementations, and proposed items.
- **Source integrity:** SHA-256 of the exact source bytes and elapsed analysis time are included in the derived report.

Run it with:

```bash
python scripts/decompose_omega_index.py --root . --out build/omega-index-decomposition.json
```

It reads the checked-out index and writes only to the requested output path. It does not rewrite `Ω.000` or `project.genome`. It deliberately reports the scope limitation: current file records are not proof of the historical 0001–2750 corpus.

The first structural reading of the canonical file on `main` (SHA-256 source blob tracked by GitHub as `cbd3b32f7a9bf74650fdae02a8ebb0831dca84dc`) found 11 records, 40 evidence references across 38 distinct reference strings, no duplicate IDs, and no missing required record fields. Distribution: 5 SYSTEM, 4 CAPABILITY, 1 RUNTIME_SURFACE, 1 CONTROL; epistemic states: 4 IMPLEMENTED, 6 SPECIFIED, 1 PARTIAL. These counts describe the file, not the implementation status of the entire platform.

## 4. API bridge (bounded, opt-in)

`scripts/vx_model_federation.py` provides a standard-library client for the five provider API families in the registry. It reads credentials only from process environment variables, fans out to at most five providers concurrently, reports `NOT_CONFIGURED` when a credential is absent, and marks outputs as proposals only.

Example (this makes live, potentially billable API requests for configured providers):

```bash
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export GOOGLE_API_KEY=...
export XAI_API_KEY=...
export MISTRAL_API_KEY=...
python scripts/vx_model_federation.py --prompt "Review this non-sensitive engineering proposal and list risks."
```

Use only keys that you have configured and authorized. Never put real secrets in the shell history, repository, issue, or CI logs. For a single provider, use `--providers openai` (or `anthropic`, `google`, `xai`, `mistral`). The client does not open pull requests, execute generated code, or modify canonical files. Unit tests mock network access; they do not prove live provider connectivity.

## 5. Execution design

1. **Fast path:** deterministic local checks and the lowest-latency model that passes task-specific evaluation.
2. **Deep path:** one frontier model plans; bounded specialist workers handle independent subtasks in parallel.
3. **Independent review:** a different provider or deterministic verifier checks critical outputs.
4. **Escalation:** disagreement, missing evidence, or high-risk changes go to a human.
5. **Evidence:** record provider, exact model ID, prompt/task hash, start/end times, outcome, test results, token/cost metadata when available, and evidence references. Never store secrets or hidden chain-of-thought.
6. **Bounds:** parallelism capped at five; no uncontrolled recursive agent spawning; no model can promote its own claim to `VERIFIED`.
7. **Repository writes:** proposed diffs only until CI passes and a human approves; never mutate `project.genome` or `Ω.000` through the model router.

## 6. What is not proven yet

- No live provider API calls were made by adding the registry or client.
- No API keys were read or created.
- No measured speedup is claimed for the complete VX execution cycle.
- The full historical index recovery remains unproven until the atomic source records and hashes are available and reconciled.
