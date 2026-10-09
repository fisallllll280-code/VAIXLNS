# VAIXLNS Autonomous Research and System Foundry V1

**State:** Executable reference workflow proposed for review  
**Canonical home:** VAIXLNS  
**Processor:** scripts/autonomous_research_foundry.py  
**Queue:** registry/research/autonomous-foundry-queue.v1.json

## Objective

Connect the existing VAIXLNS agent roster and Ω-Pattern Foundry to a bounded processor that repeatedly inspects registered project evidence, inventories explicitly approved public repositories, and emits architecture candidates with source hashes, structural attack findings, and a review handoff.

This fills an operational gap between a research specification and an automatically generated, inspectable work product. It does not claim that a model-backed global research service is already configured.

## Execution cycle

1. Load and validate the versioned queue.
2. Read only the explicitly listed local source files; hash each readable file and count selected lifecycle signals.
3. Optionally fetch public GitHub repository tree metadata from the fixed HTTPS GitHub API host, for repositories listed in the queue allow-list.
4. Validate the registered agent handoff chain.
5. Rank bounded tasks deterministically using queue priority plus observed local lifecycle signals.
6. Generate candidate patterns through the existing reference backend in Ω-Pattern Foundry.
7. Attach source references, recalculate the candidate genome digest, run validation and adversarial checks, and emit the full report.
8. Upload the report as a workflow artifact. A human or separately authorized controller decides whether any candidate advances.

## Processor limits

- Maximum eight tasks per cycle, further constrained by the queue.
- Maximum 96 local source files; maximum 512,000 bytes per file and 3,000,000 bytes across local inputs.
- Maximum eight approved public repository trees, with at most three concurrent requests.
- Five-second request timeout for each public repository.
- Public tree responses are capped at six megabytes.
- Public-source failure is explicitly recorded; it is never reported as a successful search.
- No unbounded retry loop is used.

## Authority and safety boundaries

- Local files are read as data. They are not imported, evaluated, or executed by the research processor.
- Public source code blobs are not downloaded or executed. Public mode inventories path names and blob identifiers only.
- Candidate patterns remain in status PROPOSAL.
- Novelty state remains UNASSESSED.
- Admission state remains NOT_AUTHORIZED.
- The foundry gate is a structural candidate check, not canonical admission, scientific proof, or production approval.
- The workflow has only repository read permission and uploads a report artifact; it does not commit files, create pull requests, merge, deploy, spend money, or mutate a live runtime.
- The current generator is the deterministic reference backend. A live language-model backend and full-text scholarly/source adapters must be connected, separately permissioned, tested, rate-limited, and represented in provenance before any claim of deep external research is made.

## Relationship to engineering fast-feedback

The existing engineering test router remains the authority for impact routing. Unknown and cross-cutting changes fall back to the full unittest suite. This change does not replace that router or waive repository-required CI, integration, security, or release gates.

## Commands

Repository-local cycle:

    python scripts/autonomous_research_foundry.py --local-only

Cycle with approved public repository inventory:

    python scripts/autonomous_research_foundry.py --public-sources

## Acceptance gates

- Queue schema and IDs are valid and unique.
- Local paths cannot escape the repository root.
- Public source targets are fixed to the GitHub API host and validated repository/ref values.
- Candidate provenance contains only explicitly mapped task sources.
- The agent handoff chain is reported.
- Candidate integrity and adversarial checks are attached.
- Unknown source coverage and novelty limitations remain explicit.
- Tests pass before the scheduled automation is considered operational.
- No candidate is promoted or deployed by the research workflow.
