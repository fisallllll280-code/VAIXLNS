"""Deterministic contract tests for the operational office fabric registry."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_office_fabric import validate_registry  # noqa: E402


REGISTRY_PATH = ROOT / "registry" / "office_fabric.integration.v1.json"
SCHEMA_PATH = ROOT / "schemas" / "office-fabric-registry.schema.json"


class OfficeFabricRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_registry_passes_schema_and_graph_integrity(self) -> None:
        self.assertEqual([], validate_registry(self.registry, self.schema))

    def test_declared_counts_match_registry(self) -> None:
        self.assertEqual(len(self.registry["offices"]), self.registry["coverage"]["offices_count"])
        self.assertEqual(len(self.registry["systems"]), self.registry["coverage"]["system_surfaces_count"])
        self.assertEqual(
            len(self.registry["tool_integrations"]),
            self.registry["coverage"]["tool_integrations_count"],
        )

    def test_unresolved_system_identities_remain_unverified(self) -> None:
        systems = {item["system_id"]: item for item in self.registry["systems"]}
        self.assertEqual("IDENTITY_UNVERIFIED", systems["SYS-VLNS"]["status"])
        self.assertEqual("IDENTITY_UNVERIFIED", systems["SYS-NEXNET"]["status"])

    def test_unconfigured_tools_cannot_claim_governed_execution(self) -> None:
        for tool in self.registry["tool_integrations"]:
            if tool["status"] == "NOT_CONFIGURED":
                self.assertNotEqual("GOVERNED_EXECUTION", tool["access_mode"], tool["tool_id"])

    def test_physical_adapters_default_to_observe_or_simulate(self) -> None:
        physical = [
            item for item in self.registry["tool_integrations"]
            if item["kind"] == "device_adapter"
        ]
        self.assertTrue(physical, "expected physical adapter records")
        for tool in physical:
            self.assertEqual("OBSERVE_OR_SIMULATE_ONLY", tool["access_mode"], tool["tool_id"])

    def test_financial_office_has_no_transaction_capability(self) -> None:
        forbidden = {"external_payment", "transfer_funds", "execute_trade", "execute_payment"}
        financial_tools = [
            item for item in self.registry["tool_integrations"]
            if item["office_id"] == "OFF-FINANCIAL-ANALYSIS"
        ]
        for tool in financial_tools:
            self.assertTrue(forbidden.isdisjoint(tool["capabilities"]), tool["tool_id"])

    def test_every_tool_has_contract_security_and_observability(self) -> None:
        for tool in self.registry["tool_integrations"]:
            self.assertTrue(tool["contract"]["contract_id"], tool["tool_id"])
            self.assertTrue(tool["security"]["authority_ceiling"], tool["tool_id"])
            self.assertTrue(tool["security"]["egress_policy"], tool["tool_id"])
            self.assertTrue(tool["observability"]["event_names"], tool["tool_id"])


if __name__ == "__main__":
    unittest.main()
