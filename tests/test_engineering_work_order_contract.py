"""Contract and semantic safety tests for engineering work orders."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.validate_engineering_work_order import (
    deterministic_task_order,
    read_json,
    validate_work_order,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "engineering-work-order.schema.json"
EXAMPLE_PATH = ROOT / "examples" / "engineering-work-order.example.json"


class EngineeringWorkOrderContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = read_json(SCHEMA_PATH)
        cls.example = read_json(EXAMPLE_PATH)

    def test_schema_and_fixture_parse(self):
        self.assertEqual("https://json-schema.org/draft/2020-12/schema", self.schema["$schema"])
        self.assertTrue(self.schema["required"])
        self.assertIsInstance(self.example, dict)

    def test_example_passes_semantic_contract(self):
        self.assertEqual([], validate_work_order(self.example, self.schema))

    def test_order_is_deterministic_and_respects_dependencies(self):
        first = deterministic_task_order(self.example)
        second = deterministic_task_order(copy.deepcopy(self.example))
        self.assertEqual(first, second)
        self.assertLess(first.index("T-001"), first.index("T-002"))
        self.assertLess(first.index("T-002"), first.index("T-003"))

    def test_unknown_dependency_is_rejected(self):
        candidate = copy.deepcopy(self.example)
        candidate["tasks"][1]["depends_on"] = ["DOES-NOT-EXIST"]
        self.assertTrue(any("unknown dependency" in error for error in validate_work_order(candidate, self.schema)))

    def test_dependency_cycle_is_rejected(self):
        candidate = copy.deepcopy(self.example)
        candidate["tasks"][0]["depends_on"] = ["T-003"]
        errors = validate_work_order(candidate, self.schema)
        self.assertTrue(any("cycle" in error for error in errors))

    def test_duplicate_task_ids_are_rejected(self):
        candidate = copy.deepcopy(self.example)
        candidate["tasks"][1]["task_id"] = candidate["tasks"][0]["task_id"]
        errors = validate_work_order(candidate, self.schema)
        self.assertTrue(any("unique" in error for error in errors))

    def test_task_cannot_exceed_work_order_execution_mode(self):
        candidate = copy.deepcopy(self.example)
        candidate["tasks"][0]["execution_mode"] = "AUTHORIZED_EXECUTION"
        errors = validate_work_order(candidate, self.schema)
        self.assertTrue(any("exceeds work-order policy" in error for error in errors))

    def test_external_writes_require_authorized_mode_and_approval(self):
        candidate = copy.deepcopy(self.example)
        candidate["policy"]["external_writes"] = True
        errors = validate_work_order(candidate, self.schema)
        self.assertTrue(any("external_writes requires AUTHORIZED_EXECUTION" in error for error in errors))
        self.assertTrue(any("external_writes requires at least one approval reference" in error for error in errors))

    def test_network_access_requires_allowlist(self):
        candidate = copy.deepcopy(self.example)
        candidate["policy"]["network_access"] = True
        errors = validate_work_order(candidate, self.schema)
        self.assertTrue(any("allowed_domains" in error for error in errors))

    def test_active_work_rejects_unhealthy_target(self):
        candidate = copy.deepcopy(self.example)
        candidate["state"] = "QUEUED"
        candidate["federation"]["targets"][0]["connection_state"] = "DEGRADED"
        errors = validate_work_order(candidate, self.schema)
        self.assertTrue(any("requires HEALTHY target" in error for error in errors))

    def test_active_work_rejects_cross_tenant_dispatch(self):
        candidate = copy.deepcopy(self.example)
        candidate["state"] = "RUNNING"
        candidate["federation"]["targets"][0]["connection_state"] = "HEALTHY"
        candidate["federation"]["targets"][0]["tenant_id"] = "different-tenant"
        errors = validate_work_order(candidate, self.schema)
        self.assertTrue(any("tenant mismatch" in error for error in errors))

    def test_example_has_no_external_or_physical_side_effects(self):
        self.assertFalse(self.example["policy"]["external_writes"])
        self.assertFalse(self.example["policy"]["physical_actuation"])
        self.assertFalse(self.example["policy"]["network_access"])
        self.assertEqual([], self.example["federation"]["partner_refs"])


if __name__ == "__main__":
    unittest.main()
