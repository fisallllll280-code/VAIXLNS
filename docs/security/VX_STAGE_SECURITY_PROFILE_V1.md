# VX Stage Security Profile V1

## Boundary

`Identity → Authentication → Authorization → Capability → Execution → Audit`

The VX instance cannot obtain authority from model output, tool availability, memory, or a previous successful execution.

## Required controls

### Identity
Every staged VX instance has a unique identity and registration record.

### Authentication
Requests are authenticated before privileged routing.

### Authorization
Routing requires an explicit capability match and authority scope.

### Isolation
An isolated instance is not eligible for privileged routing.

### Traceability
Requests, route decisions, execution events, isolation, recovery, and evidence references are retained.

### Credential separation
Operational credentials are supplied by the deployment environment and are never embedded in repository source.

## Stage security objectives

- unauthorized route success: zero tolerated;
- isolated-instance route success: zero tolerated;
- invalid request acceptance: zero tolerated;
- execution without provenance: zero tolerated.

## Production hardening

The reference authentication mechanism is a conformance fixture. A production federation should use workload identity, protected channels, short-lived credentials, centralized rotation, and an external trust anchor appropriate to the deployment environment.

## Security evidence

Promotion requires reproducible evidence for the controls above. A passing reference test does not establish production security.
