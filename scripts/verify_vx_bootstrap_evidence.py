#!/usr/bin/env python3
"""Independent verification of bootstrap event chain and acceptance conditions."""
import argparse, hashlib, json, sys
from pathlib import Path

def canonical(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def verify(report):
 events=report.get("events")
 if not isinstance(events,list): return False,"EVENTS_MISSING"
 previous="GENESIS"
 for i,e in enumerate(events):
  body={k:v for k,v in e.items() if k!="event_hash"}; expected=hashlib.sha256(canonical(body)).hexdigest()
  if e.get("sequence")!=i or e.get("previous_hash")!=previous or e.get("event_hash")!=expected: return False,f"HASH_CHAIN_INVALID_AT_{i}"
  previous=expected
 required={"SERVICE_READY","TASK_EXECUTED","FAILURE_INJECTED","PROCESS_FAILURE_DETECTED","RECOVERY_SUCCEEDED","UNAUTHORIZED_ACTION_REJECTED","SERVICE_STOPPED"}
 present={e.get("event_type") for e in events}
 if not required.issubset(present): return False,"REQUIRED_EVIDENCE_MISSING:"+",".join(sorted(required-present))
 if report.get("overall")!="PASS" or report.get("state")!="STOPPED": return False,"RUNTIME_NOT_STOPPED"
 if report.get("task_receipt",{}).get("output")!="VX_BOOTSTRAP_TASK_OK": return False,"TASK_OUTPUT_UNVERIFIED"
 if not report.get("recovery",{}).get("recovered"): return False,"RECOVERY_UNVERIFIED"
 if report.get("shutdown",{}).get("process_exit_code")!=0: return False,"SHUTDOWN_EXIT_NOT_ZERO"
 return True,previous

def main():
 p=argparse.ArgumentParser(); p.add_argument("evidence",type=Path); a=p.parse_args()
 try: report=json.loads(a.evidence.read_text(encoding="utf-8"))
 except Exception as e: print(f"EVIDENCE_READ_FAIL:{e}",file=sys.stderr); return 2
 ok,detail=verify(report); print(json.dumps({"valid":ok,"detail":detail,"events_checked":len(report.get("events",[]))},indent=2)); return 0 if ok else 1
if __name__=="__main__": raise SystemExit(main())
