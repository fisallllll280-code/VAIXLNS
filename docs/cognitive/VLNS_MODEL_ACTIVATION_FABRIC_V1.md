# VLNS — Model Activation & Intelligence Fabric v1

**Status:** PROPOSED / SPECIFIED BOUNDARY
**Authority:** project.genome::v1.0.0
**Owner:** VAIXLNS federation
**Role:** Governed semantic/model activation layer feeding VX

## 1. Intent

VLNS is the innovation boundary through which model intelligence is discovered, selected, prepared, activated, and delivered into VX under a capability contract.

VLNS does not become the authority over VX. VAIXLNS remains the canonical authority and VX remains the governed execution boundary.

## 2. Model lifecycle

MODEL DISCOVERY
→ MODEL IDENTITY
→ CAPABILITY PROFILE
→ ROLE/MIND ENVELOPE
→ POLICY CHECK
→ CONTEXT ASSEMBLY
→ ACTIVATION
→ VX SESSION
→ EVIDENCE
→ PERFORMANCE UPDATE

## 3. Activation contract

VLNS must provide VX with a provider-neutral activation envelope containing:

model_id
provider
model_version
role
capability_profile
context_hash
tool_profile
permission_profile
constraints
provenance
activation_id

The envelope must be deterministic enough to reconstruct what participated in an evaluation.

## 4. Role envelope

A model does not receive authority merely because it is connected.

Example roles:
- reasoning_mind
- architecture_mind
- adversary_mind
- verifier_mind
- recovery_mind
- security_mind
- innovation_mind

Each role has explicit read/propose/execute/modify/external-action permissions.

## 5. Boundary

VLNS → activation contract → VX.

VX decides orchestration, experiment design, execution, verification, admission, and capability promotion.

VLNS supplies model participation and semantic/context activation; it does not self-authorize execution.

## 6. Arena participation

Ω-ARENA participants are admitted through VLNS activation profiles. OpenAI, Gemini, Claude, Claude Code, and future providers use adapters rather than provider-specific logic in the Arena core.

## 7. Evidence

Every activation must be traceable to:
activation_id → model identity/version → role → context → task → outputs → execution → evidence events.

## 8. Identity caution

Historical repository evidence currently does not conclusively prove VLNS ↔ NAXLNS identity. Therefore this role is recorded as a governed architectural target, not as a VERIFIED repository identity. Identity promotion requires explicit evidence.

## 9. Security

Default permissions are deny-by-default. Model activation cannot grant:
- canonical writes;
- unrestricted network access;
- uncontrolled external actions;
- governance override;
- automatic capability adoption.

