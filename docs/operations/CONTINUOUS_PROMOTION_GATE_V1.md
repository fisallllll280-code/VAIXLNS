# VAIXLNS Continuous Promotion Gate v1

## Purpose

Provide one repeatable, evidence-backed decision before promoting an open pull request into main. The gate runs after a submitted review, on manual dispatch, and every 15 minutes. It reports an explicit hold reason for every pull request that is not ready.

## Required conditions

A pull request is eligible for merge only when all of the following are true:

1. It targets main and is not a draft.
2. GitHub reports the review decision as APPROVED. Automated checks cannot grant this approval.
3. GitHub reports the pull request as MERGEABLE and exposes the current head commit SHA.
4. At least one status/check result is present.
5. Every observed check is complete and successful, or explicitly neutral/skipped. Pending, failed, cancelled, malformed, missing, or unknown check evidence holds the pull request.

The planner is a deterministic, read-only Python module. It never approves a change, alters repository state, merges, or deploys. The workflow checks out the trusted main branch, creates a machine-readable evidence artifact, and asks GitHub to squash-merge only the exact eligible pull-request numbers. The repository token is required; absence of VAIXLNS_REPO_ADMIN_TOKEN stops the workflow rather than falling back to weaker behavior.

## Deployment boundary

This gate handles merge promotion only; it does not claim that an application has been published or is live. The repository's federated deployment workflow currently builds review plans and explicitly verifies that production remains held. A real deployment needs a verified target, credentials stored in the appropriate GitHub environment, a health check, and rollback evidence. Until those exist, production deployment must remain blocked.

## Local verification

Run the policy tests from the repository root:

- python -m unittest discover -s tests -p "test_continuous_promotion_gate.py" -v

Inspect generated evidence in the vaixlns-continuous-promotion-evidence workflow artifact. A HOLD decision includes the reason codes; no check result should be inferred from a missing artifact or an empty check list.

## Governance invariant

VAIXLNS may continuously observe, test, prepare, and propose. It cannot provide its own approval. Automated promotion requires human review plus independently observed successful checks.
