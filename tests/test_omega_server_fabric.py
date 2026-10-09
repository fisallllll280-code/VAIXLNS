"""Tests for policy-constrained Ω server placement planning."""
from __future__ import annotations

import copy
import unittest

from scripts.omega_server_fabric import (
    MANIFEST_SCHEMA,
    TASKS_SCHEMA,
    build_plan,
    sha256_json,
)


def pool(pool_id, task_types, *, classification="RESTRICTED", egress="DENY_BY_DEFAULT",
         isolated=True, gpu=False, state="NOT_PROVISIONED", cpu=4, memory=16, parallel=2):
    return {
        "pool_id": pool_id,
        "plane": "TEST",
        "task_types": task_types,
        "capabilities": ["tests"],
        "max_data_classification": classification,
        "isolated_execution": isolated,
        "network_egress_policy": egress,
        "operational_state": state,
        "provider": "NOT_CONFIGURED",
        "region": "NOT_CONFIGURED",
        "endpoint": None,
        "max_parallel_tasks": parallel,
        "capacity_estimate": {
            "cpu_units_per_task": cpu,
            "memory_gib_per_task": memory,
            "gpu_capable": gpu,
            "estimate_state": "TEST_FIXTURE_NOT_BENCHMARKED",
        },
    }


def task(task_id, task_type, *, classification="INTERNAL", isolated=True,
         gpu=False, cpu=1, memory=1, priority=50):
    return {
        "task_id": task_id,
        "task_type": task_type,
        "priority": priority,
        "data_classification": classification,
        "requires_isolation": isolated,
        "requires_gpu": gpu,
        "estimated_cpu_units": cpu,
        "estimated_memory_gib": memory,
    }


def inputs(pools, tasks):
    return (
        {"schema": MANIFEST_SCHEMA, "control_mode": "PLAN_ONLY",
         "policy_version": "TEST-1", "server_pools": pools},
        {"schema": TASKS_SCHEMA, "tasks": tasks},
    )


class OmegaServerFabricTests(unittest.TestCase):
    def test_unprovisioned_pool_is_proposed_but_never_dispatched(self):
        manifest, workload = inputs([pool("local-cpu", ["UNIT_TEST"])],
                                    [task("T-1", "UNIT_TEST")])
        plan = build_plan(manifest, workload)
        placement = plan["placements"][0]
        self.assertEqual(placement["placement_state"], "PROPOSED_UNPROVISIONED")
        self.assertEqual(placement["dispatch_state"], "NOT_DISPATCHED")
        self.assertEqual(plan["summary"]["dispatched_count"], 0)
        self.assertFalse(plan["safety"]["source_code_executed"])

    def test_restricted_data_never_routes_to_public_only_pool(self):
        pools = [
            pool("local-private", ["PRIVATE_SOURCE_RESEARCH"], classification="RESTRICTED"),
            pool("public-burst", ["PRIVATE_SOURCE_RESEARCH"], classification="PUBLIC",
                 egress="ALLOWLIST_ONLY"),
        ]
        manifest, workload = inputs(pools, [task("T-PRIVATE", "PRIVATE_SOURCE_RESEARCH",
                                                    classification="RESTRICTED")])
        placement = build_plan(manifest, workload)["placements"][0]
        self.assertEqual(placement["recommended_pool_id"], "local-private")
        self.assertNotIn("public-burst", placement["eligible_candidates"])

    def test_confidential_task_rejects_allowlist_egress(self):
        manifest, workload = inputs([
            pool("cloud-allowlist", ["SECURITY_SCAN"], egress="ALLOWLIST_ONLY")
        ], [task("T-SECRET", "SECURITY_SCAN", classification="CONFIDENTIAL")])
        placement = build_plan(manifest, workload)["placements"][0]
        self.assertEqual(placement["placement_state"], "BLOCKED_NO_COMPATIBLE_POOL")
        self.assertIn("CONFIDENTIAL_TASK_REQUIRES_EGRESS_DENY",
                      placement["rejected_pools"][0]["reasons"])

    def test_gpu_workload_requires_gpu_capable_pool(self):
        pools = [
            pool("cpu-only", ["MODEL_INFERENCE"], gpu=False),
            pool("gpu-node", ["MODEL_INFERENCE"], gpu=True),
        ]
        manifest, workload = inputs(pools, [task("T-GPU", "MODEL_INFERENCE", gpu=True)])
        placement = build_plan(manifest, workload)["placements"][0]
        self.assertEqual(placement["recommended_pool_id"], "gpu-node")

    def test_capacity_mismatch_blocks_pool(self):
        manifest, workload = inputs([
            pool("small", ["NUMERICAL_SIMULATION"], cpu=1, memory=1)
        ], [task("T-LARGE", "NUMERICAL_SIMULATION", cpu=4, memory=16)])
        placement = build_plan(manifest, workload)["placements"][0]
        self.assertEqual(placement["placement_state"], "BLOCKED_NO_COMPATIBLE_POOL")
        self.assertIn("CPU_CAPACITY_INSUFFICIENT", placement["rejected_pools"][0]["reasons"])
        self.assertIn("MEMORY_CAPACITY_INSUFFICIENT", placement["rejected_pools"][0]["reasons"])

    def test_no_matching_task_type_fails_closed(self):
        manifest, workload = inputs([pool("indexer", ["INDEX_QUERY"])],
                                    [task("T-UNKNOWN", "UNSUPPORTED")])
        placement = build_plan(manifest, workload)["placements"][0]
        self.assertIsNone(placement["recommended_pool_id"])
        self.assertEqual(placement["dispatch_state"], "NOT_DISPATCHED")

    def test_duplicate_ids_are_rejected(self):
        manifest, workload = inputs([pool("cpu", ["UNIT_TEST"])],
                                    [task("T-1", "UNIT_TEST"), task("T-1", "UNIT_TEST")])
        with self.assertRaisesRegex(ValueError, "task_id values must be unique"):
            build_plan(manifest, workload)

    def test_manifest_rejects_live_endpoint_in_plan_only_mode(self):
        manifest, workload = inputs([pool("cpu", ["UNIT_TEST"])],
                                    [task("T-1", "UNIT_TEST")])
        manifest["server_pools"][0]["endpoint"] = "https://example.invalid"
        with self.assertRaisesRegex(ValueError, "must not contain live endpoints"):
            build_plan(manifest, workload)

    def test_innovation_index_is_translated_to_internal_server_tasks(self):
        from scripts.omega_server_fabric import workload_from_innovation_network

        network = {
            "schema": "vaixlns.innovation-network.v1",
            "network_sha256": "a" * 64,
            "work_packets": [{
                "innovation_id": "INNOVATION-1",
                "priority_score": 90,
                "research_lanes": [
                    {"task_id": "TASK-A", "lane": "SOURCE_DISCOVERY",
                     "objective": "Locate primary sources",
                     "input_refs": ["INNOVATION-1"], "required_outputs": ["sources.json"]},
                    {"task_id": "TASK-B", "lane": "TEST_REPLAY",
                     "objective": "Reproduce the claim",
                     "input_refs": ["INNOVATION-1"], "required_outputs": ["receipt.json"]},
                ],
            }],
        }
        workload = workload_from_innovation_network(network)
        self.assertEqual(workload["task_count"], 2)
        self.assertEqual(workload["tasks"][0]["data_classification"], "INTERNAL")
        self.assertEqual(workload["tasks"][0]["task_type"], "PRIVATE_SOURCE_RESEARCH")
        self.assertEqual(workload["dispatch_state"], "NOT_DISPATCHED")
        plan = build_plan({
            "schema": MANIFEST_SCHEMA, "control_mode": "PLAN_ONLY",
            "server_pools": [pool("local-research", ["PRIVATE_SOURCE_RESEARCH"]),
                             pool("cpu", ["UNIT_TEST"])],
        }, workload)
        by_id = {item["task_id"]: item for item in plan["placements"]}
        self.assertEqual(by_id["TASK-A"]["recommended_pool_id"], "local-research")
        self.assertEqual(by_id["TASK-B"]["recommended_pool_id"], "cpu")
        self.assertEqual(plan["summary"]["dispatched_count"], 0)

    def test_unknown_innovation_lane_fails_closed(self):
        from scripts.omega_server_fabric import workload_from_innovation_network

        network = {
            "schema": "vaixlns.innovation-network.v1",
            "work_packets": [{
                "innovation_id": "INNOVATION-2",
                "research_lanes": [{"task_id": "TASK-X", "lane": "UNREGISTERED_LANE"}],
            }],
        }
        with self.assertRaisesRegex(ValueError, "no server capability mapping"):
            workload_from_innovation_network(network)

    def test_integration_gap_graph_becomes_review_tasks(self):
        from scripts.omega_server_fabric import workload_from_integration_graph

        graph = {
            "schema": "vaixlns.omega-innovation-integration-graph.v1",
            "graph_sha256": "b" * 64,
            "integration_gaps": [
                {"gap_type": "DECLARED_EVIDENCE_PATH_UNRESOLVED",
                 "node_id": "innovation:A", "reference": "missing.py", "severity": "REVIEW"},
                {"gap_type": "DECLARED_DERIVATION_CYCLE",
                 "node_id": "innovation:A", "severity": "BLOCK_REVIEW"},
            ],
        }
        workload = workload_from_integration_graph(graph)
        self.assertEqual(workload["task_count"], 2)
        self.assertTrue(all(t["data_classification"] == "INTERNAL" for t in workload["tasks"]))
        self.assertEqual(workload["dispatch_state"], "NOT_DISPATCHED")
        plan = build_plan({
            "schema": MANIFEST_SCHEMA, "control_mode": "PLAN_ONLY",
            "server_pools": [
                pool("research", ["PRIVATE_SOURCE_RESEARCH"]),
                pool("verify", ["INDEPENDENT_VERIFY"]),
            ],
        }, workload)
        by_type = {item["task_type"]: item for item in plan["placements"]}
        self.assertEqual(by_type["PRIVATE_SOURCE_RESEARCH"]["recommended_pool_id"], "research")
        self.assertEqual(by_type["INDEPENDENT_VERIFY"]["recommended_pool_id"], "verify")
        self.assertEqual(plan["summary"]["dispatched_count"], 0)

    def test_combined_workloads_reject_duplicate_task_ids(self):
        from scripts.omega_server_fabric import combine_workloads

        sample = {"schema": TASKS_SCHEMA, "source_schema": "test", "tasks": [{"task_id": "DUP"}]}
        with self.assertRaisesRegex(ValueError, "duplicate task_id"):
            combine_workloads([sample, sample])

    def test_plan_is_deterministic_and_hash_is_correct(self):
        manifest, workload = inputs([
            pool("cpu-b", ["UNIT_TEST"]),
            pool("cpu-a", ["UNIT_TEST"]),
        ], [task("T-2", "UNIT_TEST"), task("T-1", "UNIT_TEST")])
        first = build_plan(manifest, workload)
        second = build_plan(copy.deepcopy(manifest), copy.deepcopy(workload))
        self.assertEqual(first, second)
        self.assertEqual(first["plan_sha256"], sha256_json({
            key: value for key, value in first.items() if key != "plan_sha256"
        }))


if __name__ == "__main__":
    unittest.main()
