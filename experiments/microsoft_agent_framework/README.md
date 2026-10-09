# Microsoft Agent Framework Coordination Experiment

**Status:** PROPOSAL / prototype scaffold; not a live Microsoft Agent Framework integration.

## Goal

Evaluate Microsoft's official Agent Framework as a replaceable multi-agent orchestration backend for VAIXLNS engineering work orders. This isolated experiment defines deterministic planning and evidence contracts without importing third-party packages, calling model providers, dispatching remote workers, or making external changes.

## Official upstreams reviewed

- Microsoft Agent Framework: https://github.com/microsoft/agent-framework
- Semantic Kernel (upstream README identifies Agent Framework as its successor): https://github.com/microsoft/semantic-kernel
- AutoGen: https://github.com/microsoft/autogen

Agent Framework is the preferred first candidate because its official repository documents Python and .NET support, sequential/concurrent/handoff/group workflow patterns, checkpointing, human-in-the-loop, and OpenTelemetry. The upstream Python package metadata declares Python `>=3.10`; VAIXLNS's existing fast-feedback workflow uses Python 3.12. This is a declared compatibility range, not a completed dependency installation or runtime test.

## Safety and scope

- No changes to `project.genome`, `Ω.000`, canonical registries, or existing runtime paths.
- No SDK dependency added to the root project.
- No credentials, provider calls, server provisioning, code execution, or manufacturing/production actions.
- Agent output is a proposal; only an independent authority can authorize consequential execution or canonical admission.
- The prototype deliberately emits a deterministic plan and hash-linked plan events; it does not run agents.

## Run the repeatable local contract tests

From the repository root, with Python 3.12 (Python 3.10+ is expected for this stdlib-only prototype):

```bash
python -m unittest discover -s tests -p 'test_microsoft_agent_framework_prototype.py' -v
```

The tests use only the Python standard library. No network, secrets, model API, or Microsoft SDK is required.

## Acceptance gates before adding a live adapter

1. Pass the contract tests in CI on Python 3.10 and 3.12.
2. Pin and review a released `agent-framework` package and its transitive dependencies in an experiment-specific environment.
3. Implement an adapter against the exact released SDK API; retain a mock adapter for deterministic tests.
4. Prove timeout/cancellation, retries, duplicate delivery, checkpoint/replay, and failure isolation.
5. Prove capability enforcement, tenant/data-boundary isolation, and fail-closed behavior for external effects.
6. Capture reproducible run receipts and independent verification before any result can be labelled VERIFIED.

Until those gates are met, the status remains **SPECIFIED / IMPLEMENTED_PENDING_CI**, not VERIFIED.
