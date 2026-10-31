from dataclasses import replace
from datetime import datetime, timedelta, timezone
import http.client
import json
import os
import sqlite3
import tempfile
import threading
import unittest

from tools.gr8r_adapter.adapter import authorize_proposal, create_server, intake
from vcre.agent_orchestration import AuthorityGrant, OrchestrationError, TaskEnvelope, TaskState, canonical_fingerprint

SAMPLE = {'task_id': 'demo', 'title': 'Review proposal', 'source': 'gr8r', 'requested_action': 'propose'}


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime.now(timezone.utc)
        self.grant = AuthorityGrant('test-grant', 'test-principal', frozenset({'gr8r:review-proposal'}), frozenset({'gr8r:demo'}), self.now-timedelta(seconds=1), self.now+timedelta(minutes=1))
        self.envelope = TaskEnvelope('gr8r:demo', 'test-run', 'test-candidate', canonical_fingerprint(SAMPLE), 'test-revision', 'INTEGRATION_ENGINEER', 'test-principal', ('gr8r:review-proposal',), ('test-source',), 'gr8r-review.v1', ('source-digest',), 1000, 1, 1, (), 'test-grant', self.grant.issued_at, self.grant.expires_at, 'test-idempotency-001', 'gr8r:demo')

    def authorize(self, envelope=None, grant=None, principal='test-principal', capabilities=('gr8r:review-proposal',)):
        return authorize_proposal(SAMPLE, envelope or self.envelope, registered_principal_id=principal, registered_capabilities=capabilities, grant=grant or self.grant, now=self.now)

    def test_local_orchestrator_accepts_scoped_grant_without_worker_execution(self):
        record = self.authorize()
        self.assertEqual(record.state, TaskState.DISPATCHED)
        self.assertIsNone(record.evidence)
        self.assertEqual(len(record.events), 5)

    def test_rejects_revoked_expired_wrong_resource_and_grant(self):
        for grant in [replace(self.grant, revoked=True), replace(self.grant, expires_at=self.now), replace(self.grant, resource_scope=frozenset({'other'})), replace(self.grant, grant_id='unknown')]:
            with self.subTest(grant=grant), self.assertRaises(OrchestrationError):
                self.authorize(grant=grant)

    def test_rejects_missing_grant(self):
        with self.assertRaises(OrchestrationError):
            authorize_proposal(SAMPLE, self.envelope, registered_principal_id='test-principal', registered_capabilities=('gr8r:review-proposal',), grant=None, now=self.now)

    def test_rejects_identity_and_capability_mismatch(self):
        with self.assertRaises(OrchestrationError):
            self.authorize(principal='wrong')
        with self.assertRaises(OrchestrationError):
            self.authorize(capabilities=())

    def test_rejects_payload_task_role_and_tool_escalation(self):
        for changes in [dict(candidate_fingerprint='sha256:'+'0'*64), dict(task_id='gr8r:other'), dict(resource_ref='other'), dict(role='IMPLEMENTER'), dict(permitted_tools=('shell',)), dict(capability_contract=('execute',))]:
            with self.subTest(changes=changes), self.assertRaises(OrchestrationError):
                self.authorize(replace(self.envelope, **changes))


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, 'events.sqlite')
        self.key = 'test-only-local-secret-0123456789'
        self.server = create_server(path=self.db, key=self.key, port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, method='POST', path='/v1/tasks/intake', key=None, data=SAMPLE):
        connection = http.client.HTTPConnection(*self.server.server_address, timeout=3)
        connection.request(method, path, body=json.dumps(data), headers={'X-Adapter-Key': self.key if key is None else key})
        response = connection.getresponse()
        result = response.status, json.loads(response.read())
        connection.close()
        return result

    def test_http_intake_replay_and_source_retention(self):
        status, receipt = self.request()
        self.assertEqual(status, 202)
        self.assertFalse(receipt['execution_performed'])
        self.assertEqual(receipt['vx_route']['gate'], 'HOLD')
        self.assertEqual(receipt, intake(SAMPLE, self.db))
        with sqlite3.connect(self.db) as db:
            self.assertEqual(json.loads(db.execute('SELECT payload FROM proposals').fetchone()[0]), SAMPLE)
            self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0], 1)

    def test_http_rejects_key_execute_and_auth_endpoint(self):
        self.assertEqual(self.request(key='')[0], 401)
        self.assertEqual(self.request(data={**SAMPLE, 'requested_action': 'execute'})[0], 400)
        self.assertEqual(self.request(path='/v1/tasks/authorize')[0], 404)
        with sqlite3.connect(self.db) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM events').fetchone()[0], 0)

    def test_health_reports_no_remote_connection(self):
        status, health = self.request(method='GET', path='/health')
        self.assertEqual(status, 200)
        self.assertFalse(health['vx_connected'])
        self.assertTrue(health['vx_contract_available'])

    def test_rejects_public_host_and_short_key(self):
        with self.assertRaises(ValueError):
            create_server(path=self.db, key=self.key, host='0.0.0.0')
        with self.assertRaises(ValueError):
            create_server(path=self.db, key='short')
