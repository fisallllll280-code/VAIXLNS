# VAIXLNS Pattern v1

Status: IMPLEMENTED — NOT YET VERIFIED IN CI.

This is the implementation boundary for the Pattern concept.

Invariants:
1. The private language belongs to the Pattern Genome/container, not VX core.
2. Every language has exactly four directions: semantic, structural, operational, evolutionary.
3. Missing private context never causes a null dereference.
4. Replay state is optional and defaults to an empty mapping.
5. Missing language binding is a security rejection, never an auto-repair opportunity.
6. The repository never stores the private language source or raw personal identifiers.
7. Route diagnosis distinguishes reference deficiency, invariant breach, and security rejection.

Expansion: N architecture candidates produce exactly N x 4 logical routes per language.
This is a search-space count, not an execution-speed claim.

VERIFIED requires a reproducible test run covering the guards, four-direction
invariant, binding verification, and quarantine diagnosis.
