# VAIXLNS Archive Operating Model V1

The canonical repository now contains the control plane for zero-loss source
capture. It does not silently replace source-owned repositories.

## Capture

Each snapshot records repository identity, source ref, exact commit, Git tree
identifier, deterministic archive SHA-256 digest, capture timestamp, and
capture status/error when access is unavailable.

The automated workflow produces one federation bundle containing the accessible
source trees plus the manifest.

## Private repositories

Private sources require `VAIXLNS_FEDERATION_TOKEN` as a GitHub Actions secret.
The token is used only at runtime and is never written to the repository.

Without that secret, public sources can still be captured and private sources
are recorded as `CAPTURE_FAILED`; the workflow does not invent a successful
snapshot.

## Recovery

Recovery means restoring an exact captured source into a new revision. It does
not mutate the historical snapshot.

## Boundary

The workflow creates a durable manifest in Git and a downloadable recovery
bundle in GitHub Actions artifacts. A dedicated external archive repository
remains a separate hosting decision because repository creation is not available
through the current GitHub connector.
