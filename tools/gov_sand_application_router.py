"""Plan agency submissions from an indexed portfolio; does not submit anything."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ROADMAP=ROOT/"registry/gov-sand/priority-roadmap.v1.json"
TARGETS=ROOT/"registry/gov-sand/application-targets.v1.json"
OUT=ROOT/"registry/gov-sand/application-queue.v1.json"
EXCLUDED={"PERSONAL"}
def build(roadmap,targets):
    assert all(t["channel"]=="OFFICIAL_PORTAL_MANUAL" for t in targets["targets"])
    queue=[]
    for idea in roadmap["initiatives"]:
        if idea["domain"] in EXCLUDED:continue
        for target in targets["targets"]:
            if idea["domain"] not in target["areas"]:continue
            queue.append({"application_id":idea["id"]+"--"+target["id"],"system_id":idea["id"],"target_id":target["id"],"target_name":target["name"],"target_url":target["url"],"proposal":idea["name"],"source_status":idea["status"],"required_documents":target["prerequisites"],"next_action":idea["next"],"submission_status":"NOT_SUBMITTED","external_reference":None,"requires_authorized_human_submission":True})
    return {"schema_version":"1.0","actual_submissions":0,"official_approvals":0,"generated_only":True,"applications":queue}
def main():
    roadmap=json.loads(ROADMAP.read_text(encoding="utf-8"))
    targets=json.loads(TARGETS.read_text(encoding="utf-8"))
    data=build(roadmap,targets)
    OUT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Generated",len(data["applications"]),"draft routes, zero submissions")
if __name__=="__main__": main()
