# Provider Adapter Contract v1

**Status:** SPECIFIED
**Authority:** project.genome::v1.0.0
**Owner:** VLNS/VX

## 1. Principle
A provider is an implementation detail. The Arena speaks a provider-independent capability contract.

MODEL ≠ PROVIDER ≠ ADAPTER ≠ CAPABILITY ≠ AUTHORITY

## 2. Adapter responsibilities
An adapter MUST:
1. expose provider identity and adapter version;
2. declare supported capabilities;
3. normalize request/response envelopes;
4. enforce timeout, token, tool, and permission boundaries;
5. emit deterministic metadata required for replay where available;
6. emit structured errors without hiding provider failure;
7. preserve provenance for every invocation;
8. support health/conformance checks;
9. refuse operations outside its declared contract;
10. never mutate Arena scoring or governance state.

## 3. Canonical interface
discover() → ProviderDescriptor
capabilities() → CapabilitySet
conform(contract) → ConformanceReport
invoke(request) → ProviderResponse
stream(request) → ProviderEvent*
health() → HealthReport
cancel(invocation_id) → CancellationReport
fingerprint() → AdapterFingerprint

Concrete programming language/API remains an implementation decision until verified.

## 4. Provider descriptor
Required fields: provider_id; provider_name; adapter_id; adapter_version; model_id/model_family; capability_ids; supported_modalities; tool_support; context_limits; rate/usage constraints; security classification; provenance source; timestamp.

## 5. Normalized invocation
InvocationRequest contains invocation_id, arena_id, task_id, capability_contract, input payload reference, allowed tools, resource limits, timeout, policy version, and parent event id.

ProviderResponse contains invocation_id, status, output/artifact references, usage metadata, provider metadata, error classification, and evidence references.

## 6. Conformance gates
ADAPTER_READY requires schema conformance, identity/provenance conformance, permission isolation, timeout/cancellation behavior, error normalization, replay metadata, artifact integrity, and no unauthorized side effects.

Failure blocks Arena admission for that adapter.

## 7. Provider neutrality
Initial adapters may include OpenAI, Claude/Claude Code, Gemini, Grok, Mistral, Atomkit engineering services, and future providers. Inclusion is not an endorsement and does not imply VERIFIED integration.