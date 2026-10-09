# VAIXLNS Index-Driven Workflow V1

**State:** IMPLEMENTATION CANDIDATE / REFERENCE PLANNER  
**Canonical owner:** VAIXLNS  
**Registry:** registry/agents/indexed-workflow.v1.json  
**Master index:** Ω.000  
**Legacy mapping:** incomplete; missing source rows remain explicitly unmapped.

## Purpose

This vertical slice links the existing agent operating model to an executable, deterministic workflow planner. A task is mapped to a named workflow, agent identities, each agent's primary system, capability coverage, expected outputs, handoffs, authority ceiling, and a deterministic plan trace.

It complements (rather than replaces) the Master Index, agent operating model, repository federation index, admission gate, and VX federation gate.

## Canonical boundaries

- **VAIXLNS:** canonical identity, registry, lineage, governance, and admission boundary.
- **NEXENT:** discovery, research, capability analysis, architecture search, and proposals. It does not directly mutate canonical or production state.
- **VV:** knowledge reconciliation, contradiction/security review, verification, and proof review.
- **VX:** execution/runtime and recovery inside an admitted contract. Runtime dispatch is disabled in this reference planner.
- **XV:** planning and decision preparation; no self-granted authority.

Every agent AG-001 through AG-013 has exactly one primary_system_id. A task may cross systems only through a declared pipeline step and a typed handoff. An agent name, model, tool, or repository permission does not itself confer authority.

## Workflow

INTENT → INDEX/CONTEXT → IDENTITY & LINEAGE → CAPABILITY MATCH → PLAN / RESEARCH / SYNTHESIS → ADVERSARIAL REVIEW → INDEPENDENT VERIFICATION → GOVERNANCE REVIEW → AUTHORIZED ADMISSION → EXECUTION → OBSERVE → RECOVERY / REPLAY

The selected route is chosen from the declared work_type pipeline in the routing registry. Each handoff records the next agent and requires contract validation. Missing capabilities and unknown target systems fail closed.

## Automatic gates

- **Registry integrity:** unique system/agent IDs; all agents have a primary owner; all pipeline references resolve.
- **Non-loss boundary:** legacy IDs not recovered from the source remain Ω.000/UNMAPPED.
- **Authority boundary:** write scopes (DOCUMENTATION, REPOSITORY, CANONICAL, PRODUCTION, EXTERNAL), high risk, critical risk, and runtime requests are held for independent authority review.
- **Verification boundary:** AG-010 must be present before AG-011 runtime work in any pipeline that includes execution.
- **No promotion:** a plan does not promote an artifact to IMPLEMENTED, VERIFIED, or CANONICAL.
- **Trace integrity:** workflow plan events form a deterministic hash chain. That trace is not a runtime ledger or proof of the underlying work.
- **Reference-only execution:** the planner does not call model providers, external tools, GitHub mutations, or VX runtime. AG-011 remains blocked with BLOCKED_REFERENCE_PLANNER_ONLY.

## Run locally

    python scripts/indexed_workflow.py --validate-registry
    python scripts/indexed_workflow.py --request tests/fixtures/research-request.v1.json --output indexed-workflow-plan.json
    python -m unittest discover -s tests -p 'test_indexed_workflow.py' -v

A successful result means the registry contracts and plan generator passed their reference tests. It does not establish that all historical index rows have been recovered, that live agents are connected, or that production execution is ready.

## Next required integration

1. Reconcile the machine-readable Ω.000 source row by row without fabricating missing IDs.
2. Connect typed handoffs to actual agent/provider adapters and verify provider identities.
3. Bind authorization to a trusted issuer rather than a caller-supplied string.
4. Persist runtime events in the governed event/ledger fabric and capture replay evidence.
5. Demonstrate failure containment, recovery, independent verification, and explicit governance admission before enabling any write-capable adapter.
