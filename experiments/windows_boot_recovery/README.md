# VAIXLNS Windows Boot & Recovery Fabric

**State:** SPECIFIED / prototype pending CI. This is a declarative, plan-only engineering experiment, not a Windows installer or repair utility.

## Mission

Define a simple, testable path for Windows boot-readiness checks, recovery triage, device/driver profile descriptions, user-approved remediation proposals, and future partner integrations.

## Boundaries

- No Windows system changes, boot configuration writes, disk formatting, registry edits, driver installation, or automatic repair.
- No edits to `project.genome`, `Ω.000`, canonical registries, or the main runtime.
- No third-party dependencies; prototype uses the Python standard library.
- All diagnosis is a ranked hypothesis based only on supplied symptoms, not a claim of certainty.
- Any remediation with external or destructive effects is blocked by default and must remain an explicit, reviewed human decision.
- Device profiles describe requirements and provenance only. They do not contain binary drivers or bypass Windows driver-signing policy.

## Modules

- `profiles/windows-support-profiles.v1.json`: declarative support/widget/partner profiles.
- `diagnostics.py`: deterministic, read-only triage scoring and action gating.
- `tests/test_windows_boot_recovery_fabric.py`: reproducible contract tests.
- `.github/workflows/windows-boot-recovery-fabric.yml`: CI matrix on Python 3.10 and 3.12.

## Repeatable test

```bash
python -m unittest discover -s tests -p 'test_windows_boot_recovery_fabric.py' -v
```

## Official Microsoft references

- Windows Recovery Environment and startup recovery: https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-re-troubleshooting-features
- WinRE technical reference: https://learn.microsoft.com/en-us/windows-hardware/manufacture/desktop/windows-recovery-environment--windows-re--technical-reference
- Driver installation and signature requirements: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/
- Driver package integrity and Driver Store: https://learn.microsoft.com/en-us/windows-hardware/drivers/install/driver-store

These references inform the design; they do not mean this prototype is certified by Microsoft or integrated with Windows APIs.

## Next gates

1. Pass CI and review the profile schema.
2. Add fixture-based diagnostic cases from sanitized, non-sensitive logs.
3. Add a read-only Windows adapter that collects only user-approved diagnostic facts.
4. Verify recovery recommendations in disposable Windows virtual machines and snapshots.
5. Add a human-approval gate with a signed, expiring approval receipt before any future repair action.
6. Evaluate partnership options through official programs and documented eligibility; no partnership is implied by this prototype.
