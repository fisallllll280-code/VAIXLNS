import json, os, subprocess, sys, threading, time, unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch
from tools.impossibility_engine.fabric import RemoteWorker, remote_workers_from_json, run_batch, canonical_hash, clear_assessment_cache
from tools.impossibility_engine.worker_server import make_handler

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

    def test_empty_batch_is_not_success(self):
        self.assertEqual(run_batch([])["state"],"NO_TASKS")

    def test_remote_requires_https_path_and_no_inline_credentials(self):
        for endpoint in ["http://worker.example/v1/assess","https://worker.example/v1/other",
                         "https://user:pass@worker.example/v1/assess"]:
            with self.assertRaises(ValueError): RemoteWorker("node-a",endpoint).validate()
        with self.assertRaises(ValueError):
            remote_workers_from_json('[{"worker_id":"n1","endpoint":"https://worker.example/v1/assess","token":"secret"}]')

    def test_remote_failure_falls_back_locally_and_marks_degraded(self):
        worker=RemoteWorker("node-a","https://worker.example/v1/assess",token_env="OMEGA_TEST_MISSING_TOKEN")
        with patch.dict(os.environ,{},clear=True):
            result=run_batch([problem("fallback")],remote_workers=[worker],allow_local_fallback=True)
        self.assertEqual(result["results"][0]["execution"]["status"],"FALLBACK_LOCAL")
        self.assertEqual(result["state"],"DEGRADED")
        self.assertEqual(result["fallback_count"],1)
        self.assertTrue(result["worker_metrics"][0]["circuit_open"])

    def test_remote_failure_can_be_strict(self):
        worker=RemoteWorker("node-a","https://worker.example/v1/assess",token_env="OMEGA_TEST_MISSING_TOKEN")
        with patch.dict(os.environ,{},clear=True):
            result=run_batch([problem("strict")],remote_workers=[worker],allow_local_fallback=False)
        self.assertEqual(result["results"][0]["execution"]["status"],"FAILED")
        self.assertEqual(result["failed_count"],1)

    def test_load_aware_remote_pool_obeys_per_worker_capacity(self):
        workers=[RemoteWorker("node-a","https://a.example/v1/assess",max_concurrency=1),
                 RemoteWorker("node-b","https://b.example/v1/assess",max_concurrency=1)]
        active={"node-a":0,"node-b":0}; peak={"node-a":0,"node-b":0}; lock=threading.Lock()
        def fake(worker,p,task_id):
            with lock:
                active[worker.worker_id]+=1
                peak[worker.worker_id]=max(peak[worker.worker_id],active[worker.worker_id])
            time.sleep(0.01)
            with lock: active[worker.worker_id]-=1
            return {"task_id":task_id,"result":{"assessment_sha256":task_id},
                    "execution":{"status":"SUCCEEDED","transport":"https","worker_id":worker.worker_id}}
        with patch("tools.impossibility_engine.fabric._remote_assess",side_effect=fake):
            result=run_batch([problem(str(i)) for i in range(6)],max_workers=6,remote_workers=workers)
        self.assertEqual(result["state"],"EXECUTED")
        self.assertEqual(result["completed_count"],6)
        self.assertLessEqual(peak["node-a"],1)
        self.assertLessEqual(peak["node-b"],1)
        self.assertEqual(sum(m["successes"] for m in result["worker_metrics"]),6)

    def test_worker_http_health_auth_and_assessment_contract(self):
        server=ThreadingHTTPServer(("127.0.0.1",0),make_handler("worker-test","test-secret"))
        thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
        try:
            base=f"http://127.0.0.1:{server.server_port}"
            with urlopen(base+"/healthz",timeout=2) as response:
                self.assertEqual(json.loads(response.read())["capability"],"omega.assess.v1")
            body=json.dumps({"task_id":"omega-test","request_sha256":canonical_hash(problem("http")),
                             "problem":problem("http")}).encode()
            bad=Request(base+"/v1/assess",data=body,headers={"Content-Type":"application/json"})
            with self.assertRaises(HTTPError) as ctx: urlopen(bad,timeout=2)
            self.assertEqual(ctx.exception.code,401)
            good=Request(base+"/v1/assess",data=body,headers={"Content-Type":"application/json",
                          "Authorization":"Bearer test-secret"})
            with urlopen(good,timeout=2) as response: envelope=json.loads(response.read())
            self.assertEqual(envelope["worker_id"],"worker-test")
            self.assertEqual(envelope["task_id"],"omega-test")
            self.assertEqual(envelope["result"]["classification"],"ENGINEERING_CHALLENGE")
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


    def test_repeated_local_assessment_uses_bounded_cache_without_shared_mutability(self):
        clear_assessment_cache()
        item = problem("cache-me")
        first = run_batch([item], max_workers=1)
        self.assertEqual(first["cache_hits"], 0)
        first["results"][0]["result"]["title"] = "caller-mutated"
        second = run_batch([item], max_workers=1)
        self.assertEqual(second["cache_hits"], 1)
        self.assertEqual(second["results"][0]["result"]["title"], "cache-me")
        self.assertEqual(second["state"], "EXECUTED")

    def test_batch_cli_executes_multiple_tasks(self):
        payload={"problems":[problem("cli-a"),problem("cli-b")],"max_workers":2}
        process=subprocess.run([sys.executable,"-m","tools.impossibility_engine","batch","--max-workers","2"],
            input=json.dumps(payload),text=True,capture_output=True,timeout=10)
        self.assertEqual(process.returncode,0,msg=process.stderr)
        output=json.loads(process.stdout)
        self.assertEqual(output["task_count"],2)
        self.assertEqual(output["state"],"EXECUTED")

if __name__ == "__main__": unittest.main()
