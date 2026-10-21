#!/usr/bin/env python3
"""Deterministic read-only extractor from pinned local Git checkouts."""
from __future__ import annotations
import argparse,hashlib,json,re,subprocess
from pathlib import Path
SUFFIXES={".md",".jsonl"}
SKIP={".git","node_modules",".venv","venv","build","dist","__pycache__"}
ENTRY=re.compile(r"^\s*(?:[-*]\s+|(?P<num>\d{1,6})[.)]\s+)(?P<name>[^\n]{3,240})")
HEADING=re.compile(r"^#{1,6}\s+(?P<name>.+?)\s*#*\s*$")
HINT=re.compile(r"tool|agent|api|index|innovation|capability|registry|فهرس|ابتكار|أداة|وكيل",re.I)
def hash256(x):return hashlib.sha256(x).hexdigest()
def git_sha(root):
    p=subprocess.run(["git","-C",str(root),"rev-parse","HEAD"],capture_output=True,text=True)
    if p.returncode or not re.fullmatch(r"[0-9a-f]{40}",p.stdout.strip()):raise ValueError(f"Unpinned checkout: {root}")
    return p.stdout.strip()
def kind(path):
    s=path.as_posix().lower()
    if "test" in path.parts:return "TEST"
    if "innovation" in s:return "INNOVATION"
    if "agent" in s:return "AGENT"
    if "tools/" in s:return "TOOL"
    if "index" in s or "registry" in s:return "INDEX_VIEW"
    return "SPEC"
def extract(roots):
    rows=[];sources=[]
    for root in sorted((Path(x).resolve() for x in roots),key=str):
        sha=git_sha(root);repository=root.name
        for file in sorted(root.rglob("*")):
            if not file.is_file() or file.suffix.lower() not in SUFFIXES or file.is_symlink():continue
            if any(p in SKIP for p in file.relative_to(root).parts) or file.stat().st_size>2000000:continue
            relative=file.relative_to(root).as_posix();raw=file.read_bytes()
            try:lines=raw.decode("utf-8").splitlines()
            except UnicodeDecodeError:continue
            fingerprint=hash256(raw)
            sources.append(dict(repository=repository,path=relative,revision_sha=sha,content_sha256=fingerprint))
            for line_no,line in enumerate(lines,1):
                match=None;number=None
                if file.suffix==".md":
                    match=ENTRY.match(line) or HEADING.match(line)
                    if match:
                        name=match.group("name").strip().strip("`* ")
                        number=match.groupdict().get("num")
                else:
                    try:
                        item=json.loads(line);name=item.get("name") or item.get("title") or item.get("canonical_id")
                    except (ValueError,AttributeError):continue
                    if not isinstance(name,str):continue
                if file.suffix==".md" and match is None:continue
                if len(name)<3 or name.startswith(("|","http")):continue
                record_kind=kind(Path(relative))
                if record_kind=="SPEC" and not HINT.search(name):continue
                identity=f"{repository}/{relative}:{line_no}:{name}"
                rows.append(dict(source_record_id="SRC-"+hash256(identity.encode())[:24],repository=repository,path=relative,
                    revision_sha=sha,content_sha256=fingerprint,source_line=line_no,original_name=name,
                    record_type=record_kind,originating_system=repository,state="RECOVERED",
                    evidence_status="UNKNOWN",original_number=number))
    rows.sort(key=lambda x:(x["repository"],x["path"],x["source_line"],x["source_record_id"]))
    sources.sort(key=lambda x:(x["repository"],x["path"]))
    return rows,sources
def main():
    p=argparse.ArgumentParser();p.add_argument("--repo",action="append",required=True);p.add_argument("--out",required=True)
    a=p.parse_args();records,sources=extract(a.repo);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    (out/"extracted-records.jsonl").write_text("".join(json.dumps(r,ensure_ascii=False,sort_keys=True)+"\n" for r in records),encoding="utf-8")
    for name,body in [("source-manifest.json",sources),("coverage.json",dict(sources_scanned=len(sources),records_extracted=len(records),repositories=len(set(s["repository"] for s in sources)),note="Mentions only; not independently verified capabilities"))]:
        (out/name).write_text(json.dumps(body,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(f"Extracted {len(records)} mentions from {len(sources)} source files")
if __name__=="__main__":main()
