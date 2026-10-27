# VAIXLNS — Digital Service Journey Assurance / مساعد الخدمات الذكية
Status: PROPOSED / NOT INTEGRATED WITH ANY GOVERNMENT SYSTEM
Date: 2026-10-27
Canonical owner: VAIXLNS. Proposed VX governed capability; VV user experience.

## Public value
Reduce avoidable errors, wrong-channel visits, repeated appointments and incomplete applications while keeping all authoritative decisions in the official government portal. Improve discoverability, accessibility, clarity and transparency. Do NOT claim passport issuance, guaranteed acceptance, available booking slots or official affiliation.

## Initial journey: Saudi passport application / renewal support
Official destination: https://www.absher.sa/
1. User chooses issue vs renew and the beneficiary category.
2. Explain official prerequisites with source URL, publication/verification date, and confidence/freshness; mark unknown items for official confirmation.
3. Give a PRIVACY-MINIMIZED checklist: photo and name validation prompts, eligibility routing, delivery address, payment/receipts and handoff steps as appropriate to the current official journey. Never solicit/store identity numbers, passport numbers, OTP, documents or passwords by default.
4. Show PRE-SUBMISSION review: incomplete fields, contradictory selections, Arabic/English name mismatch as advisory, date/calendar mismatch, unsupported assumptions, need for explicit consent.
5. Deep link user to the official service; user authenticates directly there. Never mimic official login or bypass CAPTCHA/identity checks.
6. If an official appointment is necessary, guide users through the official appointment surface; NEVER imply appointment always required. Issuance and renewal may be available electronically without an appointment; rules must be checked per journey.
7. Only an approved API with proper agreement and scopes may request real appointment availability or act on a user's behalf. No uncontrolled scraping or booking.
8. Reminders/assisted review require explicit opt-in; never automatically submit/pay/book/cancel.
9. Official portal remains sole authority for eligibility, fees, appointment inventory and final acceptance.

## Additional journeys to evaluate
- Identity/records renewal and correction routing
- Travel permit information and status guidance
- Healthcare appointment guidance through official providers (future governed integration)
- Municipal licensing checklist and commercial permit preflight
- Accessibility and plain-language service navigation

## Proposed service design
VV multilingual accessible mobile UI → sourced Service Catalog → Requirement Validation Engine → VX policy gate → user-reviewed checklist → official handoff / approved provider adapter → evidence and feedback (without sensitive contents).
Service Catalog fields: service_id, official_authority, official_url, requirement_source, last_verified, eligibility_scope, exceptions, action_mode (GUIDANCE_ONLY|AUTHORIZED_API), data_classes, retention_policy, uncertainty, human_escalation.
No official logo/branding or endorsement claim.

## Success measures and fair evaluation
Conduct an ethics-reviewed simulated usability study on synthetic personas first, followed by authorized opt-in field pilot.
- completion rate for a clearly defined step
- pre-submission error rate (% using fixed evaluation cases)
- average time to find correct service or instruction
- avoidable wrong-appointment recommendation rate (target 0 in fixed scenario suite)
- successful official handoff rate (with explicit consent / no credential capture)
- accessibility task completion (keyboard, Arabic RTL, screen-reader checks)
- user-reported satisfaction and clarified uncertainty
For a live pilot, randomized or matched comparison and clear sample size; no made-up economic impact.

## Controls and stop conditions
- No official claim, no promise of passport/visa approval.
- No automatic reservations or cancellations without authorized API and explicit user confirmation.
- Fail closed for stale information or conflicting authority, showing only official destination for further steps.
- User never provides government portal passwords or OTP to VAIXLNS.
- No personal-document ingestion until security, privacy/legal review and purpose limitation are completed.
- Independent accessibility, legal and security review prior to deployment.
- No modifications to project.genome or Ω.000. No merge/release without user approval.
- Preserve clear distinction between demo, prototype and authorized production integrations.

## Submission package positioning
Not a replacement for Absher or government systems. A complementary service-discovery, preparation, error-prevention and accessible navigation layer. Value proposition must be evaluated in partnership with public-sector stakeholders and governed by DGA standards where applicable.

## Milestones
Days 1–3: validate sources, interview / study user journeys, scope measurable pain points.
Days 4–7: build offline checklists with sourced requirements and synthetic fixtures; run negative tests.
Days 8–10: accessibility and privacy review; prototype guided journey and proof receipts.
Days 11–14: usability pilot, independently reviewed results, proposal/dossier submission. External integrations and government approvals are not promised by this schedule.
