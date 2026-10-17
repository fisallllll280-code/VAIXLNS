#!/usr/bin/env python3
"""VAIXLNS / VX master-plan runner.

This is a single, read-only orchestration entry point for consolidating the
project plans into ordered gates. It audits repository artifacts and can run
the local test suite. It does NOT deploy services, provision credentials,
connect external providers, or claim integrations that are not configured.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PHASES = [
    ("P0", "Inventory and canonical ownership", [
        "Inventory repositories, indexes, services, agents, contracts, and legacy IDs.",
        "Map each artifact to one canonical owner; preserve source identity and lineage.",
        "Record each integration as PRESENT, PARTIAL, UNVERIFIED, or MISSING.",
    ]),
    ("P1", "Constitution and proof-carrying state", [
        "Treat PCS-001 / VX-CGF as the shared admission invariant for protected state.",
        "Require schema, content digest, evidence, replay inputs, independent verification, provenance, authorized promotion, and non-revoked validity.",
        "Fail closed when proof is missing, stale, contradictory, or invalid.",
    ]),
    ("P2", "Nexus and decomposition", [
        "Decompose each artifact by identity, type, semantics, purpose, structure, capability, relations, contract, authority, state, events, evidence, tests, lifecycle, and lineage.",
        "Generate dependency and impact maps without treating documentation as implementation.",
        "Do not replace the canonical architecture with a parallel framework.",
    ]),
    ("P3", "VX execution and model/tool federation", [
        "Route requests through policy, capability checks, adapter selection, bounded execution, verification, and event recording.",
        "Keep unconfigured model/tool connectors disabled; never infer live connectivity from a registry entry.",
        "Load credentials only from the deployment environment or approved secret manager; never print secrets.",
    ]),
    ("P4", "Agents and task orchestration", [
        "Use the task lifecycle: input -> policy -> plan -> authorize -> execute -> verify -> record.",
        "Give each agent a bounded role, declared tools, data scope, timeout, budget, and rollback/stop conditions.",
        "Require independent verification for high-impact outputs and all protected-state promotions.",
    ]),
    ("P5", "State, events, ledger, replay, and recovery", [
        "Record event ID, timestamp, actor, source, input/output digests, decision, evidence, and trace/correlation ID.",
        "Make state transitions auditable and replayable from pinned inputs, runtime version, and configuration.",
        "Test crash recovery, duplicate delivery, partial failure, and revocation; do not equate a ledger with consensus.",
    ]),
    ("P6", "System integrations and conformance", [
        "Map VX, VLNS/LNS, NEXENT, VXNode, repositories, APIs, and tools to explicit contracts.",
        "For each connector, test authentication, permissions, timeouts, retries, rate limits, error mapping, and data boundaries.",
        "Do not mark an integration complete until an end-to-end test proves its behavior.",
    ]),
    ("P7", "Engineering domains and simulation", [
        "Integrate mathematical models, computation/solvers, engineering models, physics, and simulation behind versioned contracts.",
        "Capture assumptions, units, model/version digests, parameters, outputs, uncertainty, and verification evidence.",
        "Keep simulated results distinct from observations of the real world.",
    ]),
    ("P8", "Control-center UI and observability", [
        "Provide system overview, architecture/dependencies, integrations, agents/tasks, runtime, events/state, ledger/provenance, verification/proof, operations, simulation, and evolution views.",
        "Drive screens from real APIs and label missing data as unavailable; never show mock status as live telemetry.",
        "Expose health, latency, failures, resource use, connector state, and audit traces.",
    ]),
    ("P9", "Security, tests, and release gates", [
        "Run unit, contract, integration, end-to-end, failure-injection, permission, and bypass tests.",
        "Verify every protected-state writer and promotion endpoint calls PCS-001; test direct bypass attempts.",
        "Release only after CI passes, secrets and policies are configured, rollback is tested, and operational ownership is explicit.",
    ]),
]

REQUIRED_ARTIFACTS = {
    "PCS-001 contract": "docs/canonical/PCS-001-VX-CGF.md",
    "PCS-001 validator": "scripts/pcs001_validator.py",
    "PCS-001 tests": "tests/test_pcs001_validator.py",
    "VX federation runtime": "scripts/vx_federation_runtime.py",
    "VX connector registry": "registry/federation/vx_model_connectors.v1.json",
}


def load_registry(path: Path) -> tuple[int, dict[str, int]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    connectors = data.get("connectors", [])
    statuses: dict[str, int] = {}
    for connector in connectors:
        status = str(connector.get("status", "UNKNOWN")).upper()
        statuses[status] = statuses.get(status, 0) + 1
    return len(connectors), statuses


def audit() -> int:
    print("VAIXLNS / VX — READ-ONLY IMPLEMENTATION AUDIT")
    print(f"Repository root: {ROOT}")
    missing = []
    for label, relative in REQUIRED_ARTIFACTS.items():
        exists = (ROOT / relative).is_file()
        print(f"[{'OK' if exists else 'MISSING'}] {label}: {relative}")
        if not exists:
            missing.append(relative)

    registry_path = ROOT / REQUIRED_ARTIFACTS["VX connector registry"]
    if registry_path.is_file():
        try:
            count, statuses = load_registry(registry_path)
            print(f"[INFO] Connectors declared: {count}")
            for status, amount in sorted(statuses.items()):
                print(f"[INFO] Connector status {status}: {amount}")
            if statuses.get("NOT_CONFIGURED", 0):
                print("[GATE] Unconfigured connectors remain disabled; credentials/configuration are required.")
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            print(f"[FAIL] Cannot parse connector registry: {exc}")
            missing.append("valid connector registry")
    print("[GATE] Repository-wide PCS-001 enforcement is NOT proven by file presence alone.")
    print("[GATE] External connectivity, deployment, and production readiness are NOT inferred by this audit.")
    return 1 if missing else 0


def run_tests() -> int:
    tests_dir = ROOT / "tests"
    if not tests_dir.is_dir():
        print("[FAIL] tests/ directory is missing.")
        return 2
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(tests_dir), "-v"]
    print("+", " ".join(command))
    return subprocess.run(command, cwd=ROOT, check=False).returncode


def print_plan() -> None:
    print("VAIXLNS / VX — CONSOLIDATED MASTER PLAN")
    print("Execution order: inventory -> proof/state -> architecture -> federation -> agents")
    print("                 -> ledger/replay -> integrations -> engineering -> UI/operations -> release")
    print("This script is a gate runner, not an automatic deployment system.\n")
    for code, title, tasks in PHASES:
        print(f"{code} — {title}")
        for task in tasks:
            print(f"  - {task}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", action="store_true", help="print the consolidated plan (default)")
    parser.add_argument("--check", action="store_true", help="audit required repository artifacts and connector status")
    parser.add_argument("--run-tests", action="store_true", help="run Python unittest discovery")
    args = parser.parse_args()
    selected = args.plan or args.check or args.run_tests
    result = 0
    if not selected or args.plan:
        print_plan()
    if args.check:
        result = max(result, audit())
    if args.run_tests:
        result = max(result, run_tests())
    return result


if __name__ == "__main__":
    raise SystemExit(main())
