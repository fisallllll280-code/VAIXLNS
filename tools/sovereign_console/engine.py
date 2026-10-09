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
FEDERATION_INDEX_PATH = "registry/federation/vlns-capability-index.v1.json"
VLNS_CONNECTION_STATUS_PATH = "registry/vlns_connection_status.v1.json"
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
        federation = self._read_json(FEDERATION_INDEX_PATH, required=False)
        fed_systems = federation.get("systems", []) if isinstance(federation, dict) else []
        fed_edges = federation.get("connections", []) if isinstance(federation, dict) else []
        verified_links = sum(1 for edge in fed_edges if edge.get("live_state") == "VERIFIED" and edge.get("authenticated") is True)
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
            "federation_system_count": len(fed_systems),
            "federation_verified_links": verified_links,
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
        if command == ["federation", "status"]:
            return self._federation_status()
        if command[:2] == ["federation", "inspect"] and len(tokens) == 3:
            return self._federation_inspect(tokens[2])
        if command[:2] == ["federation", "capabilities"]:
            return self._federation_capabilities(" ".join(tokens[2:]).strip() or "all")
        if command[:2] == ["federation", "attributes"]:
            return self._federation_attributes(" ".join(tokens[2:]).strip() or "all")
        if command == ["federation", "gaps"]:
            return self._federation_gaps()
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
            "agents list", "agents inspect <agent-id>", "agents route <capabilities>",
            "federation status", "federation inspect <system-id>", "federation capabilities [query]",
            "federation attributes [query]", "federation gaps", "genome inspect",
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
            "FEDERATION & ENGINEERING",
            "  federation status              Four-system inventory and recorded connection state",
            "  federation inspect <system-id> Inspect a system and its identity boundary",
            "  federation capabilities [query] Search declared capability records",
            "  federation attributes [query]  Search individual indexed properties and sources",
            "  federation gaps                Show evidence-backed integration blockers",
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
        return CommandEngine._ok("Command reference loaded.", lines, {"count": 19})

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
            (FEDERATION_INDEX_PATH, "json"),
            (VLNS_CONNECTION_STATUS_PATH, "json"),
            ("registry/innovation_measurement.v1.json", "json"),
            ("registry/federation_backend_registry.v1.json", "json"),
            ("docs/innovation/innovation-federation.json", "json"),
            ("docs/indexes/INNOVATION_MASTER_INDEX.md", "text"),
            ("docs/indexes/REPOSITORY_FEDERATION_INDEX.md", "text"),
            ("docs/indexes/FOUR_SYSTEM_RECONCILIATION_V1.md", "text"),
            ("docs/cognitive/VLNS_MODEL_ACTIVATION_FABRIC_V1.md", "text"),
            ("docs/architecture/VAIXLNS_SYSTEM_CONTEXT_CLOSURE_V1.md", "text"),
            ("docs/federation/VLNS_SYSTEM_FEDERATION_AND_ENGINEERING_DASHBOARD_V1.md", "text"),
            ("docs/omega/OMEGA_PATTERN_FOUNDRY_V1.md", "text"),
        ]
        matches: list[dict[str, Any]] = []
        searched: list[str] = []
        per_source_limit = 18

        def visit(value: Any, source: str, found: list[dict[str, Any]]) -> None:
            if isinstance(value, dict):
                # Match only this record's own scalar fields and scalar lists.
                # Avoid matching ancestors merely because a descendant contains the term.
                own_fields = {
                    key: child
                    for key, child in value.items()
                    if not isinstance(child, dict)
                    and (
                        not isinstance(child, list)
                        or all(not isinstance(element, (dict, list)) for element in child)
                    )
                }
                serialized = json.dumps(own_fields, ensure_ascii=False, sort_keys=True).casefold()
                has_identity = any(
                    key in value for key in
                    ("id", "index_id", "agent_id", "omega_id", "innovation_id", "pattern_id", "capability_id", "property_id", "gap_id", "connection_id", "system_id", "name", "title", "canonical_name")
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

    def _federation_document(self) -> dict[str, Any]:
        document = self._read_json(FEDERATION_INDEX_PATH)
        if not isinstance(document, dict) or not isinstance(document.get("systems"), list):
            raise CommandError("Invalid federation capability index: systems array required.")
        return document

    def _federation_status(self) -> dict[str, Any]:
        document = self._federation_document()
        systems = document["systems"]
        connection_record = self._read_json(VLNS_CONNECTION_STATUS_PATH, required=False)
        connection_record = connection_record if isinstance(connection_record, dict) else {}
        edges = document.get("connections", [])
        verified_links = sum(
            1 for edge in edges
            if edge.get("live_state") == "VERIFIED" and edge.get("authenticated") is True
        )
        lines = [
            "FOUR-SYSTEM FEDERATION INVENTORY — REPOSITORY EVIDENCE ONLY",
            f"Catalog: {document.get('catalog_id', 'UNSET')} [{document.get('status', 'UNSET')}]",
            f"Systems indexed: {len(systems)}",
            f"Verified authenticated links in catalog: {verified_links}/{len(edges)}",
            "",
        ]
        for item in systems:
            surface = ", ".join(item.get("repository_surfaces", []))
            lines.append(
                f"{item.get('system_id', '?'):8} | identity={item.get('identity_status', 'UNKNOWN')} "
                f"| maturity={item.get('epistemic_state', 'UNKNOWN')} | {surface}"
            )
        lines.extend([
            "",
            f"Recorded VLNS probe: {connection_record.get('status', 'UNKNOWN')}",
            f"Probe timestamp: {connection_record.get('last_probe', 'UNKNOWN')}",
            f"Authenticated connection recorded: {connection_record.get('authenticated_connection', False)}",
            "No external health probe was performed by this command.",
            "UNVERIFIED identity and connectivity are not promoted to connected/running.",
        ])
        return self._ok(
            "Loaded indexed federation state; live connectivity remains unverified.",
            lines,
            {
                "catalog_id": document.get("catalog_id"),
                "catalog_status": document.get("status"),
                "system_count": len(systems),
                "systems": systems,
                "connections": edges,
                "verified_live_links": verified_links,
                "recorded_vlns_connection": connection_record,
                "external_probe_performed": False,
            },
            [FEDERATION_INDEX_PATH, VLNS_CONNECTION_STATUS_PATH],
        )

    def _federation_inspect(self, system_id: str) -> dict[str, Any]:
        document = self._federation_document()
        key = system_id.strip().casefold()
        system = next(
            (item for item in document["systems"]
             if item.get("system_id", "").casefold() == key
             or item.get("canonical_name", "").casefold() == key),
            None,
        )
        if system is None:
            raise CommandError(f"System not found in federation index: {system_id}")
        lines = [
            f"{system.get('system_id')} — {system.get('canonical_name', 'UNNAMED')}",
            f"Role: {system.get('role', 'UNKNOWN')}",
            f"Identity state: {system.get('identity_status', 'UNKNOWN')}",
            f"Epistemic state: {system.get('epistemic_state', 'UNKNOWN')}",
            f"Integration state: {system.get('integration_state', 'UNKNOWN')}",
            "Repository surfaces:",
            *[f"  - {value}" for value in system.get("repository_surfaces", [])],
            "Declared capabilities:",
            *[f"  - {value}" for value in system.get("declared_capabilities", [])],
            "Source refs:",
            *[f"  - {value}" for value in system.get("source_refs", [])],
            "",
            "Repository association does not itself prove system identity or runtime health.",
        ]
        return self._ok(
            f"Inspected {system.get('system_id')} from the indexed federation record.",
            lines,
            system,
            [FEDERATION_INDEX_PATH],
        )

    def _federation_capabilities(self, query: str) -> dict[str, Any]:
        document = self._federation_document()
        capabilities = document.get("capability_catalog", [])
        needle = query.casefold()
        matches = capabilities if needle in ("", "all", "*") else [
            item for item in capabilities
            if needle in json.dumps(item, ensure_ascii=False, sort_keys=True).casefold()
        ]
        lines = [
            "VLNS CAPABILITY EXPLORER — CATALOG CLAIMS, NOT RUNTIME ASSERTIONS",
            f"Query: {query}",
            f"Matches: {len(matches)} / {len(capabilities)}",
            "",
        ]
        for item in matches:
            lines.append(
                f"{item.get('capability_id', '?'):14} | {item.get('status', 'UNKNOWN'):14} "
                f"| implementation={item.get('implementation_state', 'UNKNOWN')} "
                f"| {item.get('name', 'Unnamed')}"
            )
            if item.get("description"):
                lines.append(f"  {item['description']}")
        return self._ok(
            f"Found {len(matches)} indexed capability records.",
            lines,
            {"query": query, "capabilities": matches, "total": len(capabilities)},
            [FEDERATION_INDEX_PATH],
        )

    def _federation_attributes(self, query: str) -> dict[str, Any]:
        document = self._federation_document()
        properties = document.get("properties", [])
        families = document.get("attribute_families", [])
        needle = query.casefold()
        if needle in ("", "all", "*"):
            matching_properties = properties
            matching_families = families
        else:
            matching_properties = [
                item for item in properties
                if needle in json.dumps(item, ensure_ascii=False, sort_keys=True).casefold()
            ]
            matching_families = [
                item for item in families
                if needle in json.dumps(item, ensure_ascii=False, sort_keys=True).casefold()
            ]
        lines = [
            "VLNS DEEP ATTRIBUTE INDEX — DECLARATIONS, NOT AUTOMATIC IMPLEMENTATION PROOF",
            f"Query: {query}",
            f"Atomic properties: {len(matching_properties)} / {len(properties)}",
            f"Attribute families: {len(matching_families)} / {len(families)}",
            f"Indexed field definitions returned: {sum(len(item.get('fields', [])) for item in matching_families)}",
            "",
        ]
        for item in matching_properties:
            refs = item.get("source_refs", [])
            lines.append(
                f"{item.get('property_id', '?'):16} | {item.get('category', 'UNKNOWN'):16} "
                f"| {item.get('state', 'UNKNOWN')} | {item.get('name', 'Unnamed')}"
            )
            lines.append(f"  {item.get('value', '')}")
            lines.append(f"  evidence: {'; '.join(refs)}")
        if matching_families and matching_properties:
            lines.append("")
        for item in matching_families:
            fields = item.get("fields", [])
            lines.append(
                f"{item.get('family_id', '?'):18} | {item.get('state', 'UNKNOWN')} "
                f"| {item.get('owner', 'UNKNOWN')} | {item.get('name', 'Unnamed')} "
                f"| fields={len(fields)}"
            )
            lines.append("  fields: " + ", ".join(fields))
            lines.append(f"  evidence: {'; '.join(item.get('source_refs', []))}")
            if item.get("notes"):
                lines.append("  note: " + item["notes"])
        return self._ok(
            f"Found {len(matching_properties)} atomic property and {len(matching_families)} attribute-family records.",
            lines,
            {
                "query": query,
                "properties": matching_properties,
                "attribute_families": matching_families,
                "property_total": len(properties),
                "attribute_family_total": len(families),
                "indexed_field_total": sum(len(item.get("fields", [])) for item in families),
            },
            [FEDERATION_INDEX_PATH],
        )

    def _federation_gaps(self) -> dict[str, Any]:
        document = self._federation_document()
        gaps = document.get("gaps", [])
        lines = [
            "FEDERATION / ENGINEERING GAP BOARD",
            f"Open catalogued gaps: {len(gaps)}",
            "",
        ]
        for item in gaps:
            lines.append(
                f"[{item.get('severity', 'UNKNOWN')}] {item.get('gap_id', '?')} "
                f"| {item.get('topic', 'Unclassified')}: {item.get('issue', '')}"
            )
            lines.append(f"  required evidence: {item.get('required_evidence', 'UNSET')}")
            lines.append(f"  next action: {item.get('next_action', 'UNSET')}")
        lines.extend([
            "",
            "Gap closure requires the named evidence; dashboard presence is not closure.",
        ])
        return self._ok(
            f"Loaded {len(gaps)} integration/engineering gap records.",
            lines,
            {"gaps": gaps, "total": len(gaps)},
            [FEDERATION_INDEX_PATH],
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

    def _agent_inspect(self, agent_id: str) -> dict[str, Any]:
        registry = self._read_json(AGENT_REGISTRY_PATH)
        agents = registry.get("agents", []) if isinstance(registry, dict) else []
        needle = agent_id.casefold()
        agent = next((
            item for item in agents
            if item.get("agent_id", "").casefold() == needle
            or item.get("canonical_name", "").casefold() == needle
        ), None)
        if agent is None:
            raise CommandError(f"Agent not found in {AGENT_REGISTRY_PATH}: {agent_id}")
        lines = [
            f"{agent.get('agent_id')} — {agent.get('canonical_name')}",
            f"Family: {agent.get('family', 'UNSET')}",
            f"Authority scope: {agent.get('authority_scope', 'UNSET')}",
            f"Primary output: {agent.get('primary_output', 'UNSET')}",
            "",
            "Capabilities:",
            *[f"  • {value}" for value in agent.get("capabilities", [])],
            "",
            "Allowed tools:",
            *[f"  • {value}" for value in agent.get("allowed_tools", [])],
            "",
            f"Hard rule: {agent.get('hard_rule', 'UNSET')}",
            "",
            "This is a registry inspection, not proof that this agent is running.",
        ]
        return self._ok(f"Inspected {agent.get('agent_id')}.", lines, agent, [AGENT_REGISTRY_PATH])

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
