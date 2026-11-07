# VAIXLNS Ω Research Workspace

This directory is a non-canonical workspace for research records, reproducible comparisons, and decision artifacts. It does not replace `project.genome`, Ω.000, or any source repository.

## How to contribute

1. Copy `templates/research-record.template.json` to a new record file.
2. Assign a stable, unique `record_id`; preserve any source-native identifier.
3. Pin sources and versions; never cite an uninspected source as verified.
4. State the claim type, assumptions, method, baseline, metrics, and limitations.
5. Add executable commands or calculations where applicable.
6. Run `python scripts/validate_research_records.py research/records`.
7. Request independent review before setting `status` to `VERIFIED` or admitting an implementation task.

## State discipline

`PROPOSAL` and `SPECIFIED` are not implementation. `IMPLEMENTED` is not necessarily tested. `VERIFIED` requires evidence references, a recorded result, and an accepted review. Missing information stays missing.

## Directory map

- `records/`: source-backed JSON records; one record per file.
- `templates/`: record template.
- `comparisons/`: baseline/candidate comparison reports.
- `domains/`: domain-specific research protocols.
- `decisions/`: decisions and links to implementation work.

Model-generated text is a research lead, not evidence by itself. Physical claims must distinguish theory, simulation, and measurement; mathematical claims must distinguish proof from numerical support.
