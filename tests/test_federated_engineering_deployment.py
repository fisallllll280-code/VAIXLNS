import unittest

from scripts.federated_engineering_deployment import build_plan, choose_worker, validate_manifest


MANIFEST = {
    "schema": "vaixlns.federated-engineering-deployment.v1",
    "version": 1,
    "authority": "VAIXLNS",
    "mode": "PLAN_ONLY",
    "defaults": {
        "execution_enabled": False,
        "automatic_production_deployment": False,
        "max_parallel_system_rollouts": 4,
    },
    "release_gates": ["PINNED_SOURCE_REVISION", "BUILD_AND_TEST_PASS", "SEPARATE_GOVERNANCE_ADMISSION"],
    "systems": [
        {
            "system_id": "VAIXLNS",
            "role": "control-plane",
            "identity_status": "VERIFIED",
            "depends_on": [],
            "repositories": [{"full_name": "owner/VAIXLNS"}],
        },
        {
            "system_id": "VX",
            "role": "execution-runtime",
            "identity_status": "VERIFIED",
            "depends_on": ["VAIXLNS"],
            "repositories": [{"full_name": "owner/VX-runtime"}, {"full_name": "owner/VX-build"}],
        },
        {
            "system_id": "VLNS",
            "role": "knowledge-discovery",
            "identity_status": "UNVERIFIED",
            "depends_on": ["VAIXLNS"],
            "repositories": [{"full_name": "owner/NAXLNS"}],
        },
        {
            "system_id": "NEXNET",
            "role": "discovery-network",
            "identity_status": "UNVERIFIED",
            "depends_on": ["VAIXLNS"],
            "repositories": [{"full_name": "owner/NEXENT"}],
        },
    ],
}


class FederatedEngineeringDeploymentTests(unittest.TestCase):
    def test_plan_is_deterministic_and_never_authorizes_execution(self):
        first = build_plan(MANIFEST, environment="sandbox")
        second = build_plan(MANIFEST, environment="sandbox")
        self.assertEqual(first, second)
        self.assertEqual(first["target_system_count"], 4)
        self.assertFalse(first["execution_authorized"])
        self.assertTrue(all(not row["execution_authorized"] for row in first["systems"]))

    def test_unverified_system_identity_is_held_not_skipped(self):
        plan = build_plan(MANIFEST)
        rows = {row["system_id"]: row for row in plan["systems"]}
        self.assertEqual(rows["VLNS"]["status"], "HOLD")
        self.assertEqual(rows["NEXNET"]["status"], "HOLD")
        self.assertIn("SYSTEM_IDENTITY_NOT_VERIFIED", rows["VLNS"]["blockers"])

    def test_verified_systems_are_scheduled_in_dependency_waves(self):
        plan = build_plan(MANIFEST)
        rows = {row["system_id"]: row for row in plan["systems"]}
        self.assertEqual(rows["VAIXLNS"]["rollout_wave"], 1)
        self.assertEqual(rows["VX"]["rollout_wave"], 2)
        self.assertTrue(all(not wave["execution_started"] for wave in plan["waves"]))

    def test_production_is_always_held_by_reference_planner(self):
        plan = build_plan(MANIFEST, environment="production")
        self.assertEqual(plan["plan_ready_count"], 0)
        self.assertEqual(plan["held_count"], 4)
        self.assertTrue(all(row["status"] == "HOLD" for row in plan["systems"]))

    def test_dependency_cycle_is_rejected(self):
        broken = {
            **MANIFEST,
            "systems": [
                {**MANIFEST["systems"][0], "depends_on": ["VX"]},
                MANIFEST["systems"][1],
                MANIFEST["systems"][2],
                MANIFEST["systems"][3],
            ],
        }
        with self.assertRaisesRegex(ValueError, "DEPENDENCY_CYCLE"):
            validate_manifest(broken)

    def test_duplicate_system_identity_is_rejected(self):
        broken = {**MANIFEST, "systems": MANIFEST["systems"] + [MANIFEST["systems"][0]]}
        with self.assertRaisesRegex(ValueError, "DUPLICATE_SYSTEM_ID"):
            validate_manifest(broken)

    def test_execution_enablement_cannot_be_flipped_on(self):
        broken = {**MANIFEST, "defaults": {**MANIFEST["defaults"], "execution_enabled": True}}
        with self.assertRaisesRegex(ValueError, "MUST_NOT_ENABLE_EXECUTION"):
            validate_manifest(broken)

    def test_low_latency_selection_still_obeys_authority_and_identity_gates(self):
        task = {
            "capability": "engineering-deploy-plan",
            "authority_scope": "sandbox-plan",
            "data_classification": "PUBLIC",
            "risk": "LOW",
            "read_only": True,
            "idempotent": True,
            "side_effects": False,
        }
        workers = [
            {
                "worker_id": "fast-but-unauthorized",
                "identity_status": "VERIFIED",
                "state": "ACTIVE",
                "capabilities": ["engineering-deploy-plan"],
                "authority_scopes": [],
                "allowed_data_classifications": ["PUBLIC"],
                "service_p95_ms": 1,
            },
            {
                "worker_id": "unverified-fast",
                "identity_status": "UNVERIFIED",
                "state": "ACTIVE",
                "capabilities": ["engineering-deploy-plan"],
                "authority_scopes": ["sandbox-plan"],
                "allowed_data_classifications": ["PUBLIC"],
                "service_p95_ms": 2,
            },
            {
                "worker_id": "eligible-worker",
                "identity_status": "VERIFIED",
                "state": "ACTIVE",
                "capabilities": ["engineering-deploy-plan"],
                "authority_scopes": ["sandbox-plan"],
                "allowed_data_classifications": ["PUBLIC"],
                "queue_depth": 1,
                "queue_wait_ms": 5,
                "service_p95_ms": 20,
                "network_penalty_ms": 3,
            },
        ]
        result = choose_worker(task, workers)
        self.assertEqual(result["selected_worker_id"], "eligible-worker")
        self.assertEqual(result["route_class"], "FAST_PATH")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["estimated_completion_ms"], 28)

    def test_missing_authority_has_no_eligible_worker(self):
        result = choose_worker(
            {"capability": "code", "authority_scope": "prod", "data_classification": "PUBLIC"},
            [{
                "worker_id": "sandbox-only",
                "identity_status": "VERIFIED",
                "state": "ACTIVE",
                "capabilities": ["code"],
                "authority_scopes": ["sandbox"],
                "allowed_data_classifications": ["PUBLIC"],
                "service_p95_ms": 5,
            }],
        )
        self.assertEqual(result["status"], "HOLD_NO_ELIGIBLE_WORKER")
        self.assertIsNone(result["selected_worker_id"])


if __name__ == "__main__":
    unittest.main()
