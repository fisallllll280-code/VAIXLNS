"""Fail-closed capability index and read-only GitHub connector (stdlib only)."""
from __future__ import annotations
import argparse, base64, hashlib, json, os, tempfile, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "1.0.0"
class CapabilityDenied(PermissionError):
    """Identity, scope, registration, or input validation failed."""
def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()
def _infer_capability(path: Path) -> str:
    value = path.as_posix().lower()
    if "test" in value: return "verification"
    if any(x in value for x in ("memory", "index", "registry")): return "knowledge-index"
    if any(x in value for x in ("mcp", "connector", "integration")): return "integration"
    if "agent" in value: return "agent-runtime"
    if any(x in value for x in ("govern", "policy")): return "governance"
    return "source-artifact"
def build_capability_index(root: str | Path, *, repo_id: str, source_ref: str) -> dict:
    """Create deterministic file records; timestamp is excluded from the content digest."""
    root = Path(root).resolve()
    suffixes = {".py", ".md", ".json", ".yaml", ".yml", ".toml", ".schema"}
    records = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts: continue
        if path.suffix not in suffixes and path.name not in {"project.genome", "Ω.000"}: continue
        raw = path.read_bytes()
        records.append({"path": path.relative_to(root).as_posix(), "sha256": sha256_bytes(raw),
            "size_bytes": len(raw), "source": {"repository": repo_id, "ref": source_ref},
            "capability": _infer_capability(path)})
    index = {"schema_version": SCHEMA_VERSION, "repository": repo_id, "source_ref": source_ref,
        "generated_at": datetime.now(timezone.utc).isoformat(), "file_count": len(records), "files": records}
    index["content_digest"] = sha256_bytes(canonical_json(records))
    return index
def write_index_atomic(index: Mapping[str, Any], destination: str | Path) -> None:
    """Atomic replacement: failed writes leave the previous index intact."""
    destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, destination)
    except BaseException:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise
class GitHubReadOnlyConnector:
    """Allowlisted read-only GitHub Contents API connector. Never dispatches arbitrary tools."""
    tool_id = "github.read_file"
    def __init__(self, *, token: str | None = None, opener=None):
        self.token = token if token is not None else os.environ.get("GITHUB_TOKEN")
        self.opener = opener or urllib.request.urlopen
    def invoke(self, *, identity: Mapping[str, Any], registered_tools: Mapping[str, Mapping[str, Any]],
               repository: str, path: str, ref: str = "main", timeout: float = 8.0) -> dict:
        if not identity or identity.get("authenticated") is not True or not identity.get("subject"):
            raise CapabilityDenied("IDENTITY_REQUIRED")
        if self.tool_id not in identity.get("scopes", []): raise CapabilityDenied("SCOPE_DENIED")
        profile = registered_tools.get(self.tool_id)
        if not profile or profile.get("status") != "ADMITTED" or profile.get("mode") != "read_only":
            raise CapabilityDenied("TOOL_NOT_REGISTERED")
        if not isinstance(repository, str) or repository.count("/") != 1 or any(x in repository for x in ("..", " ", "\\")):
            raise CapabilityDenied("INVALID_REPOSITORY")
        if not isinstance(path, str) or not path or path.startswith("/") or ".." in Path(path).parts:
            raise CapabilityDenied("INVALID_PATH")
        if not isinstance(ref, str) or not ref or any(c in ref for c in "\r\n"): raise CapabilityDenied("INVALID_REF")
        url = "https://api.github.com/repos/" + repository + "/contents/" + urllib.parse.quote(path, safe="/") + "?ref=" + urllib.parse.quote(ref, safe="")
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "VAIXLNS-capability-gateway/1"}
        if self.token: headers["Authorization"] = "Bearer " + self.token
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with self.opener(request, timeout=timeout) as response:
                body = response.read(2_000_001)
                if len(body) > 2_000_000: raise CapabilityDenied("RESPONSE_TOO_LARGE")
                if getattr(response, "status", 200) != 200: raise CapabilityDenied("UPSTREAM_STATUS")
        except urllib.error.HTTPError as exc: raise CapabilityDenied("UPSTREAM_STATUS") from exc
        data = json.loads(body.decode("utf-8"))
        if not isinstance(data, dict) or data.get("type") != "file" or not isinstance(data.get("content"), str):
            raise CapabilityDenied("INVALID_UPSTREAM_RESPONSE")
        raw = base64.b64decode(data["content"].replace("\n", ""))
        return {"tool_id": self.tool_id, "identity": identity["subject"], "repository": repository,
            "path": path, "ref": ref, "blob_sha": data.get("sha"), "content_sha256": sha256_bytes(raw),
            "size_bytes": len(raw), "content": raw.decode("utf-8"), "read_only": True}
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build a content-addressed capability index")
    parser.add_argument("--root", default="."); parser.add_argument("--repo-id", required=True)
    parser.add_argument("--ref", required=True, help="Commit SHA or branch name")
    parser.add_argument("--output", default="registry/capability-index.v1.json")
    args = parser.parse_args(argv)
    index = build_capability_index(args.root, repo_id=args.repo_id, source_ref=args.ref)
    write_index_atomic(index, args.output)
    print(json.dumps({"status": "INDEX_WRITTEN", "output": args.output,
        "file_count": index["file_count"], "content_digest": index["content_digest"]}, sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
