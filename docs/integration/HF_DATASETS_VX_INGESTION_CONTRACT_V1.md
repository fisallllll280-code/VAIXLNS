# Datasets → VX governed ingestion contract v0.1

**Status: SPECIFIED / NOT_RUN / NOT_VERIFIED**. This contract is not a functioning Hugging Face adapter. Do not promote it to IMPLEMENTED until code and tests exist.

## Identity and authority
- Canonical authority: VAIXLNS Ω registry and governed admission.
- External code dependency: `fisallllll280-code/datasets` (upstream-derived Hugging Face Datasets source); inventory already lists it as external.
- Runtime executor: VX. NLVN is a *proposed* ingestion domain, not proven to exist as executable code.
- Dataset-specific license/rights must be evaluated separately from the Datasets library's Apache-2.0 license.
- No modifications to `project.genome`, `Ω.000`, or historical source records.

## Intake contract
```json
{
  "source": {
    "kind": "huggingface_hub_or_local",
    "repository": "REQUIRED",
    "revision_sha": "REQUIRED_FOR_HUB",
    "split": "REQUIRED",
    "data_files": [],
    "dataset_card_ref": "UNKNOWN",
    "dataset_license": "UNKNOWN"
  },
  "processing": {
    "streaming": true,
    "schema_contract_sha256": "UNKNOWN",
    "transform_manifest_sha256": "UNKNOWN",
    "max_rows": 1000
  },
  "evidence": {
    "source_hashes": [],
    "row_count_observed": 0,
    "null_counts": {},
    "schema_violations": [],
    "duplicates_exact": 0,
    "sample_hashes": [],
    "test_receipts": [],
    "privacy_review": "PENDING",
    "license_review": "PENDING"
  },
  "admission": {
    "state": "QUARANTINED",
    "reason": "EVIDENCE_REQUIRED"
  }
}
```

## Gates
G1 Source: owner/repo, commit revision, dataset card, per-dataset rights.
G2 Integrity: file and sample fingerprints, per-asset checksums where feasible; streaming alone is not whole-dataset integrity evidence.
G3 Quality: explicit feature/schema contract, nulls, invalid rows, exact duplicates.
G4 Provenance: transform lineage, tools and version pins, original/derived distinction.
G5 Policy: access, sensitive data, license and personal data handling; fail closed on unknown mandatory terms.
G6 VX: bounded test task and immutable evidence receipt.
G7 Ω: independent acceptance; no automatic VERIFIED.

## Acceptance tests (future implementation)
- Reject Hub dataset requests without pinned revision.
- Reject unknown/unauthorized dataset license for governed adoption.
- Quarantine invalid schemas and sensitive content pending review.
- Preserve source, transformation and revision hashes.
- Enforce maximum scan size during local/streaming evaluation.
- Detect exact duplicates; flag semantic duplicates separately.
- Verify deterministic replay on pinned local fixtures.
- Refuse adoption if missing evidence or failed checks.

## Status and implementation boundary
Read-only repository inspection confirmed the datasets repo structure, Apache-2.0 library license, its pytest/Ruff configuration, and VAIXLNS repository inventory's existing external-source classification. It did **not** demonstrate NLVN runtime existence, an actual data ingestion execution, dataset-specific licensing or downstream deployment.

Next implementation target: adapter in existing governed VX runtime, test against a tiny pinned public fixture, keep zero SAR external cost, then independently verify and request admission. No merge/publish without separate approval.
