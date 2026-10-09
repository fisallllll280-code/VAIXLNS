# Ω Error Locator — Evidence-First Failure Localization

**State: IMPLEMENTED ON BRANCH; production capability is not yet VERIFIED.**

## Purpose

Ω Error Locator turns an existing build, test or runtime log into a deterministic diagnostic report. It prioritizes explicit traceback frames, compiler/test file locations and failed test names, then classifies common failure signals and recommends verification steps. It targets the case where a tool reports failure but does not clearly show where to investigate.

## Run

From the repository root:

    python scripts/omega_error_locator.py --root . --input path/to/failure.log --output error-triage.json

Or pipe a captured log:

    python scripts/omega_error_locator.py --root . < failure.log

Exit code 0 means a candidate or explicit location was found; exit code 2 means evidence was insufficient or input could not be read. The report state, not the process exit code alone, determines diagnostic strength.

## Report semantics

- LOCATION_FOUND_FROM_EXPLICIT_EVIDENCE: a source path and line appeared in the log and resolved inside the inspected repository. This confirms the reported location, **not** the root cause.
- CANDIDATE_LOCATION_FOUND: a failed test or repository path suggests an inspection target but no precise source line was established.
- LOCALIZATION_INSUFFICIENT_EVIDENCE: no repository location could be grounded in the supplied log. The tool does not invent one.

Every report contains an input SHA-256, ranked locations, supporting log-line numbers, signal classifications, bounded diagnostic lines, limitations and a report hash. Common API-key, token and password patterns are redacted. The tool performs local static analysis only: it does not execute code, install dependencies, query remote services, mutate project files or transmit logs externally.

## Evidence-to-fix loop

1. Capture the complete failure output and pin the repository revision, command and environment.
2. Run the locator and inspect the highest-ranked location plus adjacent call sites.
3. Reproduce with the same pinned inputs. Test competing hypotheses instead of accepting the first match.
4. Make the smallest reviewable patch and add a regression test.
5. Re-run the exact failing command and independent relevant tests; preserve before/after receipts.
6. Keep SPECIFIED, PARTIAL, VERIFIED, CONFLICT and MISSING distinctions. A path match alone never promotes a fix to VERIFIED.

## Known limitations and next increments

This deterministic initial slice uses patterns and file-path heuristics, not a learned causal model. It does not yet ingest GitHub Actions logs automatically, compare multiple commits, build a dependency graph, separate interacting root causes, or dispatch live agents. Follow-up increments should add CI log adapters bound to immutable run/revision IDs, dependency and call-graph correlation, flake-versus-regression analysis across repeated runs, cross-repository correlation for configured VLNS/VX/NEXNET endpoints, and sandboxed approved fix verification. Each needs its own implementation and verification evidence.
