# VLNS Cross-System Federation and Engineering Dashboard v1

**Authority:** VAIXLNS  
**Status:** PROPOSED / EVIDENCE-BACKED INVENTORY  
**Dashboard implementation branch:** `feat/sovereign-command-console-v1`  
**Scope:** VLNS's documented properties, cross-system contracts, engineering views, and explicit integration gaps.

## 1. Findings from the indexed repository sources

The inspected canonical sources define four independent system identities:

- **VAIXLNS** — canonical governance, registry, admission, provenance and recovery.
- **VLNS** — knowledge/discovery and model/semantic activation boundary.
- **VX** — governed execution, observation, replay and verification.
- **NEXNET** — discovery network and architecture/research synthesis.

The candidate repository **`fisallllll280-code/NAXLNS` is not proven to be identical to VLNS**. Its own federation role document and the canonical four-system reconciliation both retain this mapping as `UNVERIFIED`. The integration must preserve this state and must not rename, collapse or merge the repositories based on similar names.

The inspected NAXLNS repository tree contained nine entries, principally README, repository contract, federation documents and a conformance workflow. The README is largely an engineering directive/specification. It is not by itself proof that the proposed model fabric, adapters, marketplace or persistent knowledge runtime exist as executable code.

## 2. Canonical cross-system topology

```text
NEXNET / NEXENT candidate
          │ research / architecture candidates (PROPOSED)
          ▼
VLNS identity (UNVERIFIED) ── discovery + evidence proposals ──▶ VAIXLNS
          │                                                    │
          │ model activation envelope (SPECIFIED)              │ admission / policy
          ▼                                                    ▼
         VX ───────── events / observations / replay ───────▶ VAIXLNS
          │
          └── execution authority remains within VX's admitted scope
```

This topology is a contract map, **not a live-connectivity claim**. In particular, the last recorded VLNS connection entry says `UNREACHABLE_FROM_CURRENT_EXECUTION_ENVIRONMENT` and `authenticated_connection=false` (probe dated 2026-10-06). The dashboard must label it as a historical observation, not a fresh probe.

## 3. VLNS attribute model

The machine-readable record `registry/federation/vlns-capability-index.v1.json` separates:

1. **Identity:** system ID, candidate repository surface, lineage status and canonical owner.
2. **Role:** knowledge/discovery, adversarial analysis, repository intelligence and proposal production.
3. **Capabilities:** discovery, adversarial analysis, architecture/capability candidates, evidence candidates, reconstruction inputs, model activation and external-integration gate.
4. **Provider/model contract:** model/provider/version, role, capability profile, context hash, tool/permission profile, constraints, provenance and activation ID.
5. **Authority envelope:** deny-by-default; model connection grants no execution authority; canonical admission remains with VAIXLNS.
6. **Integration edges:** source, target, contract, allowed payload, prohibited effects, live status and evidence references.
7. **Implementation maturity:** SPECIFIED vs PROPOSED vs IMPLEMENTED/VERIFIED. Unobserved code is not inferred.
8. **Observability:** startup, health, test, event, evidence and replay requirements.
9. **Engineering readiness:** identity, endpoint, runtime, adapter, telemetry, index and cross-system integration gaps.
10. **Provenance:** each material property has source references; conflicts and unknowns remain explicit.

## 4. Engineering dashboard panels

| Panel | Question it answers | Current command |
|---|---|---|
| Federation Overview | What are the four system identities and their evidence states? | `federation status` |
| System Inspector | What is VLNS, what is its repository surface, and what authority does it have? | `federation inspect VLNS` |
| Capability Explorer | Which capabilities are specified, proposed, implemented or unverified? | `federation capabilities all` |
| Attribute/Index Explorer | What is each property and which source supports it? | `federation attributes VLNS` |
| Integration Links | Which edges are documented versus live/authenticated? | `federation status` |
| Gap/Release Board | What blocks a safe integration or engineering release? | `federation gaps` |
| Evidence & Proof | Which local canonical structure checks pass, and what do they not prove? | `proof verify` |

These commands read local repository assets. They do not invoke remote systems, run models, deploy services, or promote canonical states.

## 5. Safe connection protocol

Each new live connector must pass:

1. **Identity:** owner/repository/system identity is pinned to evidence.
2. **Contract:** versioned request/response schema and failure modes.
3. **Credentials:** secrets supplied by environment/secret manager; never committed in source or dashboard data.
4. **Network:** HTTPS by default; explicit endpoint allow-list; timeout and response-size limit.
5. **Sandbox:** read-only discovery first; no arbitrary shell or production mutation.
6. **Conformance:** contract tests, negative tests, authentication failure tests and timeout behavior.
7. **Observability:** correlation ID, source revision, timestamps, structured event, response hash and replay reference.
8. **Independent verification:** tests and evidence checked separately from the agent that proposed the connector.
9. **Admission:** VAIXLNS policy/admission decides whether the connector may be used.
10. **Rollback:** connector disable switch and preserved prior records/evidence.

## 6. Cross-platform engineering UI

The console UI is responsive HTML and can be displayed in modern desktop and mobile browsers. Its Python bridge currently binds to loopback only. **Do not expose it by changing the bind address alone.** Phone access to a remote runtime requires an authenticated HTTPS gateway or an approved hosted UI/API with scoped identity, session protection, CSRF/origin controls where applicable, rate limiting and audit records.

The dashboard should present the following as independent states:
- user-interface reachable;
- control API reachable;
- credential authenticated;
- contract conformant;
- target system healthy;
- operation executed;
- result independently verified;
- result admitted by governance.

None of these states may be inferred from another.

## 7. Immediate implementation order

1. Keep system identities independent until evidence resolves VLNS↔NAXLNS and NEXNET↔NEXENT.
2. Use `registry/federation/vlns-capability-index.v1.json` as the dashboard's evidence-linked catalog.
3. Add read-only command surfaces for system state, attributes, capabilities and gaps.
4. Run the new regression tests and the console CI workflow.
5. Build the first live connector only after its target endpoint and credentials are supplied in the target environment.
6. Validate the model activation envelope with one local Ollama provider before expanding the provider portfolio.
7. Promote any capability only after reproducible runtime evidence and explicit admission.

## 8. Acceptance criteria

- The 4 system records and every property preserve system identity and source references.
- `VLNS ↔ NAXLNS` remains explicitly UNVERIFIED.
- The prior connection status is shown as historical and unauthenticated, not current health.
- The capability/property explorer performs local indexed search and returns evidence paths.
- Unknown commands remain fail-closed; no shell command or network probe is added to the dashboard command engine.
- Tests cover missing registry, unresolved identity, capability filtering and gaps.
- The UI does not say an agent, provider, service or integration is live unless a separate probe/execution evidence establishes it.
