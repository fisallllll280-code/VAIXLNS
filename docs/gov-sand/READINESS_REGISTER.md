# GOV/MIL Evidence & Gap Register (baseline 2026-10-27)
| ID | Requirement | Current state | Evidence needed | Owner |
|---|---|---|---|---|
| GOV-001 | Saudi commercial registration and legal entity | UNKNOWN | Official commercial registry extract / authority | Founder |
| GOV-002 | Authorized signatory and IP ownership | PENDING | Company/owner documents; repository license/IP review | Founder/legal |
| GOV-003 | Defence partnership channel and eligibility | PENDING | Official programme criteria and correspondence | Partnerships |
| GOV-004 | Supplier qualification, if relevant | PENDING | Official portal registration and confirmation | Partnerships |
| GOV-005 | Personal data classification and lawful purpose | PENDING | Privacy notice, data map, legal review | Privacy |
| GOV-006 | Consent design and controlled sharing | PROTOTYPE | Tests for explicit opt-in, revocation, audit | Engineering/privacy |
| GOV-007 | Cybersecurity and hosting requirements | PENDING | NCA/DGA applicability assessment, threat model | Security |
| GOV-008 | Banking/open banking/financing regulatory scope | PENDING | Written Saudi legal/regulatory assessment | Legal/compliance |
| GOV-009 | Court enforcement boundary | POLICY | Legal review: no automated stay/waiver | Legal |
| GOV-010 | Service simulation | PROTOTYPE | Passing unit tests and reviewed results | Engineering |
| GOV-011 | Pilot partnership and data-sharing agreement | NOT STARTED | Signed agreements and authorized API approvals | Partnerships |
| GOV-012 | Real user operations | NOT STARTED | Production evidence, authorized user studies | Operations |
| GOV-013 | Budget and sustainable financing | PENDING | Costed 12-month budget / funding source | Finance |

**Evidence policy:** NEVER convert PROTOTYPE, POLICY, or document presence into VERIFIED_OPERATIONAL. All claimed approvals require verifiable dated records and issuer. Never commit citizen data, financial statements, IDs, API credentials, or defence operational information to this repository.

## Release decision
Current status: **NO-GO for production / government integration**, **GO for isolated synthetic-data prototype and legal/partnership preparation**.

## First actions
1. Validate commercial registration and authorized representation.
2. Run unit tests in CI; attach green run URL to GOV-010.
3. Verify current Defence/اعتزاز partnership criteria from official source.
4. Produce privacy impact assessment and security threat model before any real applicant data.
5. Obtain written legal advice on financial intermediation, collections, personal data, and government procurement.
