#!/usr/bin/env python3
"""Build a searchable SQLite registry from source-grounded JSONL; never promote statuses."""
import argparse,json,sqlite3,hashlib,pathlib
REQUIRED={"source_record_id","repository","path","revision_sha","record_type","original_name","state","originating_system"}
TYPES={"INDEX_VIEW","TOOL","AGENT","INNOVATION","ALGORITHM","MODEL","LIBRARY","API","INTERFACE","TEST","SPEC"}
STATES={"RECOVERED","CANONICAL","PROPOSED","IMPLEMENTED","VERIFIED"}
def build(src,dest):
    records=[]
    for number,line in enumerate(pathlib.Path(src).read_text(encoding="utf-8").splitlines(),1):
        if not line.strip():continue
        r=json.loads(line)
        if not REQUIRED.issubset(r):raise ValueError(f"line {number}: missing required fields")
        if r["record_type"] not in TYPES or r["state"] not in STATES:raise ValueError(f"line {number}: invalid state or type")
        if len(r["revision_sha"])!=40:raise ValueError(f"line {number}: revision must be full SHA")
        if r["state"]=="VERIFIED" and (r.get("evidence_status")!="REPRODUCED" or not r.get("evidence_ref")):raise ValueError("unproven VERIFIED")
        records.append(r)
    if len({r["source_record_id"] for r in records})!=len(records):raise ValueError("duplicate source IDs")
    with sqlite3.connect(dest) as db:
        db.execute("CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, name TEXT, repo TEXT, kind TEXT, state TEXT, body TEXT)")
        db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS searchable USING fts5(id UNINDEXED,name,repo,kind)")
        if db.execute("SELECT COUNT(*) FROM records").fetchone()[0]:raise ValueError("output database is nonempty; use a new file")
        for r in records:
            vals=(r["source_record_id"],r["original_name"],r["repository"],r["record_type"])
            db.execute("INSERT INTO records VALUES (?,?,?,?,?,?)",(*vals,r["state"],json.dumps(r,ensure_ascii=False,sort_keys=True)))
            db.execute("INSERT INTO searchable VALUES (?,?,?,?)",vals)
    print(json.dumps({"indexed":len(records),"sha256":hashlib.sha256(pathlib.Path(src).read_bytes()).hexdigest()}))
def search(dest,q):
    with sqlite3.connect(dest) as db:
        for (body,) in db.execute("SELECT body FROM records WHERE id IN (SELECT id FROM searchable WHERE searchable MATCH ?) ORDER BY id",(q,)):print(body)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("mode",choices=["build","search"]);p.add_argument("input");p.add_argument("output_or_query");a=p.parse_args()
    if a.mode=="build":build(a.input,a.output_or_query)
    else:search(a.input,a.output_or_query)
