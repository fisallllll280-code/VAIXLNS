import unittest

from experiments.microsoft_agent_framework.coordinator import (
    AgentCapability,
    PlanError,
    WorkItem,
    build_plan,
)


class MicrosoftAgentCoordinationPrototypeTests(unittest.TestCase):
    def setUp(self):
        self.agents = (
            AgentCapability("agent-research", ("research", "read_only")),
            AgentCapability("agent-review", ("review", "read_only")),
            AgentCapability("agent-writer", ("write",), ("read_only", "workspace_write")),
        )

    def test_plan_is_deterministic_and_dependency_ordered(self):
        work = (
            WorkItem("verify", "reviewer", ("review",), ("research",)),
            WorkItem("research", "investigator", ("research",)),
        )
        first = build_plan(work, self.agents)
        second = build_plan(work, self.agents)
        self.assertEqual(first, second)
        self.assertEqual([task.task_id for task in first.tasks], ["research", "verify"])
        self.assertEqual(first.mode, "PLAN_ONLY")
        self.assertEqual(len(first.plan_hash), 64)

    def test_plan_events_form_hash_chain(self):
        receipt = build_plan(
            (WorkItem("one", "researcher", ("research",)),
             WorkItem("two", "reviewer", ("review",), ("one",))),
            self.agents,
        )
        previous = "0" * 64
        for sequence, event in enumerate(receipt.events, start=1):
            self.assertEqual(event["sequence"], sequence)
            self.assertEqual(event["previous_hash"], previous)
            self.assertEqual(len(event["event_hash"]), 64)
            previous = event["event_hash"]

    def test_unknown_dependency_fails_closed(self):
        with self.assertRaisesRegex(PlanError, "UNKNOWN_DEPENDENCY"):
            build_plan((WorkItem("task", "researcher", ("research",), ("missing",)),), self.agents)

    def test_cycle_fails_closed(self):
        work = (
            WorkItem("a", "researcher", ("research",), ("b",)),
            WorkItem("b", "reviewer", ("review",), ("a",)),
        )
        with self.assertRaisesRegex(PlanError, "DEPENDENCY_CYCLE"):
            build_plan(work, self.agents)

    def test_missing_capability_fails_closed(self):
        with self.assertRaisesRegex(PlanError, "NO_ELIGIBLE_AGENT"):
            build_plan((WorkItem("task", "solver", ("quantum_computation",)),), self.agents)

    def test_external_effects_cannot_enter_plan_only_prototype(self):
        with self.assertRaisesRegex(PlanError, "EFFECT_CLASS_FORBIDDEN"):
            WorkItem("deploy", "operator", ("deploy",), effect_class="external_effect")

    def test_canonical_write_capability_is_rejected(self):
        with self.assertRaisesRegex(PlanError, "CANONICAL_WRITE_FORBIDDEN"):
            AgentCapability("unsafe", ("write",), ("read_only", "canonical_write"))

    def test_duplicate_task_ids_are_rejected(self):
        work = (
            WorkItem("same", "researcher", ("research",)),
            WorkItem("same", "reviewer", ("review",)),
        )
        with self.assertRaisesRegex(PlanError, "DUPLICATE_TASK_ID"):
            build_plan(work, self.agents)

    def test_task_assignment_is_stable_across_agent_input_order(self):
        work = (WorkItem("task", "researcher", ("research",)),)
        forward = build_plan(work, self.agents)
        reverse = build_plan(work, tuple(reversed(self.agents)))
        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
