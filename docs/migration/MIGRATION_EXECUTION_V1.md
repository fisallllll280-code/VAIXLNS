# VAIXLNS Unification Migration — Execution v1

## Executed in this change

1. Established canonical repository roles.
2. Established version and release gates.
3. Established append-only archive surface.
4. Established recoverable restoration surface.
5. Registered the currently confirmed repositories as migration sources.
6. Explicitly prohibited destructive consolidation.
7. Opened the changes as a pull request instead of mutating main directly.

## Current source set

- VAIXLNS — canonical root.
- VAIXLNS-unified — executable integration surface.
- NEXENT — discovery/search/synthesis.
- vaixlns-nexent-vx — combined experimental VX surface; validate before promotion.
- VX50_COMPLETE_BUILD — historical build surface; validate before canonicalization.

## Next migration operation

Capture exact default-branch commit/ref and content digest for each source, then create an immutable archive snapshot before any file-level merge.
After capture: classify every source path as CANONICAL, INTEGRATED, ARCHIVE, RECOVERY, or QUARANTINE.
Only then perform selective integration into VAIXLNS-unified.

## Safety boundary

This change does not claim that the source repositories have already been physically copied into an external archive repository. The GitHub connection available for this session can read/write repository contents but cannot provision a new repository. Therefore the archive/recovery surfaces are established now and the external repository creation remains an explicit infrastructure step.
