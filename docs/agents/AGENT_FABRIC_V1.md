# VAIXLNS Agent Fabric V1 — Research, Investigation, and Engineering Handoffs

**State:** IMPLEMENTED CODE / TESTED IN CI; deployment and live model bindings are separate.  
**Canonical owner:** VAIXLNS  
**Execution relationship:** NEXENT discovery → VAIXLNS evidence/registry → VX simulation and execution → Innovation Control promotion gate.

## Authority rule

Agents are bounded role identities, not autonomous authorities. They may search, recover, compare, design, test, and recommend. No agent in the default chain may directly execute production changes or promote its candidate to \`VERIFIED\` or \`CANONICAL\`. The authorized governance path remains separate.

## Thirteen-role handoff chain

1. **Orchestrator:** decomposes mission and routes bounded tasks.
2. **Source Discovery:** runs approved GitHub, web, repository and source searches.
3. **Archive Recovery:** retrieves legacy records and preserves original identifiers.
4. **Claim Atomizer:** binds claims and excerpts to source identities.
5. **Novelty & Lineage:** finds aliases, duplicates, derivatives and supersession links.
6. **Counterevidence:** searches for contrary evidence, failure modes and alternate explanations.
7. **Architecture Synthesis:** creates competing candidate designs.
8. **Engineering Contract:** defines invariants, interfaces, state and failure contracts.
9. **Implementation Planner:** defines bounded work, dependencies, rollback and acceptance criteria.
10. **Security Adversary:** challenges authority boundaries, attack paths and blast radius.
11. **Test & Replay:** converts contracts into deterministic tests and reproduction steps.
12. **Proof Integrity:** checks provenance, digest, freshness, verifier diversity and evidence completeness.
13. **Governance Review:** prepares a recommendation package; it does not make the final canonical decision.

## Typed handoffs

Each agent declares accepted input artifacts, output artifacts, capabilities, and an authority scope. The registry rejects duplicate identities, unknown IDs, mismatched adjacent handoff contracts, and any role configured to self-promote. The canonical chain is deterministic and integrates with \`agents.mind_federation\`; federation links do not imply that a live model/server is connected.

## Binding to the research decision fabric

The provider-neutral implementation in \`VAIXLNS-unified/innovation_control/research_fabric.py\` implements focused source-coverage, novelty/lineage, claim-adversary, engineering-completeness and provenance-integrity roles. This canonical roster supplies the broader federation/handoff contract around that implementation. Provider adapters and live runtime bindings must be admitted and tested separately.

## Required proof before admission

- source identities and revisions are traceable;
- supporting and refuting claims are preserved;
- historical coverage gaps are explicit;
- similar names are not collapsed without evidence;
- engineering contract, security and recovery fields are complete;
- deterministic tests/replay and proof package are available;
- separate authorized promotion decision is recorded.
