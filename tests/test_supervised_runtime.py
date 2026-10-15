import tempfile, unittest
from pathlib import Path
from runtime.supervised_runtime import AgentManifest, EvidenceLedger, MissionEngine, PolicyGate, State, run_bootstrap
from runtime.agent_factory import AgentFactory
from runtime.paper_trading import simulate_paper_trades
from scripts.verify_vx_bootstrap_evidence import verify

class SupervisedRuntimeTests(unittest.TestCase):
 def test_mission_engine_rejects_unapproved_mission(self):
  with self.assertRaises(PermissionError): MissionEngine().compile({"mission_id":"VX-BOOTSTRAP-001","approved":False,"tasks":[]})
 def test_hash_chain_detects_tampering(self):
  l=EvidenceLedger(); l.append("A","test","x",{"v":1}); self.assertTrue(l.verify()["valid"]); l.events[0]["payload"]["v"]=2; self.assertFalse(l.verify()["valid"])
 def test_policy_denies_unauthorized_and_limits_restarts(self):
  g=PolicyGate(max_restarts=1)
  with self.assertRaises(PermissionError): g.authorize("production.deploy")
  g.authorize("restart",restart_count=0)
  with self.assertRaises(PermissionError): g.authorize("restart",restart_count=1)
 def test_agent_capabilities_cannot_exceed_creator_ceiling(self):
  f=AgentFactory()
  with self.assertRaises(PermissionError): f.create_manifest(agent_id="child",version="1",creator_id="parent",requested_capabilities=["production.deploy"],creator_ceiling={"task.echo"})
 def test_factory_deployment_requires_validated_artifact_and_human(self):
  f=AgentFactory(); a=f.create_manifest(agent_id="child",version="1",creator_id="parent",requested_capabilities=["task.echo"],creator_ceiling={"task.echo"})
  self.assertEqual(f.deployment_decision(a,supplied_hash=a.artifact_hash,validation_status="MANIFEST_SCHEMA_VALIDATED",approved_by="human"),"BLOCKED_VALIDATION_NOT_PASSED")
  self.assertEqual(f.deployment_decision(a,supplied_hash=a.artifact_hash,validation_status="ISOLATED_TESTS_PASSED",approved_by=None),"BLOCKED_HUMAN_APPROVAL_REQUIRED")
 def test_paper_trading_never_claims_real_orders(self):
  r=simulate_paper_trades([100,90,110]); self.assertEqual(r["mode"],"SIMULATED"); self.assertFalse(r["real_money_orders"]); self.assertFalse(r["financial_credentials_used"]); self.assertEqual([e["event"] for e in r["trade_events"]],["PAPER_BUY","PAPER_SELL"])
 def test_actual_process_health_task_failure_recovery_and_shutdown(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=run_bootstrap(Path(tmp)); self.assertEqual(r["overall"],"PASS",r.get("error")); self.assertEqual(r["state"],State.STOPPED.value); self.assertEqual(r["shutdown"]["process_exit_code"],0); self.assertEqual(r["task_receipt"]["output"],"VX_BOOTSTRAP_TASK_OK"); self.assertTrue(r["recovery"]["recovered"]); self.assertTrue(r["evidence_verification"]["valid"]); self.assertTrue(verify(r)[0])

if __name__=="__main__": unittest.main(verbosity=2)
