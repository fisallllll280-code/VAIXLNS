# VAIXLNS — Error and Replay Protocol v1

ERROR → IDENTIFY → CAPTURE → CLASSIFY → ROOT-CAUSE → PATCH → TEST → REPLAY → REGRESSION → EVIDENCE

Error classes:
BUILD | RUNTIME | DEPENDENCY | CONFIGURATION | CONTRACT | STATE | DATA | INTEGRATION | PERFORMANCE | SECURITY | NON-DETERMINISM | ARCHITECTURAL

Replay must preserve enough evidence to reproduce the original condition:
code SHA, inputs, configuration, dependency snapshot, environment, event sequence and relevant state.

An item is not marked VERIFIED because a patch compiles. The corrected behavior must pass the relevant test/simulation/replay and retain evidence.
