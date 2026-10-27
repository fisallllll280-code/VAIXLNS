"""Fail-closed federation planning tests: no network, API keys, or source system writes."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools/plan_universal_federation.py"
spec = importlib.util.spec_from_file_location("federation_plan", MODULE)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class FederationPlanTests(unittest.TestCase):
    def setUp(self):
        self.catalog = {
            "github": {"family": "REPOSITORY", "sync": "webhook_plus_reconcile"},
            "chatgpt_personal_export": {"family": "CHAT", "sync": "manual_snapshot"},
            "model_provider": {"family": "MODEL", "sync": "capability_discovery_and_live_smoke"},
            "google_drive": {"family": "DOCUMENTS", "sync": "cursor_plus_notifications"},
        }
        self.record = {"alias": "personal_chat_01", "source_class": "chatgpt_personal_export",
                       "authorization": "DECLARED", "classification": "RESTRICTED"}
        self.manifest = {"schema": "VAIXLNS.AccountSourceManifest.v1", "accounts": [self.record]}

    def test_unapproved_source_never_executes(self):
        plan = subject.compose_plan(self.manifest, self.catalog)
        self.assertEqual(plan["mode"], "OFFLINE_PLAN_ONLY")
        self.assertEqual(plan["admitted"], 0)
        self.assertEqual(plan["systems"][0]["admission"], "BLOCKED")
        self.assertEqual(plan["systems"][0]["execution"], "NOT_RUN")
        self.assertEqual(plan["systems"][0]["data_policy"], "NO_PUBLIC_RAW_CONTENT")

    def test_separate_accounts_same_provider(self):
        items = [dict(self.record), dict(self.record, alias="personal_chat_02")]
        plan = subject.compose_plan(dict(self.manifest, accounts=items), self.catalog)
        self.assertEqual(plan["source_system_count"], 2)
        self.assertNotEqual(plan["systems"][0]["account_alias"], plan["systems"][1]["account_alias"])

    def test_duplicates_rejected(self):
        with self.assertRaises(subject.FederationError):
            subject.compose_plan(dict(self.manifest, accounts=[self.record, self.record]), self.catalog)

    def test_authorization_must_have_evidence(self):
        record = dict(self.record, authorization="AUTHORIZED", source_owner_approved=True)
        with self.assertRaises(subject.FederationError):
            subject.compose_plan(dict(self.manifest, accounts=[record]), self.catalog)

    def test_authorized_is_not_live_activated(self):
        record = dict(self.record, authorization="AUTHORIZED", source_owner_approved=True,
                      permission_evidence=["private-review-002"])
        plan = subject.compose_plan(dict(self.manifest, accounts=[record]), self.catalog)
        self.assertEqual(plan["systems"][0]["connector_live_status"], "NOT_TESTED")
        self.assertEqual(plan["systems"][0]["stages"][-1]["state"], "BLOCKED_PENDING_INDEPENDENT_ADMISSION")
        self.assertEqual(plan["admitted"], 0)

    def test_credential_named_fields_rejected(self):
        record = dict(self.record, api_key="secret-value")
        with self.assertRaises(subject.FederationError):
            subject.compose_plan(dict(self.manifest, accounts=[record]), self.catalog)

    def test_alias_must_not_be_email(self):
        record = dict(self.record, alias="example@gmail.com")
        with self.assertRaises(subject.FederationError):
            subject.compose_plan(dict(self.manifest, accounts=[record]), self.catalog)

    def test_unknown_source_class_fail_closed(self):
        record = dict(self.record, source_class="unknown_platform")
        with self.assertRaises(subject.FederationError):
            subject.compose_plan(dict(self.manifest, accounts=[record]), self.catalog)

    def test_deterministic_report_independent_of_entry_order(self):
        second = dict(self.record, alias="second_account")
        first = subject.compose_plan(dict(self.manifest, accounts=[self.record, second]), self.catalog)
        other = subject.compose_plan(dict(self.manifest, accounts=[second, self.record]), self.catalog)
        self.assertEqual(first["systems"], other["systems"])
        self.assertNotEqual(first["source_manifest_digest_sha256"], other["source_manifest_digest_sha256"])

    def test_revoke_blocks(self):
        record = dict(self.record, authorization="REVOKED")
        plan = subject.compose_plan(dict(self.manifest, accounts=[record]), self.catalog)
        self.assertEqual(plan["systems"][0]["stages"][2]["state"], "BLOCKED")

    def test_reject_sensitive_nested_values(self):
        record = dict(self.record, scope_summary={"auth_token": "xyz"})
        with self.assertRaises(subject.FederationError):
            subject.compose_plan(dict(self.manifest, accounts=[record]), self.catalog)

if __name__ == "__main__":
    unittest.main()
