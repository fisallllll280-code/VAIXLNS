import hashlib
import unittest

from scripts.omega_memory_task_kernel import (
    GENESIS_HASH,
    KernelError,
    build_task_plan,
    digest_json,
    evaluate_completion,
    execute_registered_task,
    recover_context,
    verify_memory_snapshot,
)


def make_memory(record_id, subject, summary, previous=GENESIS_HASH, state="IMPLEMENTED"):
    record = {
        "schema_version": "1.0.0",
        "record_id": record_id,
        "memory_type": "DECISION",
        "subject": subject,
        "summary": summary,
        "epistemic_state": state,
        "lifecycle_state": "ACTIVE",
        "provenance": {
            "repository": "fisallllll280-code/VAIXLNS",
            "revision": "a" * 40,
            "path": "docs/example.md",
            "content_sha256": hashlib.sha256(subject.encode()).hexdigest(),
        },
        "evidence": [{
            "kind": "source",
            "ref": "docs/example.md",
            "digest": hashlib.sha256(summary.encode()).hexdigest(),
        }],
        "verification": {"method": "unit-test", "result": "PASS"},
        "lineage": {"derived_from": [], "supersedes": [], "related": []},
        "recorded_at": "2026-10-10T00:00:00Z",
        "previous_record_hash": previous,
    }
    record["record_hash"] = digest_json(record)
    return record


def sample_task(task_id, *, deps=None, caps=None, source_ids=None,
                action="inspect_memory", action_type="READ_ONLY", priority="P1", input_value=None):
    return {
        "task_id": task_id,
        "title": f"Task {task_id}",
        "description": "Perform a bounded, evidence-aware operation.",
        "action": action,
        "action_type": action_type,
        "priority": priority,
        "depends_on": deps or [],
        "required_capabilities": caps or [],
        "source_memory_ids": source_ids or [],
        "acceptance_criteria": ["Output has a deterministic digest"],
        "input": input_value or {"query": "test"},
    }


class MemorySnapshotTests(unittest.TestCase):
    def test_valid_hash_chained_snapshot(self):
        first = make_memory("MEM-1", "VX runtime", "VX runtime policy gate")
        second = make_memory("MEM-2", "Memory retrieval", "recover engineering decisions",
                             previous=first["record_hash"])
        result = verify_memory_snapshot([first, second])
        self.assertTrue(result["valid"])
        self.assertEqual(result["records"], 2)
        self.assertEqual(result["head_hash"], second["record_hash"])

    def test_tampered_record_fails_closed(self):
        record = make_memory("MEM-1", "VX runtime", "VX runtime policy gate")
        record["summary"] = "modified after hashing"
        with self.assertRaisesRegex(KernelError, "hash mismatch"):
            verify_memory_snapshot([record])

    def test_duplicate_memory_id_is_rejected(self):
        first = make_memory("MEM-1", "A", "A memory item")
        second = make_memory("MEM-2", "B", "B memory item", previous=first["record_hash"])
        second["record_id"] = "MEM-1"
        unsigned = {k: v for k, v in second.items() if k != "record_hash"}
        second["record_hash"] = digest_json(unsigned)
        with self.assertRaisesRegex(KernelError, "duplicate record_id"):
            verify_memory_snapshot([first, second])

    def test_context_recovery_returns_source_provenance_and_explanation(self):
        first = make_memory("MEM-1", "VX runtime", "VX runtime policy gate")
        second = make_memory("MEM-2", "Memory retrieval", "recover engineering decisions",
                             previous=first["record_hash"])
        result = recover_context([first, second], "VX runtime", limit=5)
        self.assertEqual(result["retrieval_method"], "DETERMINISTIC_LEXICAL")
        self.assertEqual(result["matches"][0]["record_id"], "MEM-1")
        self.assertEqual(result["matches"][0]["revision"], "a" * 40)
        self.assertIn("vx", result["matches"][0]["matched_terms"])
        self.assertEqual(result["matches"][0]["evidence_refs"][0]["ref"], "docs/example.md")

    def test_no_match_does_not_fabricate_memory(self):
        record = make_memory("MEM-1", "VX runtime", "VX runtime policy gate")
        result = recover_context([record], "quantum aircraft archive", limit=5)
        self.assertEqual(result["matches"], [])
        self.assertIn("NO_MATCHING_MEMORY", result["empty_reason"])

    def test_empty_query_is_rejected(self):
        with self.assertRaisesRegex(KernelError, "query must be non-empty"):
            recover_context([], "   ")


class TaskPlanningTests(unittest.TestCase):
    def test_dependency_aware_deterministic_plan(self):
        tasks = [
            sample_task("TASK-C", deps=["TASK-B"], priority="P0"),
            sample_task("TASK-B", deps=["TASK-A"], priority="P0"),
            sample_task("TASK-A", priority="P2"),
        ]
        result = build_task_plan("recover context, then execute safe analysis", tasks)
        ids = [task["task_id"] for task in result["tasks"]]
        self.assertEqual(ids, ["TASK-A", "TASK-B", "TASK-C"])
        self.assertEqual(result["tasks"][0]["status"], "READY")
        self.assertEqual(result["tasks"][1]["status"], "READY")
        self.assertEqual(result["tasks"][2]["status"], "READY")
        repeat = build_task_plan("recover context, then execute safe analysis", tasks)
        self.assertEqual(result["plan_id"], repeat["plan_id"])
        self.assertEqual(result["plan_digest"], repeat["plan_digest"])

    def test_missing_dependency_is_rejected(self):
        with self.assertRaisesRegex(KernelError, "missing dependencies"):
            build_task_plan("goal", [sample_task("TASK-A", deps=["NOT-THERE"])])

    def test_dependency_cycle_is_rejected(self):
        tasks = [
            sample_task("TASK-A", deps=["TASK-B"]),
            sample_task("TASK-B", deps=["TASK-A"]),
        ]
        with self.assertRaisesRegex(KernelError, "dependency cycle"):
            build_task_plan("goal", tasks)

    def test_unavailable_capability_blocks_task(self):
        task = sample_task("TASK-A", caps=["repo.write"])
        result = build_task_plan("goal", [task], available_capabilities=[])
        self.assertEqual(result["tasks"][0]["status"], "BLOCKED")
        self.assertEqual(result["tasks"][0]["missing_capabilities"], ["repo.write"])

    def test_task_requiring_missing_recovered_memory_is_blocked(self):
        task = sample_task("TASK-A", source_ids=["MEM-NOT-RECOVERED"])
        result = build_task_plan("goal", [task], recovered_memory_ids=[])
        self.assertEqual(result["tasks"][0]["status"], "BLOCKED")
        self.assertEqual(result["tasks"][0]["missing_memory_ids"], ["MEM-NOT-RECOVERED"])

    def test_external_effect_never_enters_ready_state(self):
        task = sample_task("TASK-A", action_type="EXTERNAL_EFFECT")
        result = build_task_plan("goal", [task])
        self.assertEqual(result["tasks"][0]["status"], "BLOCKED")
        self.assertFalse(result["execution_policy"]["external_effects_enabled"])


class ExecutionAndAdmissionTests(unittest.TestCase):
    def test_dry_run_does_not_call_handler(self):
        calls = []
        task = sample_task("TASK-A", input_value={"x": 1})
        result = execute_registered_task(
            task,
            handler_registry={"inspect_memory": lambda data: calls.append(data)},
            dry_run=True,
        )
        self.assertEqual(result["status"], "PLAN_ONLY")
        self.assertEqual(calls, [])

    def test_missing_capability_holds_execution(self):
        task = sample_task("TASK-A", caps=["memory.read"])
        result = execute_registered_task(
            task,
            handler_registry={"inspect_memory": lambda data: {"ok": True}},
            granted_capabilities=[],
            dry_run=False,
        )
        self.assertEqual(result["status"], "HELD")
        self.assertEqual(result["reason"], "CAPABILITY_NOT_GRANTED")

    def test_registered_handler_executes_and_result_stays_unverified(self):
        task = sample_task("TASK-A", caps=["memory.read"], input_value={"query": "VX"})
        result = execute_registered_task(
            task,
            handler_registry={"inspect_memory": lambda data: {"query": data["query"], "count": 1}},
            granted_capabilities=["memory.read"],
            dry_run=False,
        )
        self.assertEqual(result["status"], "COMPLETED")
        self.assertRegex(result["output_digest"], r"^[0-9a-f]{64}$")
        self.assertEqual(result["verification_state"], "NOT_VERIFIED")

    def test_external_effect_is_rejected_even_if_handler_exists(self):
        task = sample_task("TASK-A", action_type="EXTERNAL_EFFECT")
        result = execute_registered_task(
            task,
            handler_registry={"inspect_memory": lambda data: {"done": True}},
            granted_capabilities=["all"],
            dry_run=False,
            authorization_ref="decision://test/1",
        )
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(result["reason"], "EXTERNAL_EFFECT_DISABLED_BY_KERNEL")

    def test_sandbox_mutation_requires_decision_reference(self):
        task = sample_task("TASK-A", action_type="SANDBOX_MUTATION")
        result = execute_registered_task(
            task,
            handler_registry={"inspect_memory": lambda data: {"done": True}},
            granted_capabilities=[],
            dry_run=False,
        )
        self.assertEqual(result["status"], "HELD")
        self.assertEqual(result["reason"], "SANDBOX_MUTATION_REQUIRES_AUTHORIZATION_REFERENCE")

    def test_handler_exception_becomes_failure_not_success(self):
        def fail(_data):
            raise RuntimeError("controlled test failure")
        task = sample_task("TASK-A")
        result = execute_registered_task(
            task, handler_registry={"inspect_memory": fail}, dry_run=False,
        )
        self.assertEqual(result["status"], "FAILED")
        self.assertEqual(result["error_type"], "RuntimeError")
        self.assertEqual(result["verification_state"], "NOT_VERIFIED")

    def test_completion_is_held_until_independent_evidence(self):
        task = sample_task("TASK-A")
        raw_result = {"status": "COMPLETED", "verification_state": "NOT_VERIFIED"}
        held = evaluate_completion(
            task, raw_result, independent_verifier_id="reviewer",
            producer_id="builder", source_revision="a" * 40,
            evidence_digest="b" * 64, reproduction_command="python -m unittest",
            independent_check_passed=True,
        )
        self.assertEqual(held["decision"], "HOLD")
        self.assertEqual(held["epistemic_state"], "PARTIAL")

    def test_same_producer_and_verifier_cannot_promote(self):
        task = sample_task("TASK-A")
        accepted = evaluate_completion(
            task, {"status": "COMPLETED", "verification_state": "INDEPENDENTLY_VERIFIED"},
            independent_verifier_id="builder", producer_id="builder",
            source_revision="a" * 40, evidence_digest="b" * 64,
            reproduction_command="python -m unittest", independent_check_passed=True,
        )
        self.assertEqual(accepted["decision"], "HOLD")
        self.assertIn("producer/verifier separation-of-duties violated", accepted["blockers"])

    def test_completion_gate_accepts_complete_independent_proof_bundle(self):
        task = sample_task("TASK-A")
        result = evaluate_completion(
            task, {"status": "COMPLETED", "verification_state": "INDEPENDENTLY_VERIFIED"},
            independent_verifier_id="independent-reviewer", producer_id="builder",
            source_revision="a" * 40, evidence_digest="b" * 64,
            reproduction_command="python -m unittest tests.test_omega_memory_task_kernel -v",
            independent_check_passed=True,
        )
        self.assertEqual(result["decision"], "ACCEPT")
        self.assertEqual(result["epistemic_state"], "VERIFIED")
        self.assertEqual(result["promotion_authority"], "SEPARATE_CANONICAL_GOVERNANCE_REQUIRED")


if __name__ == "__main__":
    unittest.main()
