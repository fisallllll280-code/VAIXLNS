# Server Discovery & Innovation Fabric v1

**Canonical home:** VAIXLNS  
**Research and candidate synthesis:** NEXENT  
**Runtime adapter and execution boundary:** VX  
**Status:** IMPLEMENTED CANDIDATE — local unit tests must pass in CI; this module does not prove that any external service is live or admitted.

## Objective

Extend the existing bounded server discovery probe and registry without duplicating them. The probe establishes only point-in-time reachability for explicitly configured targets. This fabric evaluates whether a discovered server candidate fills a demonstrated capability gap and has enough independent evidence to be submitted to governance.

## Lifecycle

```text
WORLD / ARCHIVE / REPOSITORY / EXPLICIT ENDPOINT
  -> DISCOVER
  -> IDENTITY + SOURCE REVISION + CONTRACT
  -> QUARANTINE IF UNKNOWN
  -> CAPABILITY GAP + PRIOR-ART REVIEW
  -> SANDBOX + SECURITY + RECOVERY/REPLAY TESTS
  -> INDEPENDENT VERIFICATION
  -> EVIDENCE-PACKAGE REVIEW
  -> ELIGIBLE_FOR_GOVERNANCE
  -> VAIXLNS AUTHORITY DECISION (separate)
  -> VX ADAPTER / RUNTIME ADMISSION (separate)
```

## Server families to inventory

- AI / agent and MCP servers
- Local and remote inference providers
- Knowledge, retrieval and indexing services
- Code execution and sandbox services
- Vision and image-generation services
- Simulation, scientific compute and digital-twin services
- Security, policy and verification services
- Infrastructure, queues, databases and observability services
- Candidate servers that may fill a presently unserved capability

These are search families, not evidence that a specific product is novel or already connected.

## Innovation test

A candidate is not called innovative merely because it is new to this repository. It must identify an explicit capability gap, show a capability delta against the declared baseline, preserve source revision and evidence, document prior-art search coverage, and pass identity, contract, sandbox, recovery/replay, security, and independent-verification gates.

The implementation emits one of:
- `RESEARCH_REQUIRED`: a required record or gate is missing.
- `QUARANTINED`: identity or source reference is unsafe/unverified.
- `REJECTED`: a hard check failed or no capability delta remains.
- `ELIGIBLE_FOR_GOVERNANCE`: complete candidate packet for independent review only.

No decision from this module authorizes runtime, canonical writes, deployment, spending, or external side effects. `requested_runtime_admission` is audit input only and cannot change the result.

## Safety and reproducibility

- The existing `tools/server_discovery_probe.py` remains the only low-level endpoint probe in this path: GET-only, bounded, no redirect following, no subnet scanning.
- This evaluator performs no network activity and never dereferences submitted source URIs.
- Candidate digests use stable canonical JSON and SHA-256 for integrity correlation, not digital signatures.
- A changed source revision, contract, capability claim, security profile, or evidence packet requires reassessment.
- The code reports eligibility for a separate governance review; it does not claim novelty, truth, production-readiness, or trust by itself.

## Test command

```bash
python -m unittest discover -s tests -p "test_server_innovation_fabric.py" -v
```

The test suite covers the governance boundary, missing identity, contradictory prior art, no capability delta, sandbox failure, unsafe source references, deterministic ordering, and candidate self-authorization attempts.
