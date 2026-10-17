# VAIXLNS Federated Engineering Deployment V1

**Status:** executable reference planner + regression tests; live deployment is not established.  
**Authority:** VAIXLNS  
**Runtime mutation:** disabled  
**Automatic production deployment:** disabled

## Objective

Connect the current four-system federation manifest to one reviewable engineering release path without replacing canonical identity or pretending that registered repositories are live services. The first slice produces a deterministic rollout plan and chooses eligible workers by estimated completion latency after hard capability, identity, authority, health, and data-classification gates.

## Federation targets

| System | Repository surface | Current planner treatment |
|---|---|---|
| VAIXLNS | `fisallllll280-code/VAIXLNS` | Eligible for sandbox planning |
| VX | `VX-runtime`, `VX50_COMPLETE_BUILD` | Eligible for sandbox planning after VAIXLNS |
| VLNS | Candidate mapping to `NAXLNS` | HOLD until system/repository identity is verified |
| NEXNET | Candidate mapping to `NEXENT` | HOLD until system/repository identity is verified |

The two candidate mappings remain held; their names are not silently equated. A repository or CI workflow is not evidence of a deployed runtime.

## Governed engineering release path

1. Pin an immutable source commit SHA per repository.
2. Resolve dependencies and verify contracts.
3. Build and run unit/conformance tests.
4. Start in an isolated sandbox and collect startup/health evidence.
5. Run integration smoke tests across approved adapters.
6. Verify independently and retain logs, hashes, traces, and rollback material.
7. Request a separate governance admission.
8. Promote or hold; this planner never promotes or executes.

The system dependency graph creates rollout waves. Targets in the same wave may be proposed for bounded parallel work up to the configured limit. A dependency must be planned before its dependants; unresolved identity keeps a target on HOLD.

## Reducing waiting time without bypassing safety

Worker routing first excludes unhealthy, unverified, capability-mismatched, unauthorized, or data-incompatible workers. Only then does it rank candidates using estimated completion latency:

`queue depth × queue wait + p95 service time + network transfer penalty + cold-start cost − verified-cache savings`

Ties are deterministic. The FAST_PATH label is limited to low-risk, read-only, idempotent tasks with no side effects. Deployment, repository writes, production changes, and irreversible actions remain on the controlled path and require a separate executor and authorization.

Use bounded parallelism, dependency-aware waves, cache only immutable results, and retain verification evidence. This is a scheduling policy to test, not a measured claim that VAIXLNS is already faster.

## Validation and boundaries

GitHub Actions validates the manifest, compiles the Python module, runs regression tests, emits a sandbox plan, and asserts that production stays blocked. The produced plan is an artifact for review.

Not established by this change: a running multi-system cluster, bound ingress/API gateway/event bus/database/secrets/telemetry infrastructure, live model providers, cross-repository deployment credentials, production rollout, or end-to-end deployment success. Those require configured infrastructure and fresh runtime evidence.
