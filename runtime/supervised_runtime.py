"""Bounded, standard-library-only VX supervised runtime acceptance slice."""
from __future__ import annotations
import hashlib, json, os, queue, socket, subprocess, sys, time, urllib.error, urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

SERVICE_SOURCE = r'''import json, os, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
server = None
class H(BaseHTTPRequestHandler):
 def log_message(self, fmt, *args): print("HTTP " + (fmt % args), flush=True)
 def send(self, obj, code=200):
  body=json.dumps(obj).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
 def do_GET(self):
  if self.path == "/health": self.send({"status":"READY","service":"vx-bootstrap-test-service"})
  else: self.send({"error":"not found"},404)
 def do_POST(self):
  if self.path == "/shutdown":
   self.send({"status":"SHUTTING_DOWN"}); threading.Thread(target=server.shutdown,daemon=True).start(); return
  if self.path != "/task": self.send({"error":"not found"},404); return
  try:
   n=int(self.headers.get("Content-Length","0"))
   if n < 1 or n > 4096: raise ValueError("invalid body size")
   data=json.loads(self.rfile.read(n))
   if set(data) != {"task_id","value"} or not all(isinstance(data[k],str) for k in data): raise ValueError("invalid task schema")
   self.send({"task_id":data["task_id"],"status":"COMPLETED","output":data["value"]})
  except Exception as e: self.send({"error":str(e)},400)
server=ThreadingHTTPServer(("127.0.0.1",int(os.environ["VX_SAMPLE_PORT"])),H)
print(json.dumps({"event":"SERVICE_STARTED","host":"127.0.0.1","port":server.server_address[1]}),flush=True)
server.serve_forever(poll_interval=.1)
'''

def now(): return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00","Z")
def canonical(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def digest(v): return hashlib.sha256(canonical(v)).hexdigest()

class State(str, Enum):
 DISCOVERED="DISCOVERED"; VALIDATED="VALIDATED"; AUTHORIZED="AUTHORIZED"; STARTING="STARTING"; RUNNING="RUNNING"; FAILED="FAILED"; STOPPED="STOPPED"; QUARANTINED="QUARANTINED"; RECOVERY_PENDING="RECOVERY_PENDING"
TRANSITIONS={State.DISCOVERED:{State.VALIDATED,State.FAILED,State.QUARANTINED},State.VALIDATED:{State.AUTHORIZED,State.FAILED,State.QUARANTINED},State.AUTHORIZED:{State.STARTING,State.STOPPED,State.QUARANTINED},State.STARTING:{State.RUNNING,State.FAILED,State.RECOVERY_PENDING,State.STOPPED},State.RUNNING:{State.FAILED,State.STOPPED,State.RECOVERY_PENDING,State.QUARANTINED},State.FAILED:{State.RECOVERY_PENDING,State.STOPPED,State.QUARANTINED},State.RECOVERY_PENDING:{State.STARTING,State.FAILED,State.QUARANTINED,State.STOPPED},State.QUARANTINED:{State.STOPPED},State.STOPPED:set()}

@dataclass
class EvidenceLedger:
 events:list[dict[str,Any]]=field(default_factory=list)
 def append(self, kind, actor, subject, payload=None):
  e={"sequence":len(self.events),"timestamp":now(),"event_type":kind,"actor":actor,"subject":subject,"payload":payload or {},"previous_hash":self.events[-1]["event_hash"] if self.events else "GENESIS"}; e["event_hash"]=digest(e); self.events.append(e); return e
 def verify(self):
  previous="GENESIS"
  for i,e in enumerate(self.events):
   body={k:v for k,v in e.items() if k!="event_hash"}
   if e.get("sequence")!=i or e.get("previous_hash")!=previous or e.get("event_hash")!=digest(body): return {"valid":False,"failed_sequence":i,"events_checked":i}
   previous=e["event_hash"]
  return {"valid":True,"events_checked":len(self.events),"head_hash":previous}

@dataclass(frozen=True)
class AgentManifest:
 agent_id:str; version:str; creator_id:str; capabilities:tuple[str,...]; max_restarts:int=1

class AgentRegistry:
 def __init__(self,ledger): self.items={}; self.ledger=ledger
 def register(self,m,creator_ceiling):
  if not m.agent_id or not m.version or not m.creator_id: raise ValueError("manifest identity required")
  if not set(m.capabilities).issubset(creator_ceiling): raise PermissionError("CREATOR_AUTHORITY_CEILING_EXCEEDED")
  if not 0<=m.max_restarts<=2: raise ValueError("restart limit out of bounds")
  if m.agent_id in self.items: raise ValueError("duplicate agent identity")
  self.items[m.agent_id]={"manifest":m,"state":State.DISCOVERED.value}
  self.ledger.append("AGENT_REGISTERED","agent-registry",m.agent_id,{"version":m.version,"capabilities":list(m.capabilities),"manifest_hash":digest(m.__dict__)})

class PolicyGate:
 ALLOWED={"start","task.execute","restart","stop","health.check"}
 def __init__(self,max_processes=1,max_restarts=1,max_tasks=8): self.max_processes=max_processes; self.max_restarts=max_restarts; self.max_tasks=max_tasks
 def authorize(self,action,process_count=0,restart_count=0,task_count=0):
  if action not in self.ALLOWED: raise PermissionError("ACTION_NOT_ALLOWED:"+action)
  if action=="start" and process_count>=self.max_processes: raise PermissionError("PROCESS_LIMIT_EXCEEDED")
  if action=="restart" and restart_count>=self.max_restarts: raise PermissionError("RESTART_LIMIT_EXCEEDED")
  if action=="task.execute" and task_count>=self.max_tasks: raise PermissionError("TASK_LIMIT_EXCEEDED")

class MissionEngine:
 def compile(self,mission):
  if mission.get("approved") is not True: raise PermissionError("MISSION_NOT_APPROVED")
  if mission.get("mission_id")!="VX-BOOTSTRAP-001": raise ValueError("UNKNOWN_MISSION")
  tasks=mission.get("tasks")
  if not isinstance(tasks,list) or not 1<=len(tasks)<=8: raise ValueError("TASK_COUNT_OUT_OF_RANGE")
  out=[]
  for t in tasks:
   if not isinstance(t,dict) or set(t)!={"task_id","value","deadline_seconds"}: raise ValueError("INVALID_TASK_SCHEMA")
   if not isinstance(t["task_id"],str) or not t["task_id"].startswith("task.bootstrap."): raise ValueError("TASK_ID_OUTSIDE_MISSION_NAMESPACE")
   if not isinstance(t["value"],str) or len(t["value"])>256: raise ValueError("TASK_VALUE_INVALID")
   if not isinstance(t["deadline_seconds"],int) or isinstance(t["deadline_seconds"],bool) or not 1<=t["deadline_seconds"]<=30: raise ValueError("TASK_DEADLINE_INVALID")
   out.append({**t,"deadline_at":time.monotonic()+t["deadline_seconds"]})
  return out

class TaskScheduler:
 def __init__(self,capacity=8): self.q=queue.Queue(maxsize=capacity); self.cancelled=set()
 def submit(self,task): self.q.put_nowait(task)
 def cancel(self,task_id): self.cancelled.add(task_id)
 def next_task(self):
  try: t=self.q.get_nowait()
  except queue.Empty: return None
  return {**t,"cancelled_or_expired":True} if t["task_id"] in self.cancelled or time.monotonic()>t["deadline_at"] else t

class HealthMonitor:
 def wait_ready(self,adapter,timeout=4):
  end=time.monotonic()+timeout
  while time.monotonic()<end:
   if adapter.healthy(): return True
   if adapter.process and adapter.process.poll() is not None: return False
   time.sleep(.05)
  return False

class RecoveryManager:
 def __init__(self,max_restarts=1,window_seconds=20): self.max_restarts=max_restarts; self.window=window_seconds; self.times=[]
 def may_restart(self):
  t=time.monotonic(); self.times=[x for x in self.times if t-x<=self.window]
  if len(self.times)>=self.max_restarts: return False
  self.times.append(t); return True

class LocalProcessAdapter:
 def __init__(self): self.process=None; self.port=None; self.log=None
 def start(self,log_path):
  if self.process and self.process.poll() is None: raise RuntimeError("PROCESS_ALREADY_RUNNING")
  with socket.socket() as s: s.bind(("127.0.0.1",0)); self.port=s.getsockname()[1]
  env={"VX_SAMPLE_PORT":str(self.port),"PYTHONUNBUFFERED":"1"}
  self.log=open(log_path,"a",encoding="utf-8")
  self.process=subprocess.Popen([sys.executable,"-u","-c",SERVICE_SOURCE],stdin=subprocess.DEVNULL,stdout=self.log,stderr=subprocess.STDOUT,env=env,close_fds=True,text=True)
 def healthy(self):
  if not self.process or self.process.poll() is not None or not self.port: return False
  try:
   with urllib.request.urlopen(f"http://127.0.0.1:{self.port}/health",timeout=.4) as r: return r.status==200 and json.loads(r.read()).get("status")=="READY"
  except (OSError,ValueError,urllib.error.URLError): return False
 def task(self,task_id,value):
  if not self.healthy(): raise RuntimeError("SERVICE_NOT_HEALTHY")
  data=canonical({"task_id":task_id,"value":value}); req=urllib.request.Request(f"http://127.0.0.1:{self.port}/task",data=data,headers={"Content-Type":"application/json"},method="POST")
  with urllib.request.urlopen(req,timeout=2) as r: result=json.loads(r.read())
  if result!={"task_id":task_id,"status":"COMPLETED","output":value}: raise AssertionError("TASK_RECEIPT_MISMATCH")
  return result
 def stop(self,graceful=True):
  if not self.process: return None
  if self.process.poll() is None:
   if graceful and self.port:
    try:
     req=urllib.request.Request(f"http://127.0.0.1:{self.port}/shutdown",data=b"{}",headers={"Content-Type":"application/json"},method="POST")
     with urllib.request.urlopen(req,timeout=1) as r: assert r.status==200
     self.process.wait(timeout=2)
    except (OSError,urllib.error.URLError,subprocess.TimeoutExpired):
     if self.process.poll() is None: self.process.terminate()
   else: self.process.terminate()
   try: self.process.wait(timeout=2)
   except subprocess.TimeoutExpired: self.process.kill(); self.process.wait(timeout=2)
  code=self.process.returncode
  if self.log: self.log.close(); self.log=None
  return code

class Supervisor:
 def __init__(self,workdir,max_restarts=1):
  self.workdir=Path(workdir); self.workdir.mkdir(parents=True,exist_ok=True); self.ledger=EvidenceLedger(); self.registry=AgentRegistry(self.ledger); self.policy=PolicyGate(max_restarts=max_restarts); self.mission=MissionEngine(); self.scheduler=TaskScheduler(); self.health=HealthMonitor(); self.recovery=RecoveryManager(max_restarts); self.adapter=LocalProcessAdapter(); self.state=State.DISCOVERED; self.agent_id="agent.sample.health-task"; self.restart_count=0; self.transitions=[]
  self.ledger.append("LIFECYCLE_INITIALIZED","bootstrap",self.agent_id,{"state":self.state.value})
 def transition(self,new,actor,reason):
  if new!=self.state and new not in TRANSITIONS[self.state]: raise RuntimeError(f"INVALID_TRANSITION:{self.state.value}->{new.value}")
  old=self.state; self.state=new; rec={"from":old.value,"to":new.value,"timestamp":now(),"actor":actor,"reason":reason}; self.transitions.append(rec)
  if self.agent_id in self.registry.items: self.registry.items[self.agent_id]["state"]=new.value
  self.ledger.append("LIFECYCLE_TRANSITION",actor,self.agent_id,rec)
 def validate(self):
  m=AgentManifest(self.agent_id,"1.0.0","VAIXLNS_BOOTSTRAP",("health.check","task.echo"),1); self.registry.register(m,{"health.check","task.echo"}); self.transition(State.VALIDATED,"mission-engine","manifest-and-policy-validated")
 def start(self):
  self.policy.authorize("start"); self.transition(State.AUTHORIZED,"policy-gate","start-authorized"); self.transition(State.STARTING,"supervisor","local-test-service-start")
  self.adapter.start(self.workdir/"service.log")
  if not self.health.wait_ready(self.adapter): self.transition(State.FAILED,"health-monitor","readiness-failed"); raise RuntimeError("SERVICE_READINESS_FAILED")
  self.transition(State.RUNNING,"health-monitor","http-health-check-passed"); self.ledger.append("SERVICE_READY","health-monitor",self.agent_id,{"pid":self.adapter.process.pid,"port":self.adapter.port,"health_endpoint":"/health"})
 def execute(self):
  self.policy.authorize("task.execute"); task=self.mission.compile({"mission_id":"VX-BOOTSTRAP-001","approved":True,"tasks":[{"task_id":"task.bootstrap.echo.001","value":"VX_BOOTSTRAP_TASK_OK","deadline_seconds":5}]})[0]; self.scheduler.submit(task); t=self.scheduler.next_task()
  if not t or t.get("cancelled_or_expired"): raise RuntimeError("TASK_NOT_DISPATCHABLE")
  receipt=self.adapter.task(t["task_id"],t["value"]); self.ledger.append("TASK_EXECUTED","task-scheduler",t["task_id"],{"receipt":receipt,"receipt_hash":digest(receipt),"verified_output":True}); return receipt
 def fail_and_recover(self):
  old_pid=self.adapter.process.pid; self.ledger.append("FAILURE_INJECTED","bootstrap-test",self.agent_id,{"kind":"controlled-process-termination","pid":old_pid}); self.adapter.stop(graceful=False)
  exit_code=self.adapter.process.poll() if self.adapter.process else None
  if exit_code is None: raise RuntimeError("FAILURE_NOT_OBSERVED_BY_PROCESS_MONITOR")
  self.ledger.append("PROCESS_FAILURE_DETECTED","health-monitor",self.agent_id,{"pid":old_pid,"exit_code":exit_code,"detector":"subprocess.poll"})
  self.transition(State.RECOVERY_PENDING,"health-monitor","process-exit-observed")
  if not self.recovery.may_restart(): self.transition(State.QUARANTINED,"recovery-manager","restart-budget-exhausted"); return {"recovered":False,"reason":"RESTART_BUDGET_EXHAUSTED"}
  self.policy.authorize("restart",restart_count=self.restart_count); self.restart_count+=1; self.ledger.append("RECOVERY_ATTEMPT","recovery-manager",self.agent_id,{"attempt":self.restart_count,"budget":self.policy.max_restarts}); self.transition(State.STARTING,"recovery-manager","bounded-restart-authorized"); self.adapter.start(self.workdir/"service.log")
  if not self.health.wait_ready(self.adapter): self.transition(State.FAILED,"recovery-manager","readiness-after-restart-failed"); self.ledger.append("RECOVERY_FAILED","recovery-manager",self.agent_id,{"restart_count":self.restart_count}); return {"recovered":False,"reason":"READINESS_FAILED"}
  self.transition(State.RUNNING,"health-monitor","recovered-service-ready"); self.ledger.append("RECOVERY_SUCCEEDED","recovery-manager",self.agent_id,{"pid":self.adapter.process.pid,"restart_count":self.restart_count}); return {"recovered":True,"restart_count":self.restart_count,"new_pid":self.adapter.process.pid}
 def stop(self):
  if self.state!=State.STOPPED:
   self.policy.authorize("stop"); code=self.adapter.stop(graceful=True); self.transition(State.STOPPED,"supervisor","graceful-shutdown"); self.ledger.append("SERVICE_STOPPED","supervisor",self.agent_id,{"process_exit_code":code})
  return {"state":self.state.value,"process_exit_code":self.adapter.process.returncode if self.adapter.process else None}
 def report(self): return {"schema_version":"vx-bootstrap-evidence.v1","mission_id":"VX-BOOTSTRAP-001","state":self.state.value,"transitions":self.transitions,"events":self.ledger.events,"evidence_verification":self.ledger.verify(),"restart_count":self.restart_count}

def run_bootstrap(workdir):
 s=Supervisor(workdir)
 try:
  s.validate(); s.start(); task=s.execute()
  if task["output"]!="VX_BOOTSTRAP_TASK_OK": raise AssertionError("TASK_OUTPUT_MISMATCH")
  recovery=s.fail_and_recover()
  if not recovery.get("recovered"): raise RuntimeError("RECOVERY_FAILED")
  try: s.policy.authorize("production.deploy"); raise AssertionError("UNAUTHORIZED_ACTION_ALLOWED")
  except PermissionError as e: s.ledger.append("UNAUTHORIZED_ACTION_REJECTED","policy-gate",s.agent_id,{"action":"production.deploy","reason":str(e)})
  shutdown=s.stop(); report=s.report(); report.update({"task_receipt":task,"recovery":recovery,"shutdown":shutdown,"service_log_path":str((Path(workdir)/"service.log").resolve())}); report["overall"]="PASS" if shutdown["state"]=="STOPPED" and shutdown["process_exit_code"]==0 and report["evidence_verification"]["valid"] else "FAIL"; return report
 except Exception as e:
  s.ledger.append("BOOTSTRAP_ERROR","bootstrap",s.agent_id,{"error":type(e).__name__,"message":str(e)})
  if s.state not in {State.STOPPED,State.QUARANTINED}:
   try: s.stop()
   except Exception: pass
  report=s.report(); report.update({"overall":"FAIL","error":f"{type(e).__name__}: {e}"}); return report
