#!/usr/bin/env python3
"""Execute the VX-BOOTSTRAP-001 supervised-runtime acceptance scenario."""
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from runtime.supervised_runtime import run_bootstrap

def main():
 p=argparse.ArgumentParser(); p.add_argument("--workdir",default=".vx-bootstrap-run"); p.add_argument("--output",default="vx-bootstrap-evidence.json"); a=p.parse_args()
 workdir=Path(a.workdir).resolve(); report=run_bootstrap(workdir); output=Path(a.output).resolve(); output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"overall":report["overall"],"state":report["state"],"events":len(report["events"]),"evidence_verification":report["evidence_verification"],"output":str(output),"service_log":report.get("service_log_path"),"shutdown":report.get("shutdown"),"error":report.get("error")},indent=2)); return 0 if report["overall"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
