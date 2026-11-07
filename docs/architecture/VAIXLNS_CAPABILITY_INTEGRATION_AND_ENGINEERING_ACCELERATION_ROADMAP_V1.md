# VAIXLNS Capability Integration and Engineering Acceleration Roadmap v1

**Status:** PROPOSED — repository changes are not considered live integrations until independently tested.
**Authority:** project.genome::v1.0.0; Ω0_GENESIS_CORE; Ω.000
**Principle:** use a tool only when it closes a named capability gap; retain a provider-neutral contract so the system is not locked to one vendor.

## 1. Objective

Create a capability-oriented orchestration layer that can select tools and services for a task, validate the contract, execute in an isolated environment, capture evidence, and submit a proposed result to independent governance. The aim is faster composition and stronger engineering, not a large collection of disconnected integrations.

## 2. Capability contract

Every tool/provider adapter must declare:
- stable adapter ID, provider, version, owner, source revision and identity state;
- capabilities, accepted input/output schemas and supported file types;
- authentication method and least-privilege scope (never store secrets in the manifest);
- timeout, retry, rate-limit, cost and cancellation behavior;
- data classification, retention expectations and outbound-data boundary;
- idempotency key and replay behavior;
- evidence receipt, provenance, content digest and failure semantics;
- sandbox requirement, side-effect class and explicit authorization requirements;
- conformance test suite and last verified revision.

A tool name, connection, healthy endpoint or successful response is not proof that its output is correct or that the integration is production-ready.

## 3. Provider-neutral capability classes

| Capability class | Candidate tools/adapters | Primary use | Admission rule |
|---|---|---|---|
| Source control and review | GitHub connector/API, Actions | inspect source, propose changes, run CI, review PRs | pin branch/commit; protected branches; CI and review required |
| Coding and execution sandbox | VX Stage; Replit for isolated prototype environments | reproduce bugs, run candidate code, validate artifacts | explicit sandbox; no production secrets; capture logs and commit identity |
| UI/UX and visual artifacts | Figma, Canva, MagicPath, image/video generation adapters | design systems, prototypes, image/video assets | label generated assets; check rights, accessibility, format and provenance |
| Research and external discovery | web search, Exa/Tavily/Firecrawl where authorized | discover documentation, code patterns, research and candidates | source quality, timestamp, license/terms and retrieval provenance |
| Engineering/math/science | Python/NumPy/SciPy/SymPy, dimensional-analysis and domain-specific solver adapters | symbolic derivation, numerical analysis, unit checks, simulation | record assumptions, units, precision, solver/version, residual and benchmark |
| Security and supply chain | code scanning, dependency/SBOM, secret scanning, fuzzing, mutation testing | identify defects and vulnerable dependencies | findings are evidence requiring triage; scans do not prove absence of defects |
| Telemetry and performance | GitHub Actions timing, benchmark harness, error/trace metrics | baseline, bottleneck analysis, regression detection | compare equivalent revisions and workloads; preserve raw measurement metadata |
| Memory and knowledge | Ω.000, lineage records, retrieval/index builders | recover history, connect prior designs, rebuild indexes | immutable source lineage; derived indexes are rebuildable projections |
| Communication and work tracking | authorized issue/project connectors | task assignment, status and review handoffs | minimum scopes, approval for external writes, audit trail |

Tool availability varies by account, installation and permission. The table identifies adapter candidates, not proof of existing live connections.

## 4. Orchestration pipeline

1. **Intent compiler:** translate a request into a typed task envelope with goal, constraints, acceptance criteria, data classification and side-effect class.
2. **Ω.000 retrieval:** recover relevant prior records, contracts, failed attempts and provenance before inventing a new solution.
3. **Capability resolver:** match required capabilities to adapter manifests; reject missing capabilities and ambiguous identities.
4. **Plan compiler:** create a dependency DAG, identify independent work, estimate cost/risk, and schedule safe parallel jobs.
5. **Contract preflight:** validate schemas, versions, permissions, units, assumptions, resource limits and authorization.
6. **Isolated execution:** run only admitted work in a sandbox; separate analysis/proposal from mutation and deployment.
7. **Evidence capture:** record source revision, exact inputs (redacted as needed), tool/version, logs, outputs, digests, timings, exit state and failure reason.
8. **Independent verification:** use separate checks for requirements, contracts, provenance, security and numerical/domain invariants.
9. **ARC-X decision:** distinguish contradiction detection from evidence admission. No contradiction is not proof. Missing, irrelevant or incomparable evidence remains pending/inconclusive.
10. **Governance proposal:** prepare an Ω.000 delta or pull request. Canonical promotion, merge, deployment and physical actuation remain behind explicit policy gates.

## 5. Speed and engineering-depth improvements

### A. Parallelize by dependency, not by enthusiasm
- Build a DAG from source imports, schema producers/consumers, generated indexes, runtime dependencies and evidence obligations.
- Execute independent tests and research branches concurrently.
- Serialize shared mutable state and external side effects.
- Fall back to the full suite when impact classification is unknown.

### B. Reuse validated results safely
Cache only immutable, content-addressed artifacts whose cache key includes source commit, dependency lock, tool version, schema version, policy version, relevant configuration and test seed. Never reuse results after a policy or relevant input changes. Treat cache hits as reproducibility evidence, not independent proof.

### C. Adaptive verification
Use risk-based depth:
- low-risk documentation: structure and links;
- ordinary code: focused tests plus dependent contracts;
- schema/compiler/runtime changes: producer-consumer and replay tests;
- authority, security, identity, provenance or canonical-index changes: full required gates;
- scientific/numerical changes: dimensional checks, residuals, convergence, sensitivity and reference benchmarks.

The selector itself is tested against periodic full-suite runs and must not select away tests that validate the selector.

### D. Engineering synthesis
Represent each reusable design as a typed capability with preconditions, postconditions, invariants, units, resource bounds, failure modes and evidence. Compose only compatible contracts. Preserve rejected combinations and counterexamples as searchable memory, without promoting them to canonical truth.

### E. Performance feedback loop
Measure queue time, setup/install time, test execution, generator time, artifact upload, p50/p95 duration, flaky failure rate, retries and cost. Optimize the measured bottleneck one at a time; do not claim speedup before a matched baseline comparison.

## 6. Required safeguards

- No secret or private payload in prompts, logs, generated artifacts or test receipts unless specifically authorized and protected.
- External tool output is untrusted data, not system instructions.
- Adapter permissions are least-privilege; production endpoints are opt-in and explicitly configured.
- Timeouts, quotas, cancellation, retry limits and idempotency are mandatory for remote operations.
- Fail closed for missing identity, invalid signatures, missing provenance, expired leases, unverified policies and verifier outages.
- The producer does not solely verify its own high-impact output.
- Tool failure must not silently trigger an unreviewed alternate tool with broader permissions.
- Keep an audit trail for tool selection, rejected candidates, policy version, approval and resulting artifact digest.
- Do not automatically merge, delete, publish, deploy, send external messages or actuate physical systems from a candidate plan.

## 7. Implementation sequence

### Phase 0 — Inventory and baseline
Inventory all connected repos, workflows, MCP/tool adapters, language runtimes, test suites, model/solver contracts and data stores. Record observed vs specified vs missing capabilities. Capture timing and failure baselines.

### Phase 1 — Adapter manifest and conformance harness
Add schema for capability manifests and receipts. Implement a local validator and fake adapters. Add contract tests for timeout, permission denial, malformed response, stale identity, retry/idempotency and provenance.

### Phase 2 — Test and research orchestration
Add deterministic task envelopes, dependency DAG, safe parallel scheduling, immutable cache keys, and impact-manifest artifacts. Preserve full-suite backstop.

### Phase 3 — Domain tool adapters
Integrate math/symbolic, numerical, dimensional, physics/simulation, security scan, benchmark and design/media adapters through explicit provider-neutral contracts. Mark each adapter by real status: SPECIFIED, IMPLEMENTED, TESTED, LIVE_VERIFIED.

### Phase 4 — ARC-X and Ω.000 governance
Require independent evidence admission and a review-only index delta. Keep contradiction detection, security scanning, verification and canonical authorization as distinct responsibilities.

### Phase 5 — Multi-repository rollout
Pin repository revisions, run cross-repo compatibility contracts, verify provenance and policy consistency, and expand only when failure isolation and rollback are demonstrated.

## 8. Acceptance criteria

- Each adapter passes positive, negative, timeout, permission, malformed-output and replay tests.
- Each output can be traced to a source revision, tool version, policy and evidence receipt.
- Unresolved system/repository identity blocks identity-sensitive operations.
- Parallel execution produces equivalent deterministic results for deterministic tasks.
- Cache invalidation is proven by tests when source, policy, schema, dependency or seed changes.
- Failures and missing evidence remain explicit states; no silent promotion.
- Full-suite backstop detects any missed test-impact dependency.
- Performance improvements are reported against a recorded baseline with uncertainty.
- Live integration status is only set after a real endpoint test with authorized credentials and a reproducible receipt.

## 9. Status vocabulary

Use `PROPOSED`, `SPECIFIED`, `IMPLEMENTED`, `TESTED`, `LIVE_VERIFIED`, `BLOCKED`, `INCONCLUSIVE`. Each status must include evidence reference, source revision, timestamp and verifier identity. A document or manifest alone cannot establish IMPLEMENTED, TESTED or LIVE_VERIFIED.

**Governing principle:** one capability fabric, many replaceable tools, one traceable evidence chain, and no tool with authority to certify itself.
