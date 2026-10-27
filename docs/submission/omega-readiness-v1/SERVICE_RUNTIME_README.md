# GovFlow — Minimal Offline Reference Implementation

Status: IMPLEMENTED as local advisory-only code, NOT VERIFIED as a live public/government service.

Files: service_assistant.py, test_service_assistant.py. Standard-library Python only.
Run from this directory: `python -m unittest test_service_assistant -v`

This is a small reference kernel, not a government portal integration or production passport checker. Test data must be synthetic. No user identification numbers, OTP, passport documents, authentication sessions, appointment inventory, fees, or payments are obtained or processed. The official service determines every substantive eligibility requirement. There is no booking, API call, or submission function.

The `source_verified_on` flag is supplied by a human reviewer and is not itself proof of an independently checked official source. Even GUIDANCE_READY is advisory and does not signal eligibility or official confirmation.

Next work: verified source catalog with source-page version and review signature; localized accessibility UI; data privacy assessment; state-machine and contract tests; synthetic usability trial; independent reviewed run receipts; official partnership and consent before any real adapter.
