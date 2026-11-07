# AUTO-APPLY – approved-channel playbook
Status: PLANNED, NOT SUBMITTED. Official websites verified 2026-10-27.

1. Intake from registry/gov-sand/priority-roadmap.v1.json. Exclude PERSONAL debt P01 from institutional applications.
2. Route MIL to Eatizaz or MOD Supplier if relevant; other tracks require verified agency mapping.
3. Generate non-confidential brief per agency. Each claim cites its verification scope, not a universal "operational" statement.
4. Confirm legal identity, company registration, applicant authorization, vendor paperwork, privacy policy, IP ownership and pilot security review before dispatch.
5. For officially supported direct integration, require written API/agency agreement and authentication. Otherwise human opens the official page and submits.
6. Track date, exact organization, channel, reference ID, acknowledgement, deadline, response and documents; never infer official status from a local file.
7. Do not automate captcha/OTP/NAFATH, do not upload sensitive personal/military data or disclose private source code to open forms.
8. Retain provenance and immutable evidence links; escalate missing documents, stalled answers and rejections for authorized review.

Channels: https://eatizaz.mod.gov.sa/homepage ; https://supplier.mod.gov.sa/ ; https://monshaat.gov.sa/ar/jadeer . Vendor registration does not guarantee eligibility, acceptance or contract.

CLI: python tools/gov_sand_application_router.py
Output: registry/gov-sand/application-queue.v1.json (local generation only; NOT actual applications).
