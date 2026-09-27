# VAIXLNS — Vision-Language-Action Integration Contract

Status: PROPOSAL -> SPECIFIED
Canonical target: VX
Upstream reference: OpenVLA 7B (openvla/openvla-7b)
Purpose: define a governed adapter boundary for vision-language-action models without making the external model the canonical runtime.

## 1. Architectural position

OpenVLA is a model that maps language + camera observation to normalized robot actions. VAIXLNS treats this as an external intelligence/policy provider, not as the system of record.

```text
VV Observation / Intent
        |
        v
XV Intelligence Gateway
        |
        v
VLA Adapter Contract
        |
        +--> OpenVLA / other VLA provider
        |
        v
VX Policy Normalizer
        |
        +--> Simulation
        |       |
        |       v
        |   Verification / Safety
        |
        v
VX Execution Fabric
        |
        v
Robot / Device / Digital Twin
```

## 2. Canonical contract

Input:
- intent_id
- natural-language task
- observation reference (image/frame sequence)
- embodiment_id
- environment_id
- policy constraints
- authorization context
- provenance references

Provider output MUST be treated as untrusted proposal data:
- action vector/chunk
- provider model id + revision
- normalization metadata
- confidence/uncertainty if supplied
- provider timestamp
- raw input/output hashes

VX MUST NOT execute provider output directly.

## 3. Mandatory VX gates

1. Schema validation.
2. Provenance verification.
3. Embodiment compatibility check.
4. Action-space normalization.
5. Constraint/policy evaluation.
6. Simulation or digital-twin validation when available.
7. Safety envelope check.
8. Deterministic event recording.
9. Authorization check.
10. Execution.
11. Post-action observation and evidence capture.

A failed gate produces a non-executable proposal and an auditable reason.

## 4. Action model

The adapter supports generic action spaces rather than hard-coding a single robot:

```text
Action =
  { space,
    dimensions,
    values,
    units,
    normalization,
    temporal_horizon,
    embodiment_id }
```

A 7-DoF end-effector action such as
`(x,y,z,roll,pitch,yaw,gripper)`
is therefore one provider-specific representation, not the VAIXLNS canonical action model.

## 5. Critical compatibility rule

A model's documented limitation remains part of the adapter contract. OpenVLA's model card states that zero-shot generalization to unseen robot embodiments or setups is out of scope; such cases require demonstrations/fine-tuning. VAIXLNS therefore records compatibility as an explicit capability, never infers it from model existence.

## 6. Provenance

Every provider invocation SHOULD emit:

- invocation_id
- parent_intent_id
- provider
- model
- revision
- input_hash
- output_hash
- dataset/domain declaration
- embodiment_id
- environment_id
- policy_version
- gate_results
- execution_status
- evidence_refs

## 7. Determinism and replay

VX records canonicalized request, provider metadata, proposed action, gate decisions, and execution evidence. Replay MUST distinguish:

- exact replay of a recorded provider result;
- re-inference by the provider;
- simulation replay;
- physical execution.

These are different event classes and must never be conflated.

## 8. Provider federation

The same contract can wrap OpenVLA, other VLA models, classical controllers, remote policies, simulators, or future providers. Provider-specific code belongs behind the adapter boundary.

## 9. Security

Remote model code, weights, preprocessing, and outputs are untrusted inputs. The adapter MUST support:
- sandboxed provider execution;
- artifact/model revision pinning;
- checksum verification;
- capability allowlists;
- action bounds;
- environment/robot allowlists;
- credential isolation;
- audit logging.

## 10. Acceptance criteria

The integration is VERIFIED only when repository evidence demonstrates:
- adapter schema;
- provider implementation;
- unit tests;
- deterministic serialization/hash tests;
- simulation gate;
- rejection-path tests;
- provenance records;
- documented execution boundary.

Until then this document remains SPECIFIED, not VERIFIED.

## 11. Non-goals

This contract does not claim:
- that VAIXLNS contains OpenVLA weights;
- that VAIXLNS can control a physical robot without hardware integration;
- that provider accuracy equals execution safety;
- that an external model becomes part of the VAIXLNS constitutional core.

## 12. Reference

OpenVLA 7B is documented as a vision-language-action model trained on 970K robot manipulation episodes and producing normalized robot actions; its public repository provides inference, fine-tuning, and evaluation tooling. See the upstream model card and repository for provider-specific details.
