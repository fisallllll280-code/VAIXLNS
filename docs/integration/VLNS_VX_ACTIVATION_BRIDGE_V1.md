# VLNS to VX Governed Model Activation Bridge v1

**Canonical owner:** VAIXLNS  
**Semantic/model activation:** VLNS  
**Execution, verification, and evidence:** VX  
**Repository implementation:** VAIXLNS-unified  
**Canonical contract state:** SPECIFIED; runtime adoption remains evidence-gated.

## 1. System boundary

The systems remain federated and independently attributable.

VAIXLNS canonical policy
→ VLNS model activation gate
→ signed provider-neutral activation envelope
→ VLNS activation endpoint
→ receipt bound to activation_id and envelope_hash
→ VX validates receipt and emits an evidence event
→ independent conformance, replay, and admission.

VLNS provides model participation. It does not become canonical authority, choose its own permission policy, or bypass VX execution controls. VX remains responsible for capability routing, tool calls, verification, replay, and runtime admission.

## 2. Envelope

The canonical schema is schemas/vlns-activation-envelope.schema.json. The envelope binds model_id, provider, model_version, role, capability_profile, context_hash, tool_profile, permission_profile, constraints, provenance, activation_id, status, signature_algorithm, and signature.

The context itself is not included in the envelope: only the hash of its canonical JSON representation is carried. Every activation must retain an auditable relationship between task identity, source identity, source digest, envelope hash, remote receipt, and the resulting evidence event.

## 3. Authority invariants

- Model identity does not imply capability.
- Capability does not imply authority.
- A remote server being reachable does not imply that it is trusted.
- Default role permissions are read and propose.
- canonical_write, governance_override, unrestricted_network, and external_action are non-delegable at the model-activation layer.
- execute or modify permissions, even if explicitly granted by a trusted role policy, remain subject to VX capability, proof, policy, and admission gates.
- Unknown capabilities, tools, providers, roles, signatures, or receipt identities fail closed.
- No remote activation is considered fully complete until its evidence event is acknowledged.
- A failed evidence write after remote activation produces ACTIVATED_EVIDENCE_PENDING, not VERIFIED or ADMITTED.

## 4. Remote receipt contract

The runtime implementation posts the signed envelope to the configured activation path, defaulting to /v1/activations. The remote server must return a JSON object containing:

    {
      "status": "ACTIVATED",
      "activation_id": "the exact activation_id supplied in the request",
      "envelope_hash": "SHA-256 of the exact signed request envelope"
    }

The implementation rejects non-ACTIVATED states, missing values, and identifier or digest mismatch. Following receipt validation, it emits VLNS_MODEL_ACTIVATION_CONFIRMED to /events and requires acknowledgement to report ACTIVATED_AND_RECORDED.

This is a defined integration protocol; it is not evidence that the separately hosted VLNS service already implements the protocol.

## 5. Evidence states

- SPECIFIED: the canonical contract and schema exist.
- IMPLEMENTED: code implements the local validation and remote client path.
- TESTED: repository CI runs deterministic, policy, tamper, mismatch, rejection, and failure-path tests.
- CONNECTED: a configured, authenticated VLNS endpoint responds.
- VERIFIED: identity, endpoint, sandbox, execution, recovery, replay, and independent conformance evidence are attached.
- ADMITTED: explicit VAIXLNS authority allows the exact integration identity, contract, capabilities, dependency fingerprint, and environment fingerprint.
- RUNNING: the admitted integration is being monitored under the required operational policy.

These states are not interchangeable. A local fake-client test does not establish a remote connection.

## 6. Implementation trace

Reference implementation resides in VAIXLNS-unified:
- vlns/activation.py
- infra/vlns_server_client.py
- scripts/vlns_activation_bridge.py
- schemas/vlns-activation-envelope.schema.json
- tests/test_vlns_activation_bridge.py
- docs/integration/VLNS_VX_ACTIVATION_BRIDGE_V1.md

The implementation branch is a review candidate until the feature branch CI is green and its pull request is admitted. The canonical status must remain SPECIFIED / PARTIAL while the live endpoint and repository identity mapping remain unverified.

## 7. Connection prerequisites

Remote connectivity uses environment-only configuration:

    VLNS_SERVER_ENABLED=true
    VLNS_SERVER_URL=https://<configured-vlns-host>
    VLNS_SERVER_TOKEN=<secret-from-secret-manager>
    VLNS_SERVER_HEALTH_PATH=/health
    VLNS_SERVER_ACTIVATION_PATH=/v1/activations
    VLNS_SERVER_TIMEOUT=5
    VLNS_ACTIVATION_SIGNING_KEY=<separate-secret-of-at-least-32-bytes>
    VLNS_ALLOWED_PROVIDERS=ollama,openai-compatible
    VLNS_ALLOWED_CAPABILITIES=reasoning,research,engineering,verification
    VLNS_ALLOWED_TOOLS=repository.read,web.search

No secret belongs in Git. The actual deployment endpoint must be obtained from a trusted operator or deployment configuration; the implementation must not invent or scan for private endpoints.

## 8. Mandatory admission checklist

DISCOVER → QUARANTINE → IDENTITY + CONTRACT → SANDBOX → FUNCTIONAL TEST → FAILURE / RECOVERY → REPLAY → INDEPENDENT VERIFICATION → PROOF FRESHNESS → CAUSAL IMPACT BUDGET → EXPLICIT AUTHORITY → ADMISSION → RUNTIME → CONTINUOUS REVALIDATION.

The live connection and any mapping between the VLNS system and the NAXLNS repository remain UNVERIFIED until direct evidence closes these gates.
