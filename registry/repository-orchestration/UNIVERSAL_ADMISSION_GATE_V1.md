# VAIXLNS Universal Admission & Performance Gate v1

## Purpose

Every system, repository, innovation, runtime, tool and generated artifact enters the VAIXLNS federation through the same evidence gate. Being named in an index is not admission.

## Admission states

~~~text
DISCOVERED
  ↓
IDENTIFIED
  ↓
CONTRACTED
  ↓
BUILDABLE
  ↓
EXECUTABLE
  ↓
TESTED
  ↓
VERIFIED
  ↓
ADMITTED
  ↓
OPERATED
  ↓
EVOLVING
~~~

Failure moves the candidate to `BLOCKED`, `QUARANTINED` or `RECOVERY`; it does not silently pass.

## Mandatory gates

| Gate | Requirement | Evidence |
|---|---|---|
| G0 Identity | stable system/repository identity and owner boundary | manifest |
| G1 Contract | inputs, outputs, dependencies, lifecycle and authority declared | contract |
| G2 Source | executable or explicitly specification-only | source/spec evidence |
| G3 Build | reproducible dependency resolution/build | build log |
| G4 Execution | real entrypoint can execute | execution log |
| G5 Test | deterministic tests exist where executable | test report |
| G6 Conformance | canonical contract and interfaces satisfied | conformance report |
| G7 Security | secrets, permissions and boundaries checked | security evidence |
| G8 Performance | latency, throughput, resource use or declared non-runtime metric | benchmark/evidence |
| G9 Provenance | lineage to canonical system/innovation/index | lineage record |
| G10 Recovery | failure/recovery behavior is defined | recovery evidence |
| G11 Evidence | all claims point to reproducible evidence | evidence manifest |

**Admission rule:** every mandatory gate must be `PASS` or explicitly `NOT_APPLICABLE` with justification. Otherwise state is not `ADMITTED`.

## Performance is continuous

Admission is not a one-time certificate. After admission, the system enters a continuous performance loop:

~~~text
MEASURE → BASELINE → CHANGE → TEST → COMPARE → REGRESSION CHECK → EVIDENCE → ADAPT
~~~

Performance regressions, broken contracts, missing evidence or security failures can automatically demote a system from `ADMITTED` to `DEGRADED`, `BLOCKED` or `RECOVERY`.

## Innovation gate

An innovation can enter the official system graph only when:

1. canonical duplication check passes;
2. its capability boundary is explicit;
3. a prototype or formal specification exists;
4. its intended effect is testable;
5. evidence is captured;
6. lineage is recorded;
7. adoption does not overwrite an existing canonical capability.

## Repository gate

A repository is admitted only after its contract, build/test surface, CI/conformance workflow and evidence path are present. A README alone can never satisfy admission.

## Universal machine-readable verdict

Each candidate emits:

~~~json
{
  "identity": "PASS|FAIL",
  "contract": "PASS|FAIL",
  "source": "PASS|FAIL|N/A",
  "build": "PASS|FAIL|N/A",
  "execution": "PASS|FAIL|N/A",
  "tests": "PASS|FAIL|N/A",
  "conformance": "PASS|FAIL",
  "security": "PASS|FAIL|N/A",
  "performance": "PASS|FAIL|N/A",
  "provenance": "PASS|FAIL",
  "recovery": "PASS|FAIL|N/A",
  "evidence": "PASS|FAIL",
  "admission": "BLOCKED|ADMITTED"
}
~~~

## Core principle

**The system earns entry through evidence; the index never grants entry by itself.**