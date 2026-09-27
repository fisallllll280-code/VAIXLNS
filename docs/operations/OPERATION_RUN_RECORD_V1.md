# VAIXLNS — Operation Run Record v1

Every executable operation must be reproducible from an evidence record.

Required fields:

- run_id
- operation_id
- system_id
- repository
- commit_sha
- input_hash
- configuration_hash
- dependency_snapshot
- environment
- start_time
- end_time
- status
- events
- stdout/stderr references
- artifacts
- errors
- simulation_reference
- verification_reference
- proof_reference
- recovery_reference
- parent_run_id
- replay_of
- lineage

Minimum states:

PLANNED
BOOTING
RUNNING
PASSED
FAILED
BLOCKED
RECOVERING
REPLAYING
VERIFIED
REGRESSED
QUARANTINED
