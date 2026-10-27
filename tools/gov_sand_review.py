"""Evidence-constrained briefing generator. No external calls or LLM claims."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"registry/gov-sand/priority-roadmap.v1.json"
OUTPUT=ROOT/"registry/gov-sand/review-report.v1.json"
def review(items):
    ids=set()
    out=[]
    for x in items:
        for required in ("id","status","evidence","next","owner","priority"):
            if not x.get(required): raise ValueError(f"missing {required}")
        if x["id"] in ids: raise ValueError("duplicate")
        ids.add(x["id"])
        status=x["status"]
        if status not in ("TESTED_LIMITED","DOCUMENTED","DRAFT","DESIGNED","BLOCKED","PROPOSED","ACTION_REQUIRED"):
            raise ValueError("unsupported status")
        out.append({"id":x["id"],"name":x["name"],"status":status,"explanation_ar":f"الحالة: {status}. الدليل المسجل: {x['evidence']}. الخطوة التالية: {x['next']}.","requires_human_review":True})
    return {"report_type":"UNVERIFIED_REGISTRY_SUMMARY","official_approval":False,"real_integration":False,"cases":out}
def main():
    data=json.loads(INPUT.read_text(encoding="utf-8"))
    output=review(data["initiatives"])
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"reviewed {len(output['cases'])} initiatives")
if __name__=="__main__":main()
