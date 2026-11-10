# VAIXLNS Deep Agent and Innovation Orchestrator V1

**State:** IMPLEMENTED PLANNER / PROVIDER EXECUTION NOT IMPLEMENTED BY THIS MODULE  
**Canonical owner:** VAIXLNS  
**Role:** deterministic mission planning over the existing 13-role agent fabric.

## Why this slice exists

The repository already contains specialized agent identities, handoff contracts, mind-federation links, and an innovation measurement registry. This module adds a deterministic planning boundary that turns a mission into a typed, ordered task graph and makes unsupported capabilities visible before any provider or tool is invoked.

It does not replace ARC-X, the master registry, NEXENT candidate generation, VX execution, or the existing governance gate.

## Run

\`\`\`bash
python -m unittest discover -s tests -p 'test_innovation_orchestrator.py' -v
python -c "from agents.innovation_orchestrator import MissionRequest, build_mission_plan; import json; print(json.dumps(build_mission_plan(MissionRequest(intent='audit the engineering fabric')), indent=2))"
\`\`\`

## Contracts

- The current default chain contains 13 registered roles; each task has stable IDs, typed input/output artifacts, dependencies, state, and capability coverage.
- Equivalent normalized requests produce the same plan hash.
- Required capabilities absent from the roster produce a \`BLOCKED\` plan.
- Source references and user constraints are untrusted context; they are not executable instructions.
- Canonical writes, production deployment, financial transfers, and self-promotion are rejected as autonomous requested actions.
- Tasks are plan-only: no model provider calls, no external tool calls, no execution events, no production mutation.
- Authority remains \`PENDING\`; proof remains \`PENDING\`; semantic correctness is \`NOT_CLAIMED\`.

## Architecture relationship

\`\`\`text
Mission
  -> Agent Registry / Capability Coverage
  -> Deterministic Task Plan
  -> Source Discovery + ARC-X Evidence
  -> Innovation / Novelty / Counterevidence
  -> Architecture + Engineering Contract
  -> Security + Tests + Proof Integrity
  -> Governance Recommendation
  -> [separate authorized decision]
  -> VX execution request (future integration; not implemented here)
\`\`\`

## Evidence boundary

A valid plan proves that the registered workflow can be deterministically planned and structurally validated. It does not prove that agents are live, that a provider was contacted, that research is complete, or that an innovation is novel or production-ready. Those claims require separately recorded provider, source, test, runtime, and governance evidence.
