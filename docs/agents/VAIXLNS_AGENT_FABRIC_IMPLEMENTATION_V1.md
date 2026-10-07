# VAIXLNS Agent Fabric V1

State: IMPLEMENTED — CI VERIFIED FOR THE TESTED IMPLEMENTATION CONTENT.

The executable Agent Fabric connects agent registry, authority policy, Pattern routing, private language binding, Mind Federation, signed handoffs, paper economics, events, and independent proof.

INTENT
  -> AGENT REGISTRY
  -> AUTHORITY / POLICY
  -> PATTERN SELECTION
  -> PRIVATE LANGUAGE BINDING
  -> 4 DIRECTIONS
  -> MIND EXCHANGE
  -> SIGNED HANDOFF
  -> SIMULATION
  -> PAPER WALLET AUTHORIZATION / SETTLEMENT
  -> EVENTS
  -> INDEPENDENT PROOF
  -> HOLD / GOVERNANCE

## Agents

AG-001 through AG-013 are registered as specialized roles spanning recovery, identity, capability analysis, architecture, research, contradiction audit, innovation synthesis, architecture forging, security, verification, runtime integration, recovery operations, and meta-evolution governance.

The registry is capability-driven; no anonymous agent is admitted.

## Pattern coupling

An agent task cannot use the Pattern route generator without a language binding fingerprint. The private language source stays outside the repository and outside agent evidence.

Each language expands only into the four canonical directions:
semantic, structural, operational, evolutionary.

## Mind Federation

Each core agent has a logical mind identity. The default handoff chain establishes directed connections between specialized minds.

Mind Exchange carries:
intent, requested capability, assumptions, risk, evidence references, requested action, and authority scope.

The exchange stores a deterministic state hash. The implementation never requires a model provider or exposes a private language secret. Provider/model identity remains a replaceable execution detail.

## Handoff coupling

A handoff includes source agent, target agent, task, capabilities, artifacts, evidence, constraints, authority scope, expiry, and an HMAC signature.

Targets are constrained by the source agent's declared handoff targets.

## Economic coupling

AgentEconomicWallet is a paper-only execution layer. Authorization reserves budget. Settlement charges actual usage up to the reservation and reports the unused amount as a refund. Settlement produces balanced debit/credit entries and a ledger hash.

No real funds are moved.

## Verification

AgentVerifier independently checks:
- exact four-direction invariant;
- binding presence;
- HMAC-valid handoff;
- event hashes;
- mind-exchange state hash;
- paper-wallet real-value guard.

A successful internal proof is evidence about the tested simulation path. It is not production authorization.

## CI evidence

- Agent Fabric Conformance run 37568977836: SUCCESS.
- Pattern Conformance run 37568977919: SUCCESS.
- VAIXLNS Conformance run 37568977845: SUCCESS.

The later Mind Federation additions are covered by the deterministic test suite and must be rechecked on their current head before any production-oriented admission.

## State discipline

PROPOSED is not IMPLEMENTED.
IMPLEMENTED is not VERIFIED in the global production sense.
A simulation may receive verification_state=VERIFIED only after deterministic proof checks pass.
The overall dispatch disposition remains HOLD until an external governance/admission decision exists.

## Non-loss rules

No agent may delete historical records, self-grant authority, bypass security rejection, convert speculative output into canonical truth, or expose private language source material.
