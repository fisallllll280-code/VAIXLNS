# Repository Protection and Closure Policy v1

**Status: POLICY + REPOSITORY FILES IN FEATURE BRANCH. GitHub administrative settings must still be applied and independently verified.**

## 1. Observed inventory

At the latest connected-account inventory, 51 repositories were returned for the account scope: 26 public, 25 private, and 0 archived. This is a point-in-time inventory, not a full access-control audit. VAIXLNS is public, unarchived, and uses main as its default branch. The connection could not read the branch-protection endpoint (403) and returned an empty visible ruleset list for VAIXLNS; therefore this audit does not establish that all required branch controls are enabled.

Do not publish a list of private repository names or paths inside this public repository. Maintain detailed private inventory in a private audit location.

## 2. Four different actions — never use “close” as an ambiguous command

- **Protect:** retain availability and control writes using branch rules, least privilege, CI gates, secret controls and audit evidence.
- **Freeze/lock writes:** temporarily prohibit ordinary changes through administrative controls, while leaving read access intact.
- **Make private:** restrict visibility to explicitly authorized people. This is not a secret-erasure procedure. Existing public forks can remain public and detached from the upstream.
- **Archive:** make the repository read-only while preserving it as a historical reference. GitHub recommends closing issues and pull requests and updating the README/description first.
- **Delete:** permanent data-loss risk; outside this policy and never automatic.

For this account, default to protecting active canonical repositories and preserving ambiguous/legacy repositories until their lineage and dependencies are reviewed. Do not privatize every public repository or archive a repository merely because its name looks old, duplicated, or temporary.

## 3. Required branch rule for active canonical repositories

Apply a repository ruleset targeting the actual default branch (verify its name first; it is not always main). Recommended rules:

1. Require changes through pull requests; prohibit direct updates to the protected default branch.
2. Require the repository's conformance and integrity checks to pass before merge.
3. Require approval from a reviewer other than the author for high-impact canonical changes where a second authorized reviewer is available.
4. Require code-owner review for protected canonical surfaces and dismissal of stale approvals after material changes.
5. Require conversation resolution and block force pushes and branch deletion.
6. Restrict bypass actors to a short, documented list; review bypass events afterward.
7. Protect .github/workflows/, project.genome, registry/omega/, schemas/, registry/evidence/, recovery data, and the master index with stricter review.
8. Do not require signed commits until all authorized human and automation paths can satisfy that requirement without breaking the recovery/CI pipeline.

Check actual required-check names in a successful run before selecting them. A workflow file or CODEOWNERS file alone does not enforce the rule; the administrative ruleset does.

## 4. Security controls for public and private repositories

- Enable Dependabot alerts and security updates where dependency manifests exist.
- Enable Secret scanning and push protection wherever the plan supports them; immediately revoke/rotate a credential suspected of exposure. Deleting a string from the current file does not invalidate a leaked credential.
- Run CodeQL or an equivalent code-scanning engine. Review alerts and establish a remediation owner rather than treating a completed scan as proof of no vulnerabilities.
- Keep workflow permissions read-only by default; elevate a permission only in the specific job that requires it.
- Pin and review third-party GitHub Actions, constrain workflow_dispatch, and do not expose write-capable secrets to untrusted pull-request code.
- Audit collaborators, personal access tokens, GitHub Apps, deploy keys, webhook targets, environments, environments' required reviewers, and Actions secrets/variables.
- Enable multi-factor authentication and review recovery methods for the owning account.
- Keep credentials and private source data outside the public VAIXLNS repository; use private repositories and dedicated secret stores for sensitive records.

The existing .github/CODEOWNERS names the owner, and SECURITY.md exists. Those files are inputs to governance but do not prove required reviews or security features are enabled.

## 5. Closure/archive preflight

A repository can only be marked ARCHIVE_APPROVED after a reviewed closure record contains all of these:

- Exact repository full name and verified owner.
- Decision: KEEP_ACTIVE, FREEZE_WRITES, MAKE_PRIVATE, or ARCHIVE; these actions are not interchangeable.
- Repository visibility, default branch, latest commit, open PR/issues, releases/tags, Actions artifacts, package/container releases, Pages/custom domains, webhooks, deploy keys and collaborator inventory.
- Incoming/outgoing dependency map from other repositories, workflows, documents, packages, deployment jobs and external users.
- Source snapshot and Git refs backed up; archive bundle hash independently checked; restoration test documented.
- Secrets triaged and rotated if exposure is suspected.
- Migration/redirect/README notice, support owner and rollback path.
- Explicit owner approval and recorded timestamp.

Before archiving, close or transfer open work and update the README/description. After archive, verify it is read-only and that downstream consumers no longer depend on it. Do not delete it as an incidental cleanup step.

## 6. Suggested lifecycle classes

| Class | Default handling | Closure rule |
|---|---|---|
| Canonical active: VAIXLNS, master registry, genome, authority/proof surfaces | Protect; never archive as a cleanup shortcut | Freeze only by explicit incident procedure |
| Active integration/runtime: VLNS/VX/NEXNET equivalents | Protect, pin interfaces and record dependency links | Archive only after migration and dependent workflows pass |
| Recovery/legacy/duplicate-looking repository | Preserve and label REVIEW_REQUIRED | Compare hashes, lineage, forks and incoming references first |
| Public demo or disposable experiment | Keep public only if intentionally public and free of sensitive data | Archive after backup and explicit approval |
| Suspected credential/data leak | Contain exposure immediately, revoke credentials, audit history and forks | Private visibility alone is not sufficient remediation |

## 7. Administrative actions still required

The connected GitHub tooling can read repository metadata and create/update repository files, but it cannot change repository visibility, archive status, branch protection or repository security settings from this session. Complete the controls in GitHub Settings using an authorized administrator, then capture the resulting ruleset and security posture as evidence. Do not treat this document as proof that those settings were applied.

GitHub's current administrative guidance:
- Rulesets and branch protections: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets
- Security and analysis settings: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-security-and-analysis-settings-for-your-repository
- Archiving repositories: https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories
- Repository visibility changes: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility
