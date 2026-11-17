#!/usr/bin/env python3
"""Create exactly one manifest-authorized VAIXLNS repository; never overwrite an existing repo."""
from __future__ import annotations
import argparse, base64, json, os, sys, urllib.error, urllib.request
from pathlib import Path
from typing import Any, Callable

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[1]

def api_call(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Accept":"application/vnd.github+json", "Authorization":f"Bearer {token}",
        "X-GitHub-Api-Version":"2022-11-28", "Content-Type":"application/json",
        "User-Agent":"VAIXLNS-authorized-repository-factory/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw=response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        if exc.code == 404 and method == "GET":
            return {"_status":404}
        raise RuntimeError(f"GitHub API {method} {path} failed with HTTP {exc.code}") from exc

def validate_target(name: str, manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(name,str) or not name.strip():
        raise ValueError("repository name is required")
    owner=manifest.get("owner")
    if not isinstance(owner,str) or not owner.strip():
        raise ValueError("manifest owner missing")
    matches=[r for r in manifest.get("repositories",[]) if isinstance(r,dict) and r.get("name")==name]
    if len(matches)!=1:
        raise ValueError("target is not uniquely declared in the repository factory manifest")
    spec=matches[0]
    if spec.get("auto_create") is not True:
        raise ValueError("manifest does not authorize automatic creation for this target")
    if any(ch in name for ch in "/\\ "):
        raise ValueError("invalid repository name")
    return spec

def put_file(owner: str, name: str, path: str, content: str, token: str, api_fn: Callable=api_call) -> None:
    current=api_fn("GET",f"/repos/{owner}/{name}/contents/{path}",token)
    payload={"message":f"chore(factory): seed {path}","content":base64.b64encode(content.encode()).decode("ascii")}
    if current.get("_status") != 404 and isinstance(current.get("sha"),str):
        payload["sha"]=current["sha"]
    api_fn("PUT",f"/repos/{owner}/{name}/contents/{path}",token,payload)

def provision(name: str, manifest: dict[str,Any], token: str, root: Path=ROOT, api_fn: Callable=api_call) -> dict[str,Any]:
    spec=validate_target(name,manifest)
    if not token:
        raise ValueError("VAIXLNS_REPO_ADMIN_TOKEN is required; no repository was changed")
    owner=manifest["owner"]
    existing=api_fn("GET",f"/repos/{owner}/{name}",token)
    if existing.get("_status") != 404:
        return {"status":"EXISTS_NO_MUTATION","repository":f"{owner}/{name}","seeded":False}
    created=api_fn("POST","/user/repos",token,{
        "name":name,"private":manifest.get("policy",{}).get("default_visibility","private")=="private",
        "auto_init":True,"description":spec.get("description","Governed VAIXLNS subsystem")})
    contract_path=root/"registry/repository-orchestration/VAIXLNS_REPOSITORY_CONTRACT.md"
    if not contract_path.is_file():
        raise ValueError("canonical repository contract is missing; repository created but not seeded")
    contract=contract_path.read_text(encoding="utf-8")
    readme="\n".join([f"# {name}","", "Managed under the VAIXLNS Repository Perpetual Engine.","",
        f"- Role: {spec.get('role','TBD')}",f"- System family: {spec.get('system_family','TBD')}",
        "- Lifecycle: SEEDED","- Canonical authority: VAIXLNS","",
        "Created by the manifest-authorized repository factory."])
    workflow="""name: VAIXLNS Conformance
on:
  push:
  pull_request:
permissions:
  contents: read
jobs:
  conformance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Contract present
        run: test -f VAIXLNS_REPOSITORY_CONTRACT.md
"""
    seed={
      "VAIXLNS_REPOSITORY_CONTRACT.md":contract,
      "README.md":readme,
      ".github/workflows/vaixlns-conformance.yml":workflow,
      "docs/DEVELOPMENT_QUEUE.md":"# Development Queue\n\n- [ ] Establish executable entrypoint\n- [ ] Add deterministic tests\n- [ ] Capture verification evidence\n- [ ] Register performance metrics\n- [ ] Link innovation records\n"}
    for path,content in seed.items():
        put_file(owner,name,path,content,token,api_fn)
    return {"status":"CREATED_AND_SEEDED","repository":f"{owner}/{name}","seeded":True,
            "github_html_url":created.get("html_url"),"files_seeded":sorted(seed)}

def main()->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--name",required=True,help="One repository already authorized in the canonical factory manifest")
    p.add_argument("--manifest",type=Path,default=ROOT/"registry/repository-orchestration/REPOSITORY_FACTORY_MANIFEST_V1.json")
    a=p.parse_args()
    try:
        manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
        result=provision(a.name,manifest,os.getenv("VAIXLNS_REPO_ADMIN_TOKEN",""))
    except (OSError,json.JSONDecodeError,ValueError,RuntimeError) as exc:
        print("REPOSITORY_FACTORY_BLOCKED: "+str(exc),file=sys.stderr); return 2
    print(json.dumps(result,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__": raise SystemExit(main())
