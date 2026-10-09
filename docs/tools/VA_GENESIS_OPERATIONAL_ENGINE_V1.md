# VA Genesis Operational Engine v1

Status: IMPLEMENTED-PROTOTYPE; production readiness NOT VERIFIED.
Owner: VAIXLNS
System boundary: VA inside V, integrated first as an isolated package in the canonical hub.
Authority: project.genome and the existing VAIXLNS governance/verification boundary.
Version: 0.1.0

## Purpose

VA Genesis accepts one natural-language intent and generates a deterministic, dependency-free starter system. It also produces four independent operational copies: development, validation, release, and production. It is a scaffold-and-assurance prototype, not a claim that arbitrary application requirements can be solved perfectly by one message.

## Current implementation

- CLI builder: python -m va.genesis build --intent "..." --name example
- Structural verifier: python -m va.genesis verify --path generated/example
- Local API: python -m va.genesis serve --port 8765
- API health: GET /health
- API generation: POST /generate with JSON fields intent and optional name.
- Default API binding: 127.0.0.1 only. Generation API does not accept filesystem paths from requests.
- Generated service endpoints: /health and /info.
- Generated artifacts: README, service code, system specification, tests, dependency list, Dockerfile, and Compose file.
- Repeated builds use deterministic identifiers and content hashes for identical normalized inputs.

## Operational copies

Every copy includes the same seven project files plus COPY_MANIFEST.json:

- development: LOCAL_DEVELOPMENT
- validation: VALIDATION_REQUIRED
- release: RELEASE_CANDIDATE_PENDING
- production: PROMOTION_BLOCKED

The copy manifests record role, per-file hashes, project hash, source project hash, runtime-test state, and execution authorization. Each copy is created separately; an existing target is never silently overwritten.

## Assurance contract

The verifier checks required files, JSON contracts, Python syntax, per-file SHA-256 digests, the project content hash, the presence of all four copy roles, and equality between each copy and its source project.

Passing this verifier means STRUCTURAL_PASS_RUNTIME_NOT_RUN only. It does not mean the generated service has been launched, integration-tested, security-tested, or approved for production. Runtime smoke tests and production admission remain blocked until their own evidence and an authorized approval are supplied.

The prompt is treated as data in system.json. It is never interpolated into the generated Python source and never evaluated as code. The local generation API only binds to loopback by default, imposes an input-size limit, rejects unknown request fields, and does not permit the caller to select output paths.

## Non-goals / known limits

- No external LLM/provider is wired in this prototype.
- No arbitrary project-specific business logic, frontend, database schema, secrets, or cloud infrastructure is generated yet.
- The local HTTP service is not intended to be exposed to the public internet.
- Docker/Compose availability and actual container execution have not been asserted by static verification.
- The production copy is an isolated candidate directory, not an authorized production deployment.

## Next hard gates

1. Execute generated unit tests inside an isolated runner.
2. Start the generated service and record HTTP smoke-test evidence.
3. Add dependency, secret, license, and container security scans.
4. Connect a provider-backed design/implementation agent behind a typed contract.
5. Route generated claims through ARC-X evidence separation and VV proof validation.
6. Permit release only via a distinct authorization gate; never let VA authorize itself.
