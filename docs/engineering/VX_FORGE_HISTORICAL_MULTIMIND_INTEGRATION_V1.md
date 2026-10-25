# VX Engineering Forge — Historical Recovery & Multi-Mind Integration v0.1

Status: PROPOSED. Read-only audit 2026-10-25. No claim of deployed integration.

## Reuse, do not duplicate
| Existing source | Observed role | Integration decision |
| --- | --- | --- |
| docs/indexes/V_PHYSICAL_MATHEMATICAL_COMPUTATION_PRIMITIVES_V2.md | USO, Law Compiler, invariants, numerical error, simulation-vs-measurement distinctions | preserve as scientific object contract; PROPOSAL |
| docs/indexes/V_COMPUTATIONAL_REALITY_ENGINE_V1.md | historical computational reality formulation | review full content and lineage before adoption |
| docs/indexes/V_MULTIDOMAIN_SYSTEM_SYNTHESIS_ENGINE_V1.md | historical cross-domain synthesis formulation | review before binding |
| tools/impossibility_engine/engine.py | deterministic feasibility triage, not proof of impossibility | expose as bounded feasibility tool |
| tools/impossibility_engine/fabric.py | bounded worker coordinator, cache and remote-worker configuration | evaluate as local worker substrate; remote calls disabled |
| scripts/omega_engineering_cycle.py | memory -> innovation candidate -> task plan; novelty unassessed | preserve provenance and proposals |
| registry/models/vx-frontier-model-registry.json | five provider candidates, SPECIFIED_NOT_CONNECTED | discovery registry only; no connection claims |
| tools/model_mcp/server.py | explicit model invocation with credentials | no auto-calls, no spend |
| tools/engineering_test_router.py | conservative test selection | use only for fast feedback, never waive CI |

## Federation design: 10,000+ catalog entries != 10,000 active sessions
1. Discovery adapters ingest paginated, versioned catalogs and deduplicate provider/model/version/endpoint.
2. Store catalog metadata in searchable index; capability, modalities, latency, cost, license, region, safety and provenance.
3. Select bounded candidate pool by task and governance; default 0 paid calls and 0 remote calls.
4. Evaluate selected models with blinded benchmark tasks, deterministic validators, different-provider adversarial review and calibrated uncertainty.
5. Bound concurrent active sessions, retries, tokens, time and spending. Do not fan out to all models.
6. VX is sole action gateway; VV is read-only observer; Ω records decision, receipts and independent verification.
7. MCP 2026-07-28 capability discovery and version negotiation must be implemented as a separate compatible adapter; no implicit trust of remote tool metadata.

## Research domains and science
- Mathematics: formal statement, proof obligations, independent proof checking, counterexamples.
- Computational mathematics: precision, stability, convergence, error propagation, independent solver comparison.
- Physics: units, conservation laws, boundaries, model validity, uncertainty, experiment-vs-simulation.
- Software/computer engineering: profiling, deterministic tests, hardware simulation, resource accounting.
- Impossibility: contradiction triage and alternative hypotheses; never assert proven physical impossibility from heuristic output.

## Proposed pipeline
Historical source inventory -> exact source SHA + Original/Derived -> ontology and typed contracts -> engineering gap -> competing hypotheses -> independent solvers/models -> simulation -> adversarial falsification -> evidence receipts -> admission gate -> human review.
Do not collapse SIMULATED, NUMERICALLY_VERIFIED, FORMALLY_PROVEN and MEASURED.

## Immediate gates
G0: pin source commits, inspect permissions, verify protected files.
G1: run existing test suites and baseline metrics before edits.
G2: offline catalog fixture and 10000-record indexing benchmark, memory ceiling and query P95.
G3: local multi-agent scheduling with bounded fan-out and fault injection; no provider calls.
G4: independent reviewer checks evidence and original index continuity.
All steps require receipts. No merge, publish, secrets, external spending, or changes to project.genome or Ω.000.

## Research sources
- MCP 2026-07-28 specification: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/index.mdx
- OpenRouter model catalog API: https://openrouter.ai/docs/api/api-reference/models/get-models
These are interoperability references, not authorization to contact paid endpoints.
