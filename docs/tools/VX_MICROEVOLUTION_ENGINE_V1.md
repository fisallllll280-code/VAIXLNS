# VX MicroEvolution Engine Ω v1

**Status:** IMPLEMENTED REFERENCE SCANNER / READ-ONLY / NOT A SELF-MODIFYING AGENT  
**Version:** 0.1.0  
**Owner boundary:** VAIXLNS canonical engineering and evidence plane

## Purpose

Find small, evidence-linked engineering opportunities and preserve a repeatable baseline for future review. The first version is deliberately a deterministic repository inventory plus heuristic candidate generator. It does not claim to predict specific events five years ahead.

## Existing architecture fit

This is a narrow evidence-collection companion to the ARC-X Bounded Adaptive Evolution Planner and the repository perpetual-engine design. It does not replace either, does not write to canonical registries, and does not authorize mutations. Candidate records remain proposals until a separate engineering workflow validates the source and tests the proposed change.

## Run

From the repository root:

```bash
python scripts/vx_microevolution_engine.py --root . --horizon-years 5 --output build/microevolution/report.json
# On the next run, compare against a previously saved report:
python scripts/vx_microevolution_engine.py --root . --horizon-years 5 --baseline build/microevolution/previous-report.json --output build/microevolution/current-report.json
python -m unittest tests.test_vx_microevolution_engine -v
```

The scanner uses only the Python standard library. The report contains:
- repository-relative inventory of selected text/source/configuration files;
- SHA-256 for each scanned file and the Git revision when available;
- counts for source, tests, documentation and manifests;
- bounded, explainable candidate records with evidence pointers, effort, impact, confidence and planning horizon;
- optional longitudinal comparison of added, removed and hash-changed paths against a prior report;
- explicit safety limits and the distinction between heuristic proposal and verified finding.

## Candidate heuristics

- **MX-TEST-001:** source detected but no test-role files detected;
- **MX-TODO-001:** unfinished-work markers exist and require manual triage;
- **MX-DEP-001:** dependency manifests exist; a separate version/support/lockfile audit is needed;
- **MX-TRACE-001:** source and documentation coexist; trace one documented claim to an executable test and evidence;
- **MX-COMPAT-001:** establish interface compatibility fixtures for long-lived contracts.

These are prompts for investigation, not assertions that a defect exists. The scanner does not parse every language semantically, query vulnerability databases, or run tests.

## Safety and evidence contract

- Read-only: does not modify source files or install dependencies.
- No network calls and no execution of repository code.
- Skips common secret filenames, hidden directories, build caches, symlinks and oversized files.
- Reports hashes and repository revision to help reproduce the inventory.
- Never auto-approves, merges, deploys, or promotes a proposal.
- Inventory exclusions and heuristic blind spots mean the report is not a complete security audit.

## Five-year operating model

Run periodically and retain immutable reports keyed by commit SHA. Pass a prior report with `--baseline` to detect added, removed and hash-changed files. Compare reports over time to detect drift, dependency policy gaps, untested interfaces and repeated unfinished-work patterns. The included CI artifact is retained for 90 days; a five-year record requires an explicitly managed archive or repository artifact policy. Any proposed patch must be isolated, tested against a baseline, reviewed for compatibility and security, and explicitly approved before merge.

## Status vocabulary

- **IMPLEMENTED:** the scanner code exists in the repository.
- **TESTED:** the dedicated unit suite passes in an identified environment.
- **RUNTIME VERIFIED:** reserved for evidence of actual command execution, not static code review.
- **PRODUCTION:** not claimed by this reference tool.

 
## Deep idea portfolio extension

The companion [Deep Innovation Portfolio](VX_MICROEVOLUTION_DEEP_IDEAS_V1.md) adds 18 testable hypotheses and a deterministic portfolio evaluator. It complements this scanner and does not replace ARC-X's bounded-evolution gate. Run:

```bash
python scripts/vx_microevolution_ideas.py --catalog registry/vx-microevolution-ideas.v1.json --output build/microevolution/idea-evaluation.json
python -m unittest tests.test_vx_microevolution_ideas -v
```

Portfolio scores are triage signals only; novelty remains unassessed and no proposal is automatically adopted.
