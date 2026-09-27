# VAIXLNS — Integrated Operation Sources v1

This is the wiring map for connecting project outputs to operating sources.

## A. Historical material

INPUTS:
- uploaded project files
- recovered archives
- prior specifications
- diagrams
- terminology
- innovation records

OUTPUT:
- recovery evidence packet
- Atomic System Record
- source lineage

OWNER:
VAIXLNS recovery/registry layer

## B. Discovery and synthesis

INPUT:
canonical/recovered knowledge + external repository candidates

ENGINE:
NEXENT

OUTPUT:
candidate architecture, dependency candidates, implementation proposals

GATE:
never canonicalize a proposal without evidence.

## C. Canonical architecture

ENGINE:
VAIXLNS

OUTPUT:
system graph, subsystem ownership, contracts, invariants, authority boundaries, repository federation map

## D. Execution

PRIMARY:
VAIXLNS-unified

SELECTIVE SOURCES:
vaixlns-core
VX-runtime
VAIXLNS-Intent-to-Reality
vaixlns-csd-kernel

RULE:
selective import only; source repositories retain lineage until target verification succeeds.

## E. Simulation

INPUT:
operation specification + fixtures + expected state

OUTPUT:
simulation run + observed state + diff + evidence

## F. Runtime

INPUT:
verified execution plan

OUTPUT:
RUN_ID + state + events + logs + artifacts + metrics

## G. Verification

CHECK:
contracts
schemas
invariants
unit tests
integration tests
replay
recovery

OUTPUT:
verification result + evidence

## H. Evolution

INPUT:
verified runtime evidence + NEXENT proposals

OUTPUT:
new proposal → simulation → implementation → verification → canonical promotion

## Repository adoption

EXTERNAL → DISCOVERED → REVIEWED → COMPATIBLE → ADAPTER/DEPENDENCY → SELECTIVE IMPORT → VERIFIED

No external repository enters the canonical trust boundary solely because it is popular, similar, or highly starred.
