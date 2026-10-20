import unittest

from scripts.continuous_promotion_gate import build_plan, evaluate_pull_request


def passing_pr(**updates):
    pr = {
        "number": 7,
        "title": "A reviewed change",
        "url": "https://github.com/fisallllll280-code/VAIXLNS/pull/7",
        "isDraft": False,
        "reviewDecision": "APPROVED",
        "mergeable": "MERGEABLE",
        "baseRefName": "main",
        "headRefOid": "a" * 40,
        "statusCheckRollup": [
            {
                "__typename": "CheckRun",
                "name": "unit-tests",
                "status": "COMPLETED",
                "conclusion": "SUCCESS",
            },
            {
                "__typename": "StatusContext",
                "context": "security/audit",
                "state": "SUCCESS",
            },
        ],
    }
    pr.update(updates)
    return pr


class ContinuousPromotionGateTests(unittest.TestCase):
    def test_approved_ready_pr_passes(self):
        result = evaluate_pull_request(passing_pr())
        self.assertEqual(result["decision"], "READY_TO_MERGE")
        self.assertEqual(result["reasons"], [])
        self.assertEqual(result["head_sha"], "a" * 40)

    def test_draft_is_held_even_when_checks_pass(self):
        result = evaluate_pull_request(passing_pr(isDraft=True))
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("PULL_REQUEST_IS_DRAFT_OR_DRAFT_STATE_UNKNOWN", result["reasons"])

    def test_human_approval_is_mandatory(self):
        result = evaluate_pull_request(passing_pr(reviewDecision="REVIEW_REQUIRED"))
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("HUMAN_REVIEW_APPROVAL_REQUIRED", result["reasons"])

    def test_absent_checks_fail_closed(self):
        result = evaluate_pull_request(passing_pr(statusCheckRollup=[]))
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("NO_CHECK_RESULTS_FOUND", result["reasons"])

    def test_failed_check_holds_pr(self):
        pr = passing_pr(statusCheckRollup=[{
            "__typename": "CheckRun",
            "name": "integration",
            "status": "COMPLETED",
            "conclusion": "FAILURE",
        }])
        result = evaluate_pull_request(pr)
        self.assertEqual(result["decision"], "HOLD")
        self.assertTrue(any(reason.startswith("CHECK_NOT_SUCCESSFUL:integration") for reason in result["reasons"]))

    def test_in_progress_check_holds_pr(self):
        pr = passing_pr(statusCheckRollup=[{
            "__typename": "CheckRun",
            "name": "integration",
            "status": "IN_PROGRESS",
            "conclusion": None,
        }])
        result = evaluate_pull_request(pr)
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("CHECK_NOT_COMPLETED:integration", result["reasons"])

    def test_non_mergeable_pr_is_held(self):
        result = evaluate_pull_request(passing_pr(mergeable="CONFLICTING"))
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("PULL_REQUEST_NOT_CONFIRMED_MERGEABLE", result["reasons"])

    def test_only_main_is_promotable(self):
        result = evaluate_pull_request(passing_pr(baseRefName="release"))
        self.assertEqual(result["decision"], "HOLD")
        self.assertIn("BASE_BRANCH_NOT_MAIN", result["reasons"])

    def test_unknown_check_type_is_held(self):
        result = evaluate_pull_request(passing_pr(statusCheckRollup=[{
            "__typename": "FutureCheckType",
            "name": "new-provider",
        }]))
        self.assertEqual(result["decision"], "HOLD")
        self.assertTrue(any(reason.startswith("UNKNOWN_CHECK_TYPE:new-provider") for reason in result["reasons"]))

    def test_plan_sorts_prs_and_lists_only_eligible_numbers(self):
        plan = build_plan([passing_pr(number=9), passing_pr(number=3, isDraft=True)])
        self.assertEqual(plan["eligible_pr_numbers"], [9])
        self.assertEqual(plan["summary"]["pull_requests_seen"], 2)
        self.assertEqual(plan["summary"]["ready_to_merge"], 1)
        self.assertEqual(plan["summary"]["held"], 1)
        self.assertEqual(plan["pull_requests"][0]["number"], 3)

    def test_malformed_input_fails_closed(self):
        with self.assertRaises(ValueError):
            build_plan({"number": 7})


if __name__ == "__main__":
    unittest.main()
