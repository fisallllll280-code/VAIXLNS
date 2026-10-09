"""Safe, evidence-aware command engine for the VAIXLNS local console.

This console never executes free-form shell text. It dispatches a fixed set of
allow-listed commands against the current repository checkout.
"""
from __future__ import annotations

import hashlib
import json
import os
import shlex
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


GENOME_PATH = "project.genome"
MASTER_INDEX_PATH = "registry/omega/omega-000-master-index.json"
AGENT_REGISTRY_PATH = "registry/agent_registry.v1.json"
ZERO_HASH = "0" * 64


def canonical_digest(value: object) -> str:
    material = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


class CommandError(ValueError):
    """Raised when a known command is used incorrectly."""


class CommandEngine:
    def __init__(self, root: str | Path | None = None) -> None:
        self.root = Path(root or Path(__file__).resolve().parents[2]).resolve()
        self._events: list[dict[str, Any]] = []
        self._last_event_hash = ZERO_HASH
        self._lock = threading.RLock()

    def state(self) -> dict[str, Any]:
        genome = self._read_json(GENOME_PATH, required=False)
        index = self._read_json(MASTER_INDEX_PATH, required=False)
        agents = self._read_json(AGENT_REGISTRY_PATH, required=False)
        runtime_configured = bool(os.environ.get("VX_RUNTIME_URL", "").strip())
        return {
            "system": "VAIXLNS",
            "index_id": index.get("index_id") if isinstance(index, dict) else None,
            "index_status": index.get("status") if isinstance(index, dict) else "MISSING",
            "genome_version": (
                genome.get("canonical_source", {}).get("version")
                if isinstance(genome, dict) else None
            ),
            "agent_count": len(agents.get("agents", [])) if isinstance(agents, dict) else 0,
            "runtime": "CONFIGURED_UNCHECKED" if runtime_configured else "NOT_CONNECTED",
            "event_count": len(self._events),
            "last_event_hash": self._last_event_hash,
            "mode": "LOCAL_REPOSITORY",
        }

    def execute(self, raw_command: str) -> dict[str, Any]:
        raw = (raw_command or "").strip()
        if not raw:
            return {"ok": False, "summary": "Empty command.", "lines": ["Type help to list available commands."], "data": None, "evidence": []}
        if len(raw) > 1200:
            return {"ok": False, "summary": "Command rejected: input exceeds 1200 characters.", "lines": [], "data": None, "evidence": []}
        try:
            tokens = shlex.split(raw)
            if not tokens:
                raise CommandError("Empty command.")
            result = self._dispatch(tokens)
        except CommandError as exc:
            result = {"ok": False, "summary": str(exc), "lines": [str(exc)], "data": None, "evidence": []}
        except Exception as exc:  # the API returns a concise error, not a server traceback
            result = {"ok": False, "summary": "Command failed safely.", "lines": [f"{type(exc).__name__}: {exc}"], "data": None, "evidence": []}

        event = self._record(raw, bool(result.get("ok")), str(result.get("summary", "")))
        result["event"] = event
        result["command"] = raw
        return result

    def _dispatch(self, tokens: list[str]) -> dict[str, Any]:
        command = [item.lower() for item in tokens]
        if command == ["help"] or command == ["?"]:
            return self._help()
        if command == ["status"]:
            return self._status()
        if command == ["map"] or command == ["system", "map"]:
            return self._system_map()
        if command[:2] == ["index", "list"] and len(command) == 2:
            return self._index_list()
        if command[:2] == ["index", "search"] and len(tokens) >= 3:
            return self._index_search(" ".join(tokens[2:]))
        if command == ["agents", "list"]:
            return self._agents_list()
        if command[:2] == ["agents", "inspect"] and len(tokens) == 3:
            return self._agent_inspect(tokens[2])
        if command[:2] == ["agents", "route"] and len(tokens) >= 3:
            return self._agents_route(tokens[2:])
        if command == ["genome", "inspect"]:
            return self._genome_inspect()
        if command == ["genome", "verify"]:
            return self._verify_genome()
        if command == ["proof", "verify"]:
            return self._proof_verify()
        if command == ["runtime", "status"]:
            return self._runtime_status()
        if command[:2] == ["runtime", "simulate"]:
            intent = " ".join(tokens[2:]).strip() or "VAIXLNS safe execution rehearsal"
            return self._simulate(intent)
        if command == ["tests", "run"]:
            return self._run_tests()
        if command == ["history"]:
            return self._history()
        known = [
            "help", "status", "map", "index list", "index search <terms>",
            "agents list", "agents inspect <agent-id>", "agents route <capabilities>", "genome inspect",
            "genome verify", "proof verify", "runtime status",
            "runtime simulate <intent>", "tests run", "history",
        ]
        return {
            "ok": False,
            "summary": "Unknown command. No shell command was executed.",
            "lines": [f"Unknown command: {shlex.join(tokens)}", "", "Try: help"],
            "data": {"available_commands": known},
            "evidence": [],
        }

    @staticmethod
    def _ok(summary: str, lines: list[str], data: Any = None, evidence: list[str] | None = None) -> dict[str, Any]:
        return {"ok": True, "summary": summary, "lines": lines, "data": data, "evidence": evidence or []}

    @staticmethod
    def _help() -> dict[str, Any]:
        lines = [
            "VAIXLNS Sovereign Command Console — allow-listed command surface",
            "",
            "CONTROL",
            "  status                         Repository, index, agents, and runtime readiness",
            "  map                            Canonical system boundaries",
            "  history                        In-memory hash-linked session audit",
            "",
            "INDEX & KNOWLEDGE",
            "  index list                     List records in Ω.000",
            "  index search <terms>           Search index and registered-agent metadata",
            "  genome inspect                 Show canonical source and epistemic rules",
            "  genome verify                  Recompute project.genome SHA-256",
            "",
            "AGENT FABRIC",
            "  agents list                    List agents from the canonical agent registry",
            "  agents inspect <agent-id>      Inspect scope, capabilities, and hard rules",
            "  agents route <capabilities>     Find definitions covering all requested capabilities",
            "",
            "PROOF & EXECUTION",
            "  proof verify                   Validate canonical control surfaces and digest",
            "  runtime status                 Check whether an external VX endpoint is configured",
            "  runtime simulate <intent>      Deterministic rehearsal; never claims real execution",
            "  tests run                      Run the repository unittest suite (60-second limit)",
            "",
            "SAFETY",
            "  Free-form shell commands are not supported.",
            "  Runtime simulation is not a production run or VERIFIED evidence.",
            "  External model providers and a live VX runtime are not implied by this console.",
        ]
        return CommandEngine._ok("Command reference loaded.", lines, {"count": 14})

    def _read_json(self, relative: str, required: bool = True) -> Any:
        path = self.root / relative
        if not path.is_file():
            if required:
                raise CommandError(f"Required file missing: {relative}")
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            if required:
                raise CommandError(f"Cannot read valid JSON from {relative}: {exc}") from exc
            return None

    def _status(self) -> dict[str, Any]:
        state = self.state()
        lines = [
            "VAIXLNS LOCAL CONTROL STATUS",
            f"Master index: {state['index_id'] or 'MISSING'} [{state['index_status']}]",
            f"Genome version: {state['genome_version'] or 'MISSING'}",
            f"Registered agents: {state['agent_count']}",
            f"VX runtime: {state['runtime']}",
            f"Local session events: {state['event_count']}",
            "",
            "This reports repository artifacts, not production uptime.",
        ]
        ok = bool(state["index_id"] and state["genome_version"] and state["agent_count"])
        return {"ok": ok, "summary": "Repository surfaces discovered." if ok else "One or more canonical surfaces are missing.", "lines": lines, "data": state, "evidence": [GENOME_PATH, MASTER_INDEX_PATH, AGENT_REGISTRY_PATH]}

    def _system_map(self) -> dict[str, Any]:
        lines = [
            "VAIXLNS  → canonical control plane, governance, provenance",
            "Ω.000    → master index and typed references",
            "VV       → knowledge discovery surface (current epistemic state in index)",
            "VX       → execution / generation boundary; external endpoint not assumed",
            "XV       → planning and intelligence evolution boundary",
            "Agents   → bounded workers with capability, scope, and evidence constraints",
            "Proof    → digest + canonical surfaces + reproducible test outputs",
            "",
            "Authority flows from canonical governance; an agent proposal cannot silently promote itself.",
        ]
        return self._ok("System boundary map loaded from declared VAIXLNS architecture.", lines, {
            "canonical_source": GENOME_PATH,
            "master_index": MASTER_INDEX_PATH,
            "agent_registry": AGENT_REGISTRY_PATH,
            "external_runtime_env": "VX_RUNTIME_URL",
        }, [GENOME_PATH, MASTER_INDEX_PATH, AGENT_REGISTRY_PATH])

    def _index_list(self) -> dict[str, Any]:
        index = self._read_json(MASTER_INDEX_PATH)
        records = index.get("records", []) if isinstance(index, dict) else []
        lines = [f"{index.get('index_id', 'Ω.000')} — {index.get('name', 'Master Index')}", ""]
        for record in records:
            lines.append(
                f"{record.get('id', '?'):30} | {record.get('type', '?'):14} | "
                f"{record.get('epistemic_state', 'UNSET'):12} | {record.get('role', '')}"
            )
        lines.append("")
        lines.append(f"Records found: {len(records)} (from repository file; no generated records added).")
        return self._ok(f"Loaded {len(records)} master-index records.", lines, {"index_id": index.get("index_id"), "records": records}, [MASTER_INDEX_PATH])

    def _index_search(self, query: str) -> dict[str, Any]:
        needle = query.strip().casefold()
        if not needle:
            raise CommandError("Usage: index search <terms>")

        search_sources = [
            (MASTER_INDEX_PATH, "json"),
            (AGENT_REGISTRY_PATH, "json"),
            ("registry/innovation_measurement.v1.json", "json"),
            ("registry/federation_backend_registry.v1.json", "json"),
            ("docs/innovation/innovation-federation.json", "json"),
            ("docs/indexes/INNOVATION_MASTER_INDEX.md", "text"),
            ("docs/indexes/REPOSITORY_FEDERATION_INDEX.md", "text"),
            ("docs/omega/OMEGA_PATTERN_FOUNDRY_V1.md", "text"),
        ]
        matches: list[dict[str, Any]] = []
        searched: list[str] = []
        per_source_limit = 18

        def visit(value: Any, source: str, found: list[dict[str, Any]]) -> None:
            if isinstance(value, dict):
                serialized = json.dumps(value, ensure_ascii=False, sort_keys=True).casefold()
                has_identity = any(
                    key in value for key in
                    ("id", "index_id", "agent_id", "omega_id", "innovation_id", "pattern_id", "name", "title")
                )
                if needle in serialized and has_identity and len(found) < per_source_limit:
                    found.append({"source": source, "record": value, "match_type": "registry-record"})
                for child in value.values():
                    if len(found) >= per_source_limit:
                        break
                    visit(child, source, found)
            elif isinstance(value, list):
                for child in value:
                    if len(found) >= per_source_limit:
                        break
                    visit(child, source, found)

        for relative, kind in search_sources:
            path = self.root / relative
            if not path.is_file():
                continue
            searched.append(relative)
            local: list[dict[str, Any]] = []
            try:
                text = path.read_text(encoding="utf-8")
                if kind == "json":
                    visit(json.loads(text), relative, local)
                else:
                    for line_number, line in enumerate(text.splitlines(), start=1):
                        if needle in line.casefold():
                            local.append({
                                "source": relative,
                                "record": {"line_number": line_number, "text": line[:360]},
                                "match_type": "source-line",
                            })
                            if len(local) >= per_source_limit:
                                break
            except (OSError, json.JSONDecodeError, RecursionError):
                continue
            matches.extend(local)

        lines = [
            f"Federated index search: {query}",
            f"Searchable sources inspected: {len(searched)}",
            f"Matching records/source lines: {len(matches)}",
            "",
        ]
        for item in matches[:80]:
            record = item["record"]
            identity = (
                record.get("id") or record.get("index_id") or record.get("agent_id")
                or record.get("omega_id") or record.get("innovation_id") or record.get("pattern_id")
                or record.get("name") or record.get("title")
            )
            if not identity:
                identity = f"line {record.get('line_number', '?')}: {record.get('text', '')}"
            state = record.get("epistemic_state") or record.get("family") or record.get("authority_scope") or item["match_type"]
            lines.append(f"{identity}  [{state}]  <- {item['source']}")
        if not matches:
            lines.append("No match in the configured local source set. This command does not search the internet or every conversation.")
        elif len(matches) > 80:
            lines.append("Output capped at 80 matches; refine the query for a smaller result set.")
        lines.extend([
            "",
            "Search scope: local canonical/index/innovation records only; each result retains its source path.",
        ])
        return self._ok(
            f"Found {len(matches)} local records or source lines matching {query!r}.",
            lines,
            {"query": query, "searched_sources": searched, "matches": matches[:120]},
            searched,
        )

    def _agents_list(self) -> dict[str, Any]:
        registry = self._read_json(AGENT_REGISTRY_PATH)
        agents = registry.get("agents", []) if isinstance(registry, dict) else []
        lines = [f"Agent registry status: {registry.get('status', 'UNSET')}", f"Registry source: {AGENT_REGISTRY_PATH}", ""]
        for agent in agents:
            lines.append(
                f"{agent.get('agent_id', '?'):8} | {agent.get('canonical_name', 'Unnamed')} | "
                f"{agent.get('family', '?')} | scope={agent.get('authority_scope', 'UNSET')}"
            )
        lines.append("")
        lines.append("Registry presence does not imply an agent process is currently running.")
        return self._ok(f"Loaded {len(agents)} registered agent definitions.", lines, {"status": registry.get("status"), "agents": agents}, [AGENT_REGISTRY_PATH])

    def _agents_route(self, required_capabilities: list[str]) -> dict[str, Any]:
        from agents.agent_fabric import AgentRegistry

        registry = AgentRegistry(self.root / AGENT_REGISTRY_PATH)
        matches = registry.capable_of(required_capabilities)
        lines = [
            "CAPABILITY ROUTING PREVIEW — REGISTRY METADATA ONLY",
            "Required capabilities: " + ", ".join(required_capabilities),
            f"Eligible definitions: {len(matches)}",
            "",
        ]
        for agent in matches:
            lines.append(
                f"{agent.agent_id:8} | {agent.canonical_name} | "
                f"scope={agent.authority_scope} | capabilities={', '.join(agent.capabilities)}"
            )
        if not matches:
            lines.append("No registered definition declares every requested capability.")
        lines.extend([
            "",
            "This finds candidates only. It does not invoke a provider, grant authority, or start an agent process.",
        ])
        return self._ok(
            f"Found {len(matches)} candidate agent definitions for the requested capabilities.",
            lines,
            {"required_capabilities": required_capabilities, "candidates": [
                {
                    "agent_id": agent.agent_id,
                    "canonical_name": agent.canonical_name,
                    "capabilities": list(agent.capabilities),
                    "authority_scope": agent.authority_scope,
                    "hard_rule": agent.hard_rule,
                } for agent in matches
            ]},
            [AGENT_REGISTRY_PATH],
        )

    def _genome_inspect(self) -> dict[str, Any]:
        genome = self._read_json(GENOME_PATH)
        canonical_source = genome.get("canonical_source", {})
        integrity = genome.get("integrity", {})
        lines = [
            f"System: {genome.get('system', {}).get('name', 'UNSET')}",
            f"Canonical source: {canonical_source.get('type')}::{canonical_source.get('version')}",
            f"Authority anchor: {genome.get('genesis', {}).get('authority_anchor')}",
            f"Master index: {genome.get('master_index', {}).get('id')} → {genome.get('master_index', {}).get('path')}",
            f"Hash algorithm: {genome.get('canonicalization', {}).get('hash')}",
            f"Declared SHA-256: {integrity.get('canonical_hash', 'MISSING')}",
            "",
            "Epistemic states: " + ", ".join(genome.get("epistemic_states", [])),
            "Lifecycle states: " + ", ".join(genome.get("lifecycle_states", [])),
            "",
            "A declaration is read as metadata; verification is separately computed.",
        ]
        return self._ok("Canonical genome inspected.", lines, genome, [GENOME_PATH])

    def _verify_genome(self) -> dict[str, Any]:
        genome = self._read_json(GENOME_PATH)
        integrity = genome.get("integrity", {})
        expected = integrity.get("canonical_hash")
        normalized = json.loads(json.dumps(genome, ensure_ascii=False))
        normalized.setdefault("integrity", {})["canonical_hash"] = ""
        actual = canonical_digest(normalized)
        matches = isinstance(expected, str) and expected == actual
        lines = [
            f"Source: {GENOME_PATH}",
            f"Algorithm: SHA-256 over canonical JSON; integrity.canonical_hash set to empty string before hashing",
            f"Expected: {expected or 'MISSING'}",
            f"Computed: {actual}",
            f"Result: {'PASS' if matches else 'FAIL'}",
        ]
        return {
            "ok": matches,
            "summary": "Genome digest matches." if matches else "Genome digest mismatch; canonical integrity is not verified.",
            "lines": lines,
            "data": {"expected": expected, "actual": actual, "matches": matches},
            "evidence": [GENOME_PATH],
        }

    def _proof_verify(self) -> dict[str, Any]:
        checks: list[dict[str, Any]] = []
        def add(name: str, passed: bool, detail: str, source: str = "") -> None:
            checks.append({"name": name, "state": "PASS" if passed else "FAIL", "detail": detail, "source": source})

        genome_path = self.root / GENOME_PATH
        index_path = self.root / MASTER_INDEX_PATH
        agents_path = self.root / AGENT_REGISTRY_PATH
        add("canonical genome exists", genome_path.is_file(), GENOME_PATH, GENOME_PATH)
        add("master index exists", index_path.is_file(), MASTER_INDEX_PATH, MASTER_INDEX_PATH)
        add("agent registry exists", agents_path.is_file(), AGENT_REGISTRY_PATH, AGENT_REGISTRY_PATH)

        try:
            genome = self._read_json(GENOME_PATH)
            normalized = json.loads(json.dumps(genome, ensure_ascii=False))
            expected = normalized.get("integrity", {}).get("canonical_hash")
            normalized.setdefault("integrity", {})["canonical_hash"] = ""
            actual = canonical_digest(normalized)
            add("genome SHA-256", expected == actual, f"expected={expected}; computed={actual}", GENOME_PATH)
            add("genome authority anchor", genome.get("genesis", {}).get("authority_anchor") == "Ω0_GENESIS_CORE", str(genome.get("genesis", {}).get("authority_anchor")), GENOME_PATH)
            index = self._read_json(MASTER_INDEX_PATH)
            add("Ω.000 identity", index.get("index_id") == "Ω.000", str(index.get("index_id")), MASTER_INDEX_PATH)
            add("Ω.000 canonical status", index.get("status") == "CANONICAL", str(index.get("status")), MASTER_INDEX_PATH)
            agents = self._read_json(AGENT_REGISTRY_PATH)
            agent_list = agents.get("agents", [])
            ids = [item.get("agent_id") for item in agent_list]
            add("unique agent IDs", len(ids) == len(set(ids)) and None not in ids, f"{len(ids)} registered definitions; IDs unique", AGENT_REGISTRY_PATH)
        except (CommandError, AttributeError, TypeError) as exc:
            add("canonical JSON parsing", False, str(exc))

        contract_candidates = [
            "VAIXLNS_REPOSITORY_CONTRACT.md",
            "registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md",
        ]
        contract = next((path for path in contract_candidates if (self.root / path).is_file()), None)
        add("repository contract", contract is not None, contract or "contract candidate not found", contract or "")
        workflows = [
            ".github/workflows/vaixlns-conformance.yml",
            ".github/workflows/federation-integrity.yml",
        ]
        workflow = next((path for path in workflows if (self.root / path).is_file()), None)
        add("conformance workflow", workflow is not None, workflow or "workflow candidate not found", workflow or "")
        gate_path = "scripts/federation_integrity_gate.py"
        add("federation integrity gate", (self.root / gate_path).is_file(), gate_path, gate_path)

        passed = sum(check["state"] == "PASS" for check in checks)
        failed = len(checks) - passed
        lines = [
            "DETERMINISTIC PROOF GATE",
            f"Checks: {len(checks)} | PASS: {passed} | FAIL: {failed}",
            "",
            *[f"[{item['state']}] {item['name']}: {item['detail']}" for item in checks],
            "",
            "A passing structural gate is not evidence of production uptime or model quality.",
        ]
        return {"ok": failed == 0, "summary": f"Proof gate {('PASS' if failed == 0 else 'BLOCKED')}: {passed}/{len(checks)} checks passed.", "lines": lines, "data": {"passed": passed, "failed": failed, "checks": checks}, "evidence": list(dict.fromkeys(item["source"] for item in checks if item.get("source")))}

    def _runtime_status(self) -> dict[str, Any]:
        endpoint = os.environ.get("VX_RUNTIME_URL", "").strip()
        artifacts = {
            "stage_entrypoint": "scripts/vx_stage_runtime.py",
            "stage_tests": "tests/test_vx_stage_runtime.py",
            "stage_runbook": "docs/operations/VX_STAGE_RUNTIME_RUNBOOK_V1.md",
        }
        artifact_states = {name: (self.root / path).is_file() for name, path in artifacts.items()}
        if endpoint:
            runtime_state = "CONFIGURED_UNCHECKED"
            detail = "VX_RUNTIME_URL is set, but this console does not claim a successful health check."
        else:
            runtime_state = "NOT_CONNECTED"
            detail = "No VX_RUNTIME_URL configured; no external runtime call was made."
        lines = [
            f"External VX endpoint: {runtime_state}",
            detail,
            "",
            "Repository reference surfaces:",
            *[f"{'FOUND' if exists else 'MISSING'}  {name}: {artifacts[name]}" for name, exists in artifact_states.items()],
            "",
            "A reference entrypoint is not the same as a deployed, live VX service.",
        ]
        return self._ok("Runtime boundary inspected; operational connectivity is not inferred.", lines, {"runtime": runtime_state, "endpoint_configured": bool(endpoint), "artifacts": artifact_states}, list(artifacts.values()))

    def _simulate(self, intent: str) -> dict[str, Any]:
        if len(intent) > 500:
            raise CommandError("Simulation intent must be 500 characters or fewer.")
        from agents.agent_fabric import AgentRegistry, DEFAULT_HANDOFF_CHAIN
        from agents.mind_federation import MindFederation

        registry = AgentRegistry(self.root / AGENT_REGISTRY_PATH)
        agent_by_id = {agent.agent_id: agent for agent in registry.all()}
        chain = tuple(agent_id for agent_id in DEFAULT_HANDOFF_CHAIN if agent_id in agent_by_id)
        if not chain:
            chain = tuple(agent_by_id.keys())
        if not chain:
            raise CommandError("No registered agents are available for simulation.")

        genome = self._read_json(GENOME_PATH)
        index = self._read_json(MASTER_INDEX_PATH)
        federation = MindFederation.from_registry(tuple(agent_by_id.keys()), chain)
        prior = ZERO_HASH
        trace: list[dict[str, Any]] = []
        previous_agent = None

        for sequence, agent_id in enumerate(chain, start=1):
            agent = agent_by_id[agent_id]
            exchange_ref = None
            exchange_hash = None
            if previous_agent is not None:
                source = agent_by_id[previous_agent]
                semantic_state = {
                    "intent": intent,
                    "requested_capability": ", ".join(agent.capabilities) or "general review",
                    "assumptions": ["deterministic rehearsal only", "no external side effects"],
                    "risk": "bounded; no provider calls; no runtime execution",
                    "evidence_refs": [GENOME_PATH, MASTER_INDEX_PATH, AGENT_REGISTRY_PATH],
                    "requested_action": "simulate governed agent handoff",
                    "authority_scope": [source.authority_scope, agent.authority_scope],
                }
                exchange = federation.exchange(
                    source_agent=previous_agent,
                    target_agent=agent_id,
                    semantic_state=semantic_state,
                    evidence_refs=(GENOME_PATH, MASTER_INDEX_PATH, AGENT_REGISTRY_PATH),
                    authority_scope=(source.authority_scope, agent.authority_scope),
                )
                exchange_ref = exchange.exchange_id
                exchange_hash = exchange.state_hash

            event_data = {
                "sequence": sequence,
                "agent_id": agent.agent_id,
                "agent_name": agent.canonical_name,
                "family": agent.family,
                "capabilities": list(agent.capabilities),
                "authority_scope": agent.authority_scope,
                "declared_hard_rule": agent.hard_rule,
                "intent": intent,
                "genome_version": genome.get("canonical_source", {}).get("version"),
                "index_id": index.get("index_id"),
                "handoff_id": exchange_ref,
                "handoff_state_hash": exchange_hash,
                "previous_hash": prior,
            }
            digest = canonical_digest(event_data)
            trace.append({**event_data, "event_hash": digest})
            prior = digest
            previous_agent = agent_id

        federation_state = federation.state()
        lines = [
            "MODE: SIMULATION_ONLY",
            f"Intent: {intent}",
            f"Registry source: {AGENT_REGISTRY_PATH}",
            f"Registered definitions: {len(registry.all())}",
            f"Agents rehearsed in governed chain: {len(trace)}",
            f"Semantic handoffs validated: {federation_state['exchange_count']}",
            "",
            *[
                f"{item['sequence']:02d} {item['agent_id']} | {item['agent_name']} "
                f"| scope={item['authority_scope']} | {item['event_hash'][:12]}"
                for item in trace
            ],
            "",
            f"Final trace hash: {prior}",
            f"Federation history hash: {federation_state['history_hash']}",
            "No project files were changed. No external model or VX runtime was called.",
            "Result state: SPECIFIED (simulation trace only; not VERIFIED execution evidence).",
        ]
        return self._ok(
            "Deterministic governed-agent rehearsal completed; no production execution occurred.",
            lines,
            {
                "mode": "SIMULATION_ONLY",
                "intent": intent,
                "trace": trace,
                "final_hash": prior,
                "federation_state": federation_state,
                "epistemic_state": "SPECIFIED",
                "chain": list(chain),
            },
            [GENOME_PATH, MASTER_INDEX_PATH, AGENT_REGISTRY_PATH],
        )

    def _run_tests(self) -> dict[str, Any]:
        tests_dir = self.root / "tests"
        if not tests_dir.is_dir():
            raise CommandError("Test suite unavailable: tests/ directory not found.")
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
        try:
            process = subprocess.run(
                command,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "summary": "Test suite timed out after 60 seconds.", "lines": ["TIMEOUT: python -m unittest discover -s tests -p test_*.py"], "data": {"timeout_seconds": 60}, "evidence": ["tests/"]}
        output = (process.stdout + "\n" + process.stderr).strip()
        output_lines = output.splitlines()[-80:] if output else ["No test output was produced."]
        lines = [f"Command: {shlex.join(command)}", f"Exit code: {process.returncode}", "", *output_lines]
        passed = process.returncode == 0
        return {"ok": passed, "summary": "Repository test suite passed." if passed else "Repository test suite failed; inspect output.", "lines": lines, "data": {"exit_code": process.returncode, "output": output[-12000:]}, "evidence": ["tests/"]}

    def _history(self) -> dict[str, Any]:
        with self._lock:
            events = self._events[-15:]
        lines = ["IN-MEMORY HASH-LINKED SESSION HISTORY", ""]
        if not events:
            lines.append("No command events recorded yet.")
        for event in events:
            lines.append(f"{event['sequence']:04d} {event['timestamp']} {'PASS' if event['ok'] else 'FAIL'} {event['command']} [{event['event_hash'][:16]}]")
        lines.extend(["", f"Events in this process: {len(self._events)}", f"Latest hash: {self._last_event_hash}", "History is process-local and is reset when the server restarts."])
        return self._ok(f"Loaded {len(events)} recent session events.", lines, {"events": events, "count": len(self._events), "last_hash": self._last_event_hash})

    def _record(self, command: str, ok: bool, summary: str) -> dict[str, Any]:
        with self._lock:
            body = {
                "sequence": len(self._events) + 1,
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "command": command,
                "ok": ok,
                "summary": summary[:300],
                "previous_hash": self._last_event_hash,
            }
            event_hash = canonical_digest(body)
            event = {**body, "event_hash": event_hash}
            self._events.append(event)
            self._last_event_hash = event_hash
            return event
