# VX Federation Runtime — Operator Runbook

**Status:** executable reference runtime added; external connectors remain inactive until separately configured, tested, and admitted.

## Components

- `scripts/vx_federation_runtime.py`: deterministic, fail-closed selection, budget/data-policy checks, OpenAI-compatible and Anthropic adapters, and hash-only evidence receipts.
- `registry/federation/vx_model_connectors.v1.json`: starter connector inventory for hosted models, local runtimes, MCP, repositories, and collaboration.
- `tests/test_vx_federation_runtime.py`: policy, evidence, credential, capability, and fail-closed regression tests.
- `.github/workflows/vx-federation-runtime.yml`: CI validation and tests.

## Run offline validation

```bash
python scripts/vx_federation_runtime.py --check
python -m unittest tests.test_vx_federation_runtime -v
```

This performs no network calls.

## Connector activation requirements

A connector remains `NOT_CONFIGURED` unless all of the following are satisfied outside this reference runtime:

1. Exact endpoint, model ID, and supported capabilities are confirmed.
2. Secrets are supplied through the deployment secret manager/environment, never committed.
3. The adapter is implemented and its provider-specific contract tests pass.
4. Data classification, region, retention, tenant isolation, tool scopes, and budgets are reviewed.
5. Current contract digest and independently reviewable runtime evidence are attached.
6. The canonical authority approves the activation state change.

Do not change a registry entry to `ACTIVE_VERIFIED` just to make routing succeed. This code intentionally has no automatic activation, fallback to weaker policy, credential discovery, tool execution for unimplemented adapters, or remote probing in its preflight mode.

## Current adapter coverage

- `openai_compatible`: implemented for explicitly configured OpenAI Chat Completions-compatible endpoints.
- `openai_compatible_local`: same wire contract, but callers must explicitly instantiate the local/no-auth adapter and use a trusted local endpoint.
- `anthropic_messages`: implemented for the Anthropic Messages API.
- `google_generative_ai`: implemented for Gemini `generateContent`, with the API key sent in a header rather than the URL.
- Azure, Bedrock, Vertex, MCP, GitHub, Slack, and other catalog entries remain inventory placeholders only; their adapters are not implemented or active in this commit.

The registry is a roadmap and inventory, not evidence of working connections. A valid registry check proves only local structure.
