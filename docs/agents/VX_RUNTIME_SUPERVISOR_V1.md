# VX Runtime Supervisor V1

**State:** implementation proposed on a feature branch; CI evidence pending.  
**Authority:** VAIXLNS registry and governance remain canonical.  
**Execution boundary:** VX adapter injection only.  
**Canonical adoption:** not performed.

## Implemented boundary

- Accepts only `OBSERVE`, `RESEARCH`, and `PROPOSE`.
- Rejects production mutation, canonical writes, release/deploy, unknown operations, self-promotion, missing task identity, malformed evidence references, oversized inputs, and task-budget overflow.
- Holds when the named adapter is not explicitly configured.
- Wraps every adapter result as `PROPOSED`; worker output cannot promote itself to `VERIFIED`.
- Does not load credentials, discover providers, access the network, mutate repositories, or write `project.genome` / `Ω.000`.

## Task envelope

Required fields: `task_id`, `agent_id`, `adapter_id`, `operation`, and `input`. Research/proposal operations require non-empty `evidence_refs` by default. The adapter is injected by the caller and is not presumed live or admitted.

## Run tests

```bash
python -m unittest tests.test_runtime_supervisor -v
```

## Admission blockers

This module alone does not prove a live model, MCP server, persistent task ledger, distributed scheduler, sandbox, or production deployment. Before activation, bind it through the existing VX Federation Gate and action-envelope schema; add durable event receipts, provider-specific health checks, isolated execution, independent review, and integration tests. Until then the truthful status is `PROPOSED / ADAPTER_NOT_CONFIGURED_HOLD`.
