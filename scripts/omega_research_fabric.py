#!/usr/bin/env python3
"""Incremental local engineering index with opt-in public research and server adapters."""
from __future__ import annotations
import argparse, hashlib, html, json, os, re, sqlite3, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

SCHEMA = "vaixlns.omega-research-fabric.v1"
IGNORE = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build", "target", ".next", ".vaixl_ns"}
IGNORE_NAMES = {"omega-research-results.json", "engineering-execution-plan.json", "engineering-execution-receipt.json"}
TEXT = {".md",".rst",".txt",".py",".rs",".go",".js",".jsx",".ts",".tsx",".java",".c",".cc",".cpp",".h",".hpp",".cs",".rb",".php",".swift",".kt",".json",".yaml",".yml",".toml",".xml",".sql",".sh",".tf",".proto",".graphql",".ini",".cfg"}
SYSTEMS = ("VAIXLNS","VLNS","NEXNET","NEXENT","VX","VV","XV","ARC-X","V-Kernel","VSG","Ω0_GENESIS_CORE","project.genome")
SIGNALS = {
 "REQUIREMENT": r"\b(must|shall|required|requirement|acceptance criteria)\b",
 "PROOF_OR_PROVENANCE": r"\b(invariant|proof obligation|deterministic|reproducible|provenance|sha-?256)\b",
 "SECURITY": r"\b(security|threat|secret|credential|permission|authorization|trust boundary|sandbox)\b",
 "INTERFACE_OR_SCHEMA": r"\b(endpoint|interface|api|schema|contract|protocol|manifest)\b",
 "TEST_OR_FAILURE": r"\b(test|regression|assert|negative case|failure|counterexample|replay)\b",
 "PERFORMANCE": r"\b(latency|throughput|cache|incremental|benchmark|memory|index|cost)\b",
 "RESEARCH": r"\b(research|paper|doi|citation|reference|arxiv|crossref|openalex)\b",
}
UA = "VAIXLNS-OMEGA-Research-Fabric/1.0"
MAX_BYTES = 4_000_000

def canonical(v: Any) -> bytes:
    return json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def clean(v: Any, cap: int = 12000) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", str(v or "")))).strip()[:cap]
def category(p: Path) -> str:
    n, s = p.name.lower(), p.suffix.lower()
    if "test" in p.parts or n.startswith("test_") or ".test." in n: return "TEST"
    if n in {"pyproject.toml","package.json","cargo.toml","go.mod","makefile","dockerfile"}: return "CONFIG"
    if s in {".md",".rst",".adoc"}: return "DOCUMENTATION"
    if s in {".py",".rs",".go",".js",".jsx",".ts",".tsx",".java",".c",".cc",".cpp",".h",".hpp",".cs",".rb",".php",".swift",".kt"}: return "SOURCE"
    if s in {".json",".yaml",".yml",".toml",".xml",".sql",".proto",".graphql"}: return "SCHEMA_OR_DATA"
    return "OTHER"
def inverted_abstract(index: Any) -> str:
    if not isinstance(index, dict): return ""
    positions = {}
    for word, places in index.items():
        if isinstance(places, list):
            for place in places:
                if isinstance(place, int) and place >= 0: positions[place] = word
    return " ".join(positions[i] for i in range(max(positions) + 1) if i in positions) if positions else ""
def extract(path: str, raw: bytes) -> dict[str, Any]:
    body = ""
    if Path(path).suffix.lower() in TEXT and len(raw) <= 2_000_000:
        body = raw.decode("utf-8-sig", errors="replace")
    combined = path + "\n" + body
    return {
      "path": path, "filename": Path(path).name, "category": category(Path(path)),
      "size_bytes": len(raw), "sha256": sha(raw), "body": body[:2_000_000],
      "system_refs": sorted(s for s in SYSTEMS if s.casefold() in combined.casefold()),
      "omega_refs": sorted(set(re.findall(r"Ω[.]?\d{3,5}(?:[.][A-Z0-9_-]+)?", body, re.I)))[:500],
      "signals": sorted(k for k, pattern in SIGNALS.items() if re.search(pattern, body, re.I)),
    }
def db_open(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(path)); db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=NORMAL")
    db.executescript("""
      CREATE TABLE IF NOT EXISTS docs(path TEXT PRIMARY KEY,filename TEXT,category TEXT,size INTEGER,mtime INTEGER,sha256 TEXT,body TEXT,systems TEXT,omegas TEXT,signals TEXT);
      CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(path UNINDEXED,filename,category,body,tokenize='unicode61');
      CREATE TABLE IF NOT EXISTS evidence(id TEXT PRIMARY KEY,provider TEXT,source_id TEXT,title TEXT,url TEXT,abstract TEXT,published TEXT,retrieved TEXT,content_sha256 TEXT,state TEXT,metadata TEXT);
      CREATE VIRTUAL TABLE IF NOT EXISTS evidence_fts USING fts5(id UNINDEXED,provider,title,abstract,tokenize='unicode61');
    """); db.commit(); return db
def index_local(root: Path, db: sqlite3.Connection, db_path: Path, out_path: Path) -> dict[str, Any]:
    root = root.resolve(); paths = []; skip_paths = {db_path.resolve(),out_path.resolve()}
    for current, dirs, files in os.walk(root, followlinks=False):
        base = Path(current); dirs[:] = sorted(d for d in dirs if d not in IGNORE and not (base/d).is_symlink())
        for name in sorted(files):
            p = base/name
            if p.is_file() and not p.is_symlink() and p.resolve() not in skip_paths and name not in IGNORE_NAMES:
                paths.append(p)
    seen=set(); changed=unchanged=skipped=0
    for p in sorted(paths):
        rel=p.relative_to(root).as_posix(); seen.add(rel)
        try: stat=p.stat(); raw=p.read_bytes()
        except OSError: skipped+=1; continue
        filehash=sha(raw); old=db.execute("SELECT sha256 FROM docs WHERE path=?",(rel,)).fetchone()
        if old and old["sha256"] == filehash: unchanged+=1; continue
        item=extract(rel,raw)
        db.execute("DELETE FROM docs_fts WHERE path=?",(rel,))
        db.execute("""INSERT INTO docs VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET
          filename=excluded.filename,category=excluded.category,size=excluded.size,mtime=excluded.mtime,
          sha256=excluded.sha256,body=excluded.body,systems=excluded.systems,omegas=excluded.omegas,signals=excluded.signals""",
          (rel,item["filename"],item["category"],item["size_bytes"],stat.st_mtime_ns,item["sha256"],item["body"],
           json.dumps(item["system_refs"],ensure_ascii=False),json.dumps(item["omega_refs"],ensure_ascii=False),json.dumps(item["signals"])))
        db.execute("INSERT INTO docs_fts VALUES(?,?,?,?)",(rel,item["filename"],item["category"],item["body"])); changed+=1
    oldpaths=[r["path"] for r in db.execute("SELECT path FROM docs")]
    removed=0
    for rel in oldpaths:
        if rel not in seen:
            db.execute("DELETE FROM docs_fts WHERE path=?",(rel,)); db.execute("DELETE FROM docs WHERE path=?",(rel,)); removed+=1
    hashes=[(r["path"],r["sha256"]) for r in db.execute("SELECT path,sha256 FROM docs ORDER BY path")]
    inv=sha(canonical(hashes)); db.commit()
    return {"root":str(root),"file_count":len(seen)-skipped,"changed":changed,"unchanged":unchanged,"removed":removed,"skipped":skipped,"inventory_sha256":inv}
def terms(q: str) -> str:
    t=re.findall(r"[\wΩ]+",q,re.UNICODE)
    return " AND ".join('"'+x.replace('"','""')+'"' for x in t[:20])
def local_search(db: sqlite3.Connection,q: str,limit: int) -> list[dict[str,Any]]:
    match=terms(q)
    if not match: return []
    rows=db.execute("""SELECT d.*,snippet(docs_fts,3,'[',']','…',16) AS snippet,bm25(docs_fts) score
      FROM docs_fts JOIN docs d ON d.path=docs_fts.path WHERE docs_fts MATCH ?
      ORDER BY score,d.path LIMIT ?""",(match,limit)).fetchall()
    return [{"path":r["path"],"category":r["category"],"sha256":r["sha256"],"snippet":r["snippet"],
      "score":r["score"],"system_refs":json.loads(r["systems"]),"omega_refs":json.loads(r["omegas"]),
      "engineering_signals":json.loads(r["signals"]),"state":"LOCAL_SOURCE_FOUND_NOT_SEMANTICALLY_VERIFIED"} for r in rows]
def record(provider: str, source_id: str, title: Any, url: Any, abstract: Any="", published: Any="", metadata: dict|None=None) -> dict[str,Any]:
    base={"provider":provider,"source_id":clean(source_id,500),"title":clean(title,1000) or "(untitled)",
          "url":clean(url,2000),"abstract":clean(abstract),"published":clean(published,80),"metadata":metadata or {}}
    base["content_sha256"]=sha(canonical(base)); base["id"]=sha((provider+"\n"+base["source_id"]+"\n"+base["url"]).encode())
    base["state"]="DISCOVERED_UNVERIFIED"; return base
def parse_results(provider: str, raw: bytes, limit: int) -> list[dict[str,Any]]:
    out=[]
    if provider=="arxiv":
        root=ET.fromstring(raw); ns={"a":"http://www.w3.org/2005/Atom"}
        for e in root.findall("a:entry",ns)[:limit]:
            ident=e.findtext("a:id",default="",namespaces=ns)
            out.append(record(provider,ident,e.findtext("a:title",default="",namespaces=ns),ident,
                e.findtext("a:summary",default="",namespaces=ns),e.findtext("a:published",default="",namespaces=ns),
                {"authors":[clean(a.findtext("a:name",default="",namespaces=ns),200) for a in e.findall("a:author",ns)]}))
        return out
    payload=json.loads(raw.decode())
    items=payload.get("message",{}).get("items",[]) if provider=="crossref" else payload.get("results",[]) if provider=="openalex" else payload.get("items",[])
    for x in items[:limit]:
        if provider=="crossref":
            doi=x.get("DOI",""); date=x.get("published-print") or x.get("published-online") or {}
            parts=date.get("date-parts",[[]])[0] if isinstance(date,dict) else []
            out.append(record(provider,doi or x.get("URL",""),(x.get("title") or [""])[0],x.get("URL") or ("https://doi.org/"+doi if doi else ""),
             x.get("abstract",""),"-".join(map(str,parts)),{"type":x.get("type",""),"publisher":x.get("publisher","")}))
        elif provider=="openalex":
            out.append(record(provider,x.get("id",""),x.get("title",""),x.get("doi") or x.get("id",""),
             inverted_abstract(x.get("abstract_inverted_index")),x.get("publication_date",""),
             {"cited_by_count":x.get("cited_by_count",0),"open_access":x.get("open_access",{})}))
        elif provider=="github":
            out.append(record(provider,x.get("full_name",""),x.get("full_name",""),x.get("html_url",""),x.get("description",""),x.get("pushed_at",""),
             {"stars":x.get("stargazers_count",0),"language":x.get("language",""),"default_branch":x.get("default_branch","")}))
    return out
def https_get(url: str, headers: dict|None=None, timeout: int=15) -> bytes:
    u=urlparse(url)
    if u.scheme!="https" or not u.hostname or u.username or u.password or u.fragment: raise ValueError("public provider URL must be HTTPS without embedded credentials/fragments")
    req=urllib.request.Request(url,headers={"User-Agent":UA,**(headers or {})},method="GET")
    with urllib.request.urlopen(req,timeout=max(2,min(30,timeout))) as res:
        raw=res.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise ValueError("response byte limit exceeded")
    return raw
def search_provider(provider: str,q: str,limit: int,timeout: int) -> list[dict[str,Any]]:
    limit=max(1,min(limit,25))
    if provider=="crossref":
        params={"query":q,"rows":str(limit)}
        if os.getenv("VAIXLNS_MAILTO"): params["mailto"]=os.environ["VAIXLNS_MAILTO"]
        url="https://api.crossref.org/works?"+urllib.parse.urlencode(params)
    elif provider=="openalex":
        params={"search":q,"per-page":str(limit)}
        if os.getenv("OPENALEX_API_KEY"): params["api_key"]=os.environ["OPENALEX_API_KEY"]
        url="https://api.openalex.org/works?"+urllib.parse.urlencode(params)
    elif provider=="arxiv":
        url="https://export.arxiv.org/api/query?"+urllib.parse.urlencode({"search_query":"all:"+q,"max_results":str(limit),"sortBy":"relevance"})
    elif provider=="github":
        url="https://api.github.com/search/repositories?"+urllib.parse.urlencode({"q":q+" in:name,description,readme","per_page":str(limit),"sort":"updated"})
    else: raise ValueError("unsupported provider")
    headers={"Accept":"application/vnd.github+json"} if provider=="github" else {}
    if provider=="github" and os.getenv("GITHUB_TOKEN"): headers["Authorization"]="Bearer "+os.environ["GITHUB_TOKEN"]
    return parse_results(provider,https_get(url,headers,timeout),limit)
def store_evidence(db: sqlite3.Connection,items: list[dict[str,Any]]) -> None:
    for x in items:
        new=not db.execute("SELECT 1 FROM evidence WHERE id=?",(x["id"],)).fetchone()
        vals=(x["id"],x["provider"],x["source_id"],x["title"],x["url"],x["abstract"],x["published"],
              time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),x["content_sha256"],x["state"],json.dumps(x["metadata"],ensure_ascii=False,sort_keys=True))
        db.execute("""INSERT INTO evidence VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET
          title=excluded.title,url=excluded.url,abstract=excluded.abstract,published=excluded.published,
          retrieved=excluded.retrieved,content_sha256=excluded.content_sha256,state=excluded.state,metadata=excluded.metadata""",vals)
        if new: db.execute("INSERT INTO evidence_fts VALUES(?,?,?,?)",(x["id"],x["provider"],x["title"],x["abstract"]))
    db.commit()
def remote_search(db: sqlite3.Connection,q: str,limit: int) -> list[dict[str,Any]]:
    match=terms(q)
    if not match: return []
    rows=db.execute("""SELECT e.*,bm25(evidence_fts) score FROM evidence_fts JOIN evidence e ON e.id=evidence_fts.id
      WHERE evidence_fts MATCH ? ORDER BY score,e.provider,e.source_id LIMIT ?""",(match,limit)).fetchall()
    return [{"provider":r["provider"],"source_id":r["source_id"],"title":r["title"],"url":r["url"],"abstract":r["abstract"],
      "published":r["published"],"retrieved_at":r["retrieved"],"content_sha256":r["content_sha256"],"state":r["state"],
      "metadata":json.loads(r["metadata"]),"score":r["score"]} for r in rows]
def safe_server_url(base: str,path: str) -> str:
    u=urlparse(base)
    if u.scheme not in {"http","https"} or not u.hostname or u.username or u.password or u.query or u.fragment: raise ValueError("invalid server base URL")
    if u.scheme=="http" and u.hostname not in {"localhost","127.0.0.1","::1"}: raise ValueError("remote server must use HTTPS")
    p=urlparse(path)
    if p.scheme or p.netloc or not path.startswith("/") or ".." in Path(p.path).parts: raise ValueError("server path must be absolute and cannot traverse directories")
    return base.rstrip("/")+path
def server_get(url: str,timeout: int) -> bytes:
    u=urlparse(url)
    if u.scheme=="http" and u.hostname not in {"localhost","127.0.0.1","::1"}: raise ValueError("insecure HTTP blocked")
    req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"application/json"},method="GET")
    with urllib.request.urlopen(req,timeout=max(2,min(30,timeout))) as res: raw=res.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES: raise ValueError("server response byte limit exceeded")
    return raw
def search_server(config: dict[str,Any],q: str,timeout: int) -> dict[str,Any]:
    sid=str(config.get("server_id","")).strip()
    if not sid: raise ValueError("server_id required")
    base=config["base_url"]
    health=json.loads(server_get(safe_server_url(base,config.get("health_path","/health")),timeout).decode())
    result={"server_id":sid,"state":"HEALTHY","health":health,"results":[]}
    if q:
        url=safe_server_url(base,config.get("search_path","/search"))
        url += ("&" if "?" in url else "?")+urllib.parse.urlencode({"q":q})
        payload=json.loads(server_get(url,timeout).decode())
        items=payload.get("results",[]) if isinstance(payload,dict) else []
        for i,x in enumerate(items[:25]):
            if not isinstance(x,dict): continue
            result["results"].append(record("server:"+sid,x.get("id") or x.get("omega_id") or str(i),
              x.get("title") or x.get("name") or x.get("omega_id"),x.get("url",""),
              x.get("abstract") or x.get("summary") or x.get("description",""),x.get("updated_at",""),
              {"omega_id":x.get("omega_id"),"kind":x.get("kind")}))
    return result
def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",default="."); p.add_argument("--db",default=".vaixl_ns/omega-research-index.sqlite3")
    p.add_argument("--output",default="omega-research-results.json"); p.add_argument("--query",default="")
    p.add_argument("--research",action="store_true",help="opt in to outbound public research API calls")
    p.add_argument("--providers",nargs="+",choices=["crossref","openalex","arxiv","github"],default=["crossref","openalex","arxiv","github"])
    p.add_argument("--server-manifest"); p.add_argument("--limit",type=int,default=10); p.add_argument("--timeout",type=int,default=15)
    a=p.parse_args(); a.limit=max(1,min(25,a.limit)); a.timeout=max(2,min(30,a.timeout))
    root=Path(a.root).resolve(); dbpath=Path(a.db).resolve(); outpath=Path(a.output).resolve()
    if not root.is_dir(): p.error("project root is not a directory")
    db=db_open(dbpath)
    try:
        index=index_local(root,db,dbpath,outpath); local=local_search(db,a.query,a.limit) if a.query else []
        prior=remote_search(db,a.query,a.limit) if a.query else []; found=[]; providers=[]; servers=[]
        if a.research and a.query:
            for provider in a.providers:
                try:
                    records=search_provider(provider,a.query,a.limit,a.timeout); store_evidence(db,records); found+=records
                    providers.append({"provider":provider,"state":"SEARCH_SUCCEEDED","count":len(records)})
                except Exception as exc: providers.append({"provider":provider,"state":"SEARCH_FAILED","error_type":type(exc).__name__,"message":str(exc)[:300]})
        if a.server_manifest:
            manifest=json.loads(Path(a.server_manifest).read_text(encoding="utf-8"))
            if not isinstance(manifest.get("servers",[]),list): p.error("server manifest 'servers' must be an array")
            for cfg in manifest.get("servers",[])[:25]:
                try:
                    r=search_server(cfg,a.query,a.timeout); servers.append(r)
                    if r["results"]: store_evidence(db,r["results"]); found+=r["results"]
                except Exception as exc: servers.append({"server_id":str(cfg.get("server_id",""))[:100],"state":"ADAPTER_FAILED","error_type":type(exc).__name__,"message":str(exc)[:300],"results":[]})
        result={"schema":SCHEMA,"index":index,"query":a.query,"local_results":local,"previously_indexed_remote_results":prior,
          "remote_discoveries":sorted({x["id"]:x for x in found}.values(),key=lambda x:(x["provider"],x["source_id"])),
          "provider_status":providers,"server_status":servers,
          "semantics":{"local_sha256":"SHA-256 of full local file bytes","remote_hash":"normalized metadata hash, not full paper/repository",
            "remote_state":"DISCOVERED_UNVERIFIED","agents_dispatched":0,"project_code_executed":False,
            "coverage":"configured providers and explicit server manifest only; no universal-coverage claim"}}
        result["result_sha256"]=sha(canonical(result))
        outpath.parent.mkdir(parents=True,exist_ok=True); outpath.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"schema":SCHEMA,"index":index,"local_results":len(local),"remote_discoveries":len(found),
          "providers":providers,"servers":[{"server_id":x.get("server_id"),"state":x.get("state"),"results":len(x.get("results",[]))} for x in servers],
          "result_sha256":result["result_sha256"],"execution":"NOT_PERFORMED"},ensure_ascii=False,sort_keys=True))
        return 0
    except (OSError,ValueError,sqlite3.Error,json.JSONDecodeError) as exc: p.error(str(exc))
    finally: db.close()
if __name__=="__main__": raise SystemExit(main())
