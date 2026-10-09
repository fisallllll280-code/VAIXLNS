## Purpose
<!-- State the problem and user/business outcome. -->

## Canonical and memory safety
- [ ] I preserved historical records and did not silently delete or overwrite canonical material.
- [ ] Any changed canonical/control-plane surface has a clearly identified owner and rationale.
- [ ] Evidence states remain accurate; no proposal or unexecuted code is labeled VERIFIED.

## Security and privacy
- [ ] No credentials, access tokens, customer secrets, private source contents, or personal data were added.
- [ ] External inputs are treated as untrusted and all new permissions are least-privilege.
- [ ] Repository, workflow, and data-classification boundaries were reviewed.
- [ ] New network endpoints are documented and disabled by default until explicitly approved.

## Verification evidence
- [ ] Tests/checks run against the exact source revision.
- [ ] Relevant logs, hashes, and reproducible instructions are available.
- [ ] Failure cases, rollback, and counterevidence have been considered.

## Repository lifecycle
- [ ] No repository visibility, archive, deletion, collaborator, or billing change is hidden in this PR.
- [ ] If a closure is proposed, the target repository and exact action are documented separately.

## Risk
- Expected impact:
- Data classification:
- Rollback method:
- Required follow-up:
