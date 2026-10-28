# VX Governed Error Routing — Reference Contract

Status: IMPLEMENTATION CANDIDATE — NOT PRODUCTION VERIFIED

## Intent

Provide a deterministic, testable reference for registering VX-family specialists,
discovering agents by declared capability, and routing structured error signals.
Unknown errors remain unassigned and deployment-blocked rather than being silently
discarded or routed to an invented owner.

## Required flow

1. A system emits a minimal error envelope: ID, source system, type, severity, and evidence references. Secrets and sensitive payloads must not be copied into the envelope.
2. VX classifies the error using a deterministic taxonomy.
3. VX routes only to a registered specialist whose state is routable and whose declared authority includes diagnosis.
4. Critical/SEV0/SEV1 errors block promotion and recommend isolation.
5. Missing eligible specialists produce UNASSIGNED and block deployment.
6. The specialist proposes a repair in an isolated environment. Repair does not close the incident.
7. Independent tests and VX review are required before closure or promotion.

## Safety boundaries

- This reference module does not download, install, merge, deploy, transfer money, or remediate incidents automatically.
- This file does not claim a live connection to external models or MCP servers.
- Registration data is not proof of agent identity; production requires authenticated workload identity, authorization checks, immutable audit events, replay protection, and secret-safe observability.
- Do not change protected canonical sources such as project.genome or Ω.000.
- No production promotion without explicit approval and enforced repository/runtime gates.

## Error capability mapping

| Error family | Capability |
|---|---|
| security, auth, permission | security-review |
| test, verification | verification |
| build, compile, code | coding |
| integration, connection, API, MCP | integration |
| data, index, registry | data-integrity |
| timeout, performance, resource | observability |
| unknown | diagnosis; remain blocked if no eligible owner exists |

The taxonomy is a starting point and must be reviewed against existing registry data before broad rollout. A real deployment must map capability names to actual registered VX agents and verify the mapping with integration tests.

## Verification

Run from the repository root:

    python -m unittest tests.test_vx_federation_gate -v
    python scripts/vx_federation_gate.py simulation

Passing these unit tests would validate only the reference module, not production connectivity, security posture, or organization-wide deployment enforcement.
