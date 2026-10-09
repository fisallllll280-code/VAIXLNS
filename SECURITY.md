# Security Policy

## Reporting

Do not disclose unpatched vulnerabilities in public issues. Use the repository's private security-reporting mechanism when available.

## Scope

Security-sensitive changes must preserve the VAIXLNS canonical-source, admission, provenance, evidence, deterministic-runtime, and non-loss rules.

## Administrative boundary

Branch protection, required reviews, secret policies, and private reporting configuration are administrative controls and are not claimed as configured by this file.
## Repository administration

- See [Repository Protection and Closure Policy](docs/operations/REPOSITORY_PROTECTION_AND_CLOSURE_POLICY_V1.md) for branch rules, security controls, freeze/archive gates, and recovery expectations.
- A SECURITY.md file does not prove repository settings are enabled. Verify branch rules, Dependabot alerts, secret scanning/push protection, and code-scanning status in GitHub Settings.
- Never post credentials or private source contents in public issues or pull requests. If a credential may have leaked, revoke or rotate it first, then investigate its history and exposure scope.
