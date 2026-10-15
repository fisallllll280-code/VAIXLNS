import unittest

from agents.runtime_supervisor import RuntimeHold, RuntimePolicy, RuntimeSupervisor


class EchoAdapter:
    def execute(self, task):
        return {"summary": "bounded proposal", "promotion": "VERIFIED"}


def valid_task(**overrides):
    task = {
        "task_id": "task-001",
        "agent_id": "AG-01-SOURCE-DISCOVERY",
        "adapter_id": "test-echo",
        "operation": "RESEARCH",
        "input": {"query": "inspect source"},
        "evidence_refs": ["sha256:example-source-digest"],
    }
    task.update(overrides)
    return task


class RuntimeSupervisorTests(unittest.TestCase):
    def test_dispatch_returns_proposal_not_worker_authority(self):
        supervisor = RuntimeSupervisor({"test-echo": EchoAdapter()})
        result = supervisor.dispatch(valid_task())
        self.assertEqual(result["status"], "PROPOSED")
        self.assertEqual(result["promotion"], "NOT_PERMITTED")
        self.assertFalse(result["canonical_write"])
        self.assertEqual(result["result"]["promotion"], "VERIFIED")

    def test_unknown_adapter_holds_without_execution(self):
        supervisor = RuntimeSupervisor()
        with self.assertRaisesRegex(RuntimeHold, "ADAPTER_NOT_CONFIGURED_HOLD"):
            supervisor.dispatch(valid_task())

    def test_production_mutation_is_denied(self):
        supervisor = RuntimeSupervisor({"test-echo": EchoAdapter()})
        with self.assertRaisesRegex(RuntimeHold, "OPERATION_DENIED"):
            supervisor.dispatch(valid_task(operation="PRODUCTION_MUTATE"))

    def test_agent_cannot_self_promote_or_write_canonical_state(self):
        supervisor = RuntimeSupervisor({"test-echo": EchoAdapter()})
        with self.assertRaisesRegex(RuntimeHold, "AGENT_AUTHORITY_ESCALATION_DENIED"):
            supervisor.dispatch(valid_task(may_promote=True))

    def test_research_requires_evidence(self):
        supervisor = RuntimeSupervisor({"test-echo": EchoAdapter()})
        with self.assertRaisesRegex(RuntimeHold, "EVIDENCE_REQUIRED_HOLD"):
            supervisor.dispatch(valid_task(evidence_refs=[]))

    def test_dispatch_budget_is_bounded(self):
        supervisor = RuntimeSupervisor(
            {"test-echo": EchoAdapter()}, RuntimePolicy(max_tasks=1)
        )
        supervisor.dispatch(valid_task())
        with self.assertRaisesRegex(RuntimeHold, "TASK_BUDGET_EXCEEDED"):
            supervisor.dispatch(valid_task(task_id="task-002"))

    def test_missing_task_identity_is_rejected(self):
        supervisor = RuntimeSupervisor({"test-echo": EchoAdapter()})
        with self.assertRaisesRegex(RuntimeHold, "REQUIRED_TASK_FIELD_MISSING"):
            supervisor.dispatch(valid_task(agent_id=""))


if __name__ == "__main__":
    unittest.main()
