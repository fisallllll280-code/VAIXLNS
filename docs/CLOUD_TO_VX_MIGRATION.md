# Cloud / Claude-to-VX Migration Contract

The requested "Claude/cloud repository" is not present under the connected account under the exact name claude-fable-5. Public GitHub search returns unrelated repositories, so they are not imported automatically.

## Canonical migration

Cloud implementation
  -> snapshot/reference
  -> capability extraction
  -> dependency mapping
  -> VX contract
  -> adapter
  -> deterministic execution boundary
  -> evidence
  -> replay
  -> operational assurance

## Required adapter surface

- identity
- model/provider metadata
- tools
- input/output schemas
- network boundaries
- filesystem boundaries
- secrets boundary
- rate/latency limits
- policy hooks
- event emission
- evidence capture
- replay strategy
- failure/recovery behavior

## Rule

VX is the execution authority. A cloud model may provide intelligence, planning, generation or interpretation, but model output is a proposal until it passes capability, policy, authorization, execution and evidence gates.

## No false universality

"Works with any system" means the VX contract is system-neutral and extensible. Actual interoperability requires a verified adapter for each protocol/platform/device family.
