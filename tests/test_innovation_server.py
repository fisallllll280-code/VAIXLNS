import json
import os
import tempfile
import threading
import time
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from services.innovation_server.server import (
    JobStore, Worker, make_handler, public_job, run_builtin
)


class InnovationServerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "jobs.sqlite3")
        self.store = JobStore(self.db_path)

    def tearDown(self):
        self.tmp.cleanup()

    def wait_for_state(self, job_id, expected, timeout=3):
        deadline = time.time() + timeout
        while time.time() < deadline:
            row = self.store.get(job_id)
            if row and row["state"] == expected:
                return row
            time.sleep(0.02)
        self.fail(f"job {job_id} did not reach {expected}")

    def test_allowlisted_hash_action_is_deterministic(self):
        a = run_builtin("hash_json", {"b": 2, "a": 1})
        b = run_builtin("hash_json", {"a": 1, "b": 2})
        self.assertEqual(a["sha256"], b["sha256"])

    def test_unknown_action_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "ACTION_NOT_ALLOWLISTED"):
            run_builtin("shell", {"command": "echo unsafe"})

    def test_idempotency_key_replays_same_job(self):
        first, created1 = self.store.submit("echo", {"x": 1}, "request-123")
        second, created2 = self.store.submit("echo", {"x": 1}, "request-123")
        self.assertTrue(created1)
        self.assertFalse(created2)
        self.assertEqual(first["job_id"], second["job_id"])

    def test_idempotency_key_payload_conflict_is_rejected(self):
        self.store.submit("echo", {"x": 1}, "request-123")
        with self.assertRaisesRegex(ValueError, "IDEMPOTENCY_KEY_CONFLICT"):
            self.store.submit("echo", {"x": 2}, "request-123")

    def test_worker_pool_runs_independent_jobs_concurrently(self):
        rows = [self.store.submit("echo", {"index": index})[0] for index in range(6)]
        active = 0
        max_active = 0
        guard = threading.Lock()

        def delayed_handler(action, payload):
            nonlocal active, max_active
            with guard:
                active += 1
                max_active = max(max_active, active)
            try:
                time.sleep(0.12)
                return real_handler(action, payload)
            finally:
                with guard:
                    active -= 1

        real_handler = run_builtin
        pool = WorkerPool(self.store, workers=3, poll_seconds=0.005)
        with patch("services.innovation_server.server.run_builtin", side_effect=delayed_handler):
            pool.start()
            try:
                for row in rows:
                    self.wait_for_state(row["job_id"], "COMPLETED", timeout=4)
            finally:
                pool.stop()

        self.assertGreaterEqual(max_active, 2)
        self.assertTrue(all(self.store.get(row["job_id"])["state"] == "COMPLETED" for row in rows))

    def test_worker_pool_rejects_invalid_worker_counts(self):
        for count in (0, -1, 33, True, 1.5):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    WorkerPool(self.store, workers=count)

    def test_worker_persists_result_but_does_not_claim_verification(self):
        row, _ = self.store.submit("tokenize", {"text": "VX memory VX task"})
        worker = Worker(self.store, poll_seconds=0.01)
        worker.start()
        try:
            completed = self.wait_for_state(row["job_id"], "COMPLETED")
        finally:
            worker.stop()
        public = public_job(completed)
        self.assertEqual(public["result"]["value"]["count"], 4)
        self.assertEqual(public["result"]["verification_state"], "NOT_VERIFIED")

    def test_server_health_and_authenticated_job_submission(self):
        token = "t" * 40
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.store, token))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            health_request = Request(base + "/health", headers={"Authorization": "Bearer " + token})
            with urlopen(health_request, timeout=2) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(json.loads(response.read())["external_effects"], "DISABLED")
            request = Request(
                base + "/v1/jobs",
                data=json.dumps({"action": "hash_json", "payload": {"x": 1}}).encode(),
                headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(request, timeout=2) as response:
                self.assertEqual(response.status, 202)
                payload = json.loads(response.read())
                self.assertEqual(payload["job"]["state"], "QUEUED")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_unauthorized_request_is_rejected(self):
        token = "t" * 40
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.store, token))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with self.assertRaises(HTTPError) as err:
                urlopen(f"http://127.0.0.1:{server.server_port}/v1/jobs", timeout=2)
            self.assertEqual(err.exception.code, 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_job_queue_survives_store_reopen(self):
        row, _ = self.store.submit("echo", {"durable": True})
        reopened = JobStore(self.db_path)
        self.assertEqual(reopened.get(row["job_id"])["state"], "QUEUED")


if __name__ == "__main__":
    unittest.main()
