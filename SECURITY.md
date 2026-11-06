# Security Policy

## Reporting

Do not disclose unpatched vulnerabilities in public issues. Use the repository's private security-reporting mechanism when available.

## Scope

Security-sensitive changes must preserve the VAIXLNS canonical-source, admission, provenance, evidence, deterministic-runtime, and non-loss rules.

## Administrative boundary

Branch protection, required reviews, secret policies, and private reporting configuration are administrative controls and are not claimed as configured by this file.


## Malware and malicious-code control

All tracked files are scanned by the deterministic repository malware guard at
scripts/security_guard.py during conformance and by the dedicated Malware Guard
workflow.

High-confidence detections block admission. Optional remediation quarantines the
affected file under .security-quarantine/<sha256>/ instead of silently deleting
it, preserving the project's non-loss and recovery guarantees.

This repository-local control is a first-pass detector, not a claim of malware
immunity. Code scanning, dependency analysis, secret scanning, provenance
verification, and runtime isolation remain complementary controls.
