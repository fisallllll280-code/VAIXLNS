# Closed Engineering Workspaces v1

## Purpose
Provide a deterministic, fail-closed workspace lifecycle for agent-generated engineering artifacts. The first implementation is a local filesystem control layer, not a hardened operating-system sandbox.

## Security contract
- Workspace identifiers are restricted to a bounded safe character set.
- Workspaces are created below an explicitly configured root; duplicate names and traversal attempts are rejected.
- New workspace directories request owner-only permissions (0700).
- Network access, host mounts, production credentials, canonical writes, production deployments, and command execution are denied/disabled by policy declaration.
- A sealed baseline records relative file paths, sizes, and SHA-256 digests. Verification detects changed, added, and removed files.
- Symlinks are rejected during inventory to avoid following workspace paths outside the boundary.
- Authority remains PENDING. A valid file baseline does not authorize execution, promotion, merge, or deployment.

## Current limits
This code does NOT create a container, VM, namespace, seccomp policy, network firewall, credential broker, or OS-enforced filesystem boundary. It does not execute untrusted code. The isolation object is a declared policy contract; actual enforcement beyond the filesystem checks is not yet implemented. Do not use this module alone to run hostile code or to claim production-grade isolation.

## API example
```python
from scripts.closed_workspaces import create_workspace, seal_workspace, verify_workspace
create_workspace("/secure/local/workspaces", "mission-001", mission_id="MIS-001", source_revision="git:<pinned-commit>")
seal_workspace("/secure/local/workspaces", "mission-001")
result = verify_workspace("/secure/local/workspaces", "mission-001")
assert result["valid"]
```

Use a dedicated OS account and an actual container/VM runtime with network disabled, read-only source mounts, resource quotas, and no production credentials before adding an execution adapter.

## Status
SPECIFIED + IMPLEMENTED for local lifecycle and integrity checks. PARTIAL for isolation; OS-enforced containment and execution adapter remain MISSING. CI results determine test status. No production-readiness claim is made.