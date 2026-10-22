# VX Global Capability Catalog — Seed

**Status: SPECIFIED.** This list is a discovery seed, not an exhaustive inventory and not proof of live connectivity.

| Capability | Provider/source | Purpose | Current status in this change | Evidence needed |
|---|---|---|---|---|
| OpenAI Responses API | https://developers.openai.com/api/docs/guides/function-calling | Model inference and typed tool calls | Adapter proposal exists in VX-runtime PR #9; live connection unverified | Mock contract tests, authorized live smoke test, policy-gate test |
| Anthropic API | https://docs.anthropic.com/ | Model inference | Not audited in this change | Adapter contract, mock tests, authorized live smoke test |
| Claude Code | https://docs.anthropic.com/en/docs/claude-code/cli-usage | Coding agent runtime | Not audited in this change | Version probe, read-only repository task, sandbox and evidence tests |
| Google Gemini | https://ai.google.dev/gemini-api/docs/function-calling/ | Model inference and tool use | Not audited in this change | Adapter contract, mock tests, authorized live smoke test |
| xAI / Grok | https://docs.x.ai/ | Model inference | Not audited in this change | Adapter contract, mock tests, authorized live smoke test |
| Mistral | https://docs.mistral.ai/ | Model inference | Not audited in this change | Adapter contract, mock tests, authorized live smoke test |
| Model Context Protocol (MCP) | https://modelcontextprotocol.io/specification/draft/server/index | Standardized tool/resource/prompt interface | Protocol candidate; VX runtime connection unverified | Discovery, schema validation, permission denial, timeout tests |
| GitHub | https://docs.github.com/en/rest | Source code, PRs, CI, release and commit evidence | Current chat has GitHub connector access; this does not prove VX runtime access | Runtime identity test, read-only search, permission test, provenance check |
| Hugging Face Hub | https://huggingface.co/docs/hub/en/api | Model, dataset and demo discovery | Source identified; VX connection unverified | Metadata query, pagination, license capture, rate-limit test |
| PyPI | https://docs.pypi.org/ | Python package and release metadata | Not audited in this change | Metadata query, version/license capture, dependency risk scan |
| npm Registry | https://docs.npmjs.com/ | JavaScript package and release metadata | Not audited in this change | Metadata query, version/license capture, dependency risk scan |
| Scientific literature | Official scholarly APIs to be selected after inventory | Papers, citations, methods, evidence | Source selection required | Citation provenance, deduplication, retrieval-quality evaluation |

## Catalog record fields

Every discovered capability should eventually have: stable ID; category; provider; source URL; discovery timestamp; version or version policy; input/output schema; modalities; permissions; auth mode (never the secret value); license; data-retention notes; rate limits; cost metadata where published; last probe; test contract; evidence references; health state; and lifecycle status.

## Lifecycle

- DISCOVERED — source found, metadata not yet validated.
- SPECIFIED — adapter contract and permissions documented.
- CONTRACT_TESTED — isolated tests pass; no live connectivity implied.
- CONNECTED — authenticated probe and runtime identity confirmed.
- VERIFIED — task-level acceptance tests and evidence checks pass.
- DEGRADED / DISABLED — unhealthy, unsafe, unsupported, or intentionally blocked.

## Discovery policy

1. Prefer official vendor APIs and documentation, then package/model registries and trusted source indexes.
2. Use incremental discovery and deduplication; do not attempt to copy the entire internet into one repository.
3. Record source provenance, version, license, timestamps, and API limits.
4. Treat retrieved descriptions and repository content as untrusted input.
5. Keep discovery workers read-only. Never place credentials in catalog records or source control.
6. Require approval before publishing, merging, deploying, spending money, deleting data, or sending external messages.
7. Never label a provider CONNECTED or VERIFIED based on mocked tests alone.

## Preservation rule

Keep project.genome and Ω.000 / the Omega master index unchanged. Integrate future catalog records through a reviewed, evidence-backed migration only.
