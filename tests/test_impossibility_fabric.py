import os, threading, time, unittest
from unittest.mock import patch
from tools.impossibility_engine.fabric import RemoteWorker, remote_workers_from_json, run_batch

def problem(title):
    return {"title": title, "goal": "Meet a measurable target",
            "constraints": [{"kind": "range", "variable": "latency_ms", "min": 0, "max": 50}],
            "evidence": [{"state": "OBSERVED", "ref": "fixture"}]}

class ImpossibilityFabricTests(unittest.TestCase):
    def test_concurrent_dispatch_preserves_input_order(self):
        lock=threading.Lock(); active=0; peak=0
        def fake(p):
            nonlocal active, peak
            with lock: active += 1; peak=max(peak, active)
            time.sleep(0.02 if p["title"]=="slow-first" else 0.005)
            with lock: active -= 1
            return {"assessment_sha256": p["title"]}
        ps=[problem("slow-first"),problem("fast-second"),problem("third")]
        with patch("tools.impossibility_engine.fabric.assess", side_effect=fake):
            result=run_batch(ps,max_workers=3)
        self.assertEqual(result["state"],"EXECUTED")
        self.assertEqual([r["result"]["assessment_sha256"] for r in result["results"]],
                         ["slow-first","fast-second","third"])
        self.assertGreaterEqual(peak,2)
        self.assertEqual(result["completed_count"],3)

    def test_bad_task_does_not_drop_other_task(self):
        result=run_batch([problem("ok"),{"goal":"bad","constraints":"invalid"}],max_workers=2)
        self.assertEqual(result["results"][0]["execution"]["status"],"SUCCEEDED")
        self.assertEqual(result["results"][1]["execution"]["status"],"FAILED")
        self.assertEqual(result["failed_count"],1)

    def test_remote_requires_https_valid_path_and_no_inline_credentials(self):
        for endpoint in ["http://worker.example/v1/assess","https://worker.example/v1/other",
                         "https://user:pass@worker.example/v1/assess"]:
            with self.assertRaises(ValueError): RemoteWorker("node-a",endpoint).validate()
        with self.assertRaises(ValueError):
            remote_workers_from_json('[{"worker_id":"n1","endpoint":"https://worker.example/v1/assess","token":"secret"}]')

    def test_remote_failure_falls_back_locally_visibly(self):
        worker=RemoteWorker("node-a","https://worker.example/v1/assess",token_env="OMEGA_TEST_MISSING_TOKEN")
        with patch.dict(os.environ,{},clear=True):
            result=run_batch([problem("fallback")],remote_workers=[worker],allow_local_fallback=True)
        self.assertEqual(result["results"][0]["execution"]["status"],"FALLBACK_LOCAL")
        self.assertEqual(result["configured_remote_workers"],["node-a"])

    def test_remote_failure_can_be_strict(self):
        worker=RemoteWorker("node-a","https://worker.example/v1/assess",token_env="OMEGA_TEST_MISSING_TOKEN")
        with patch.dict(os.environ,{},clear=True):
            result=run_batch([problem("strict")],remote_workers=[worker],allow_local_fallback=False)
        self.assertEqual(result["failed_count"],1)

    def test_duplicate_worker_ids_rejected(self):
        config='[{"worker_id":"node-a","endpoint":"https://one.example/v1/assess"},{"worker_id":"node-a","endpoint":"https://two.example/v1/assess"}]'
        with self.assertRaises(ValueError): remote_workers_from_json(config)

if __name__ == "__main__": unittest.main()
