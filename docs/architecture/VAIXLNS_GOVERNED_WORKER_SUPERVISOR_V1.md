# VAIXLNS Governed Worker Supervisor v1

**Status: PROPOSAL / reference implementation; runtime integration and CI evidence pending.**

## Purpose

Provide a bounded, auditable control plane for assigning work to explicitly registered specialist workers. This is an additive feature branch and does not alter `project.genome`, `Ω.000`, admission authority, or existing canonical registries.

## Components

- `runtime/agent_registry.py`: unique agent IDs, declared capabilities, enabled state, bounded attempt count; ambiguous routing is blocked.
- `runtime/task_scheduler.py`: task IDs and explicit QUEUED/RUNNING/SUCCEEDED/FAILED/BLOCKED lifecycle. Current storage is in-memory only.
- `runtime/supervisor.py`: capability-based dispatch; human approval required by default; bounded retries; structured receipts.
- `runtime/health_monitor.py`: local metadata summary only. It does not probe external services or assert that remote agents are online.
- `tests/test_agent_supervisor.py`: standard-library regression tests for approval, routing, duplicate registration, failure receipts, and health-scope labeling.

## Worker lifecycle

`INTENT → QUEUED → APPROVAL GATE → CAPABILITY RESOLUTION → RUNNING → RECEIPT`

Any missing/ambiguous capability or missing approval is blocked. Worker exceptions become `FAILED` receipts. There is no automatic publication, production deployment, destructive action, shell execution, or secret access in this reference implementation.

## Integration plan

1. Run `python -m unittest discover -s tests -p 'test_agent_supervisor.py' -v` in a clean checkout.
2. Wire into VX only through the existing governed runtime and tool-action envelope; do not enable direct tool calls.
3. Connect VLNS/NEXNET only after identity, endpoint, and contract evidence is independently verified.
4. Add persistent storage, authentication/authorization, deadlines, cancellation, structured event provenance, and provider adapters before production use.
5. Add CI and evidence receipts; do not mark VERIFIED until those checks execute and pass.

## Status semantics

A successful unit test demonstrates local behavior only. It does not prove provider connectivity, deployed workers, external system identity, or production readiness.
