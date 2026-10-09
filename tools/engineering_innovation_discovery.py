#!/usr/bin/env python3
"""Evidence-first discovery of engineering software releases and source changes."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen

MAX_TIMEOUT = 20.0
MAX_BYTES = 2 * 1024 * 1024
GITHUB_API = "https://api.github.com"
GITLAB_HOSTS = {"gitlab.com", "gitlab.onelab.info"}
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
PROJECT_RE = re.compile(r"^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)+$")
TERMS = {
    "adaptive", "aero", "algorithm", "analysis", "assembly", "benchmark",
    "cad", "cae", "calculation", "convergence", "crash", "design",
    "electromagnetic", "element", "fea", "finite", "flow", "geometry",
    "gpu", "healing", "heat", "hpc", "kernel", "mesh", "meshing", "model",
    "multiphysics", "numerical", "optimization", "parallel", "performance",
    "physics", "precision", "simulation", "solver", "step", "stress",
    "thermal", "topology", "turbulence", "validation", "visualization",
}
DEFAULT_MANIFEST = Path(__file__).resolve().parents[1] / "registry/engineering/ENGINEERING_INNOVATION_SOURCES_V1.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def text_value(value: Any, maximum: int = 1400) -> str:
    if value is None:
        return ""
    return str(value)[:maximum]


def validate_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("manifest needs a non-empty sources array")
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("every source must be an object")
        sid = source.get("id")
        if not isinstance(sid, str) or not sid or sid in seen:
            raise ValueError("every source id must be non-empty and unique")
        seen.add(sid)
        provider = source.get("provider")
        if provider == "github":
            if not isinstance(source.get("repository"), str) or not REPO_RE.fullmatch(source["repository"]):
                raise ValueError(f"{sid}: invalid GitHub repository")
        elif provider == "gitlab":
            if source.get("host") not in GITLAB_HOSTS:
                raise ValueError(f"{sid}: GitLab host not allowlisted")
            if not isinstance(source.get("project_path"), str) or not PROJECT_RE.fullmatch(source["project_path"]):
                raise ValueError(f"{sid}: invalid GitLab project path")
        else:
            raise ValueError(f"{sid}: provider must be github or gitlab")
    return sources


def request_json(
    url: str, provider: str, timeout: float,
    opener: Callable[..., Any] = urlopen,
    environ: dict[str, str] | None = None,
) -> Any:
    env = os.environ if environ is None else environ
    headers = {"Accept": "application/json", "User-Agent": "VAIXLNS-Engineering-Discovery/1.0"}
    if provider == "github":
        headers["X-GitHub-Api-Version"] = "2022-11-28"
        token = env.get("GITHUB_TOKEN") or env.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    elif provider == "gitlab":
        # Never forward a gitlab.com credential to the separate Gmsh host.
        target_host = urlsplit(url).hostname
        token_name = "GITLAB_TOKEN" if target_host == "gitlab.com" else "GITLAB_ONELAB_INFO_TOKEN" if target_host == "gitlab.onelab.info" else ""
        if token_name and env.get(token_name):
            headers["PRIVATE-TOKEN"] = env[token_name]
    try:
        with opener(Request(url, headers=headers, method="GET"), timeout=min(max(timeout, 1.0), MAX_TIMEOUT)) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise RuntimeError("RESPONSE_TOO_LARGE")
            return json.loads(raw.decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"HTTP_{exc.code}") from None
    except URLError as exc:
        reason = getattr(exc, "reason", None)
        raise RuntimeError(f"NETWORK_{type(reason).__name__ if reason is not None else 'ERROR'}") from None
    except (TimeoutError, OSError):
        raise RuntimeError("NETWORK_TIMEOUT_OR_IO_ERROR") from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise RuntimeError("INVALID_JSON_RESPONSE") from None


def github_fetch(source: dict[str, Any], timeout: float) -> dict[str, Any]:
    slug = source["repository"]
    url = f"{GITHUB_API}/repos/{slug}"
    repo = request_json(url, "github", timeout)
    releases = request_json(url + "/releases?per_page=3", "github", timeout)
    commits = request_json(url + "/commits?per_page=5", "github", timeout)
    lic = repo.get("license") if isinstance(repo.get("license"), dict) else {}
    release_rows = []
    for item in releases if isinstance(releases, list) else []:
        if not isinstance(item, dict) or item.get("draft"):
            continue
        release_rows.append({
            "tag": text_value(item.get("tag_name"), 200),
            "name": text_value(item.get("name") or item.get("tag_name"), 240),
            "published_at": text_value(item.get("published_at"), 80),
            "url": text_value(item.get("html_url"), 500),
            "body": text_value(item.get("body"), 1600),
            "prerelease": bool(item.get("prerelease")),
        })
    commit_rows = []
    for item in commits if isinstance(commits, list) else []:
        if not isinstance(item, dict):
            continue
        details = item.get("commit") if isinstance(item.get("commit"), dict) else {}
        author = details.get("author") if isinstance(details.get("author"), dict) else {}
        message = text_value(details.get("message"), 1000)
        commit_rows.append({
            "sha": text_value(item.get("sha"), 80),
            "title": message.splitlines()[0] if message else "",
            "committed_at": text_value(author.get("date"), 80),
            "url": text_value(item.get("html_url"), 500),
        })
    return {
        "provider": "github", "slug": slug,
        "repository_url": text_value(repo.get("html_url") or source.get("repository_url"), 500),
        "description": text_value(repo.get("description"), 1000),
        "homepage": text_value(repo.get("homepage"), 500),
        "default_branch": text_value(repo.get("default_branch"), 200),
        "pushed_at": text_value(repo.get("pushed_at"), 80),
        "updated_at": text_value(repo.get("updated_at"), 80),
        "stars": repo.get("stargazers_count"), "forks": repo.get("forks_count"),
        "archived": bool(repo.get("archived")), "license_spdx": text_value(lic.get("spdx_id"), 120),
        "topics": repo.get("topics", []) if isinstance(repo.get("topics"), list) else [],
        "latest_release_tag": release_rows[0]["tag"] if release_rows else None,
        "latest_release_published_at": release_rows[0]["published_at"] if release_rows else None,
        "head_sha": commit_rows[0]["sha"] if commit_rows else None,
        "recent_releases": release_rows, "recent_commits": commit_rows,
    }


def gitlab_fetch(source: dict[str, Any], timeout: float) -> dict[str, Any]:
    host = source["host"]
    base = f"https://{host}/api/v4/projects/{quote(source['project_path'], safe='')}"
    project = request_json(base, "gitlab", timeout)
    releases = request_json(base + "/releases?per_page=3", "gitlab", timeout)
    branch = text_value(project.get("default_branch") or "master", 200)
    commits = request_json(base + "/repository/commits?per_page=5&ref_name=" + quote(branch, safe=""), "gitlab", timeout)
    release_rows = []
    for item in releases if isinstance(releases, list) else []:
        if isinstance(item, dict):
            link = item.get("_links") if isinstance(item.get("_links"), dict) else {}
            release_rows.append({
                "tag": text_value(item.get("tag_name"), 200),
                "name": text_value(item.get("name") or item.get("tag_name"), 240),
                "published_at": text_value(item.get("released_at"), 80),
                "url": text_value(link.get("self"), 500),
                "body": text_value(item.get("description"), 1600),
                "prerelease": False,
            })
    commit_rows = []
    for item in commits if isinstance(commits, list) else []:
        if isinstance(item, dict):
            commit_rows.append({
                "sha": text_value(item.get("id"), 80),
                "title": text_value(item.get("title"), 400),
                "committed_at": text_value(item.get("committed_date"), 80),
                "url": text_value(item.get("web_url"), 500),
            })
    licence = project.get("license") if isinstance(project.get("license"), dict) else {}
    return {
        "provider": "gitlab", "slug": text_value(project.get("path_with_namespace") or source["project_path"], 300),
        "repository_url": text_value(project.get("web_url") or source.get("repository_url"), 500),
        "description": text_value(project.get("description"), 1000),
        "homepage": text_value(project.get("web_url"), 500),
        "default_branch": branch, "pushed_at": text_value(project.get("last_activity_at"), 80),
        "updated_at": text_value(project.get("last_activity_at"), 80),
        "stars": project.get("star_count"), "forks": project.get("forks_count"),
        "archived": bool(project.get("archived")), "license_spdx": text_value(licence.get("key"), 120),
        "topics": project.get("topics", []) if isinstance(project.get("topics"), list) else [],
        "latest_release_tag": release_rows[0]["tag"] if release_rows else None,
        "latest_release_published_at": release_rows[0]["published_at"] if release_rows else None,
        "head_sha": commit_rows[0]["sha"] if commit_rows else None,
        "recent_releases": release_rows, "recent_commits": commit_rows,
    }


def prior_snapshots(baseline: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(baseline, dict) or not isinstance(baseline.get("source_snapshots"), list):
        return {}
    return {x["source_id"]: x for x in baseline["source_snapshots"] if isinstance(x, dict) and isinstance(x.get("source_id"), str)}


def classify(snapshot: dict[str, Any], previous: dict[str, Any] | None) -> tuple[str, str, list[str]]:
    if snapshot.get("fetch_status") != "SUCCESS":
        return "SOURCE_FETCH_FAILED", "NONE", []
    if previous is None:
        return "INITIAL_OBSERVATION", "BASELINE", []
    changes = []
    if snapshot.get("latest_release_tag") and snapshot.get("latest_release_tag") != previous.get("latest_release_tag"):
        changes.append("LATEST_RELEASE_TAG_CHANGED")
    if snapshot.get("head_sha") and snapshot.get("head_sha") != previous.get("head_sha"):
        changes.append("HEAD_COMMIT_CHANGED")
    if snapshot.get("license_spdx") != previous.get("license_spdx"):
        changes.append("LICENSE_METADATA_CHANGED")
    if snapshot.get("default_branch") != previous.get("default_branch"):
        changes.append("DEFAULT_BRANCH_CHANGED")
    if "LATEST_RELEASE_TAG_CHANGED" in changes:
        return "NEW_RELEASE_SIGNAL", "HIGH", changes
    if "LICENSE_METADATA_CHANGED" in changes or "DEFAULT_BRANCH_CHANGED" in changes:
        return "SOURCE_POLICY_OR_BRANCH_CHANGE", "HIGH", changes
    if "HEAD_COMMIT_CHANGED" in changes:
        return "SOURCE_ACTIVITY_CHANGED", "MEDIUM", changes
    return "NO_CHANGE_OBSERVED", "LOW", changes


def candidate_terms(source: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    corpus = " ".join([
        text_value(snapshot.get("description")),
        " ".join(text_value(x) for x in source.get("focus", [])),
        " ".join(text_value(x.get("name")) + " " + text_value(x.get("body")) for x in snapshot.get("recent_releases", []) if isinstance(x, dict)),
        " ".join(text_value(x.get("title")) for x in snapshot.get("recent_commits", []) if isinstance(x, dict)),
    ]).lower()
    return sorted(term for term in TERMS if re.search(r"\b" + re.escape(term) + r"\b", corpus))


def collect(
    manifest: dict[str, Any], baseline: dict[str, Any] | None = None,
    timeout: float = 12.0,
    fetchers: dict[str, Callable[[dict[str, Any], float], dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    sources = validate_manifest(manifest)
    previous = prior_snapshots(baseline)
    providers = fetchers or {"github": github_fetch, "gitlab": gitlab_fetch}
    snapshots = []
    findings = []
    for source in sources:
        try:
            snap = providers[source["provider"]](source, timeout)
            snap["fetch_status"] = "SUCCESS"
            snap["source_id"] = source["id"]
            snap["observed_at"] = now()
            snap["evidence_sha256"] = hashlib.sha256(json.dumps(snap, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
        except Exception as exc:
            snap = {
                "source_id": source["id"], "provider": source["provider"],
                "slug": source.get("repository") or source.get("project_path"),
                "fetch_status": "FAILED", "error_code": text_value(str(exc), 120), "observed_at": now(),
            }
        state, priority, changes = classify(snap, previous.get(source["id"]))
        terms = candidate_terms(source, snap) if snap.get("fetch_status") == "SUCCESS" else []
        score = min(100, (25 if state == "NEW_RELEASE_SIGNAL" else 10 if state == "SOURCE_ACTIVITY_CHANGED" else 0)
                    + min(45, 3 * len(terms))
                    + (15 if source.get("priority") == "P1" else 5 if source.get("priority") == "P2" else 0))
        findings.append({
            "source_id": source["id"], "title": source.get("repository") or source.get("project_path"),
            "domain": source.get("domain"), "official_url": source.get("official_url"),
            "repository_url": source.get("repository_url"), "integration_role": source.get("integration_role"),
            "state": state, "priority": priority, "change_types": changes,
            "engineering_terms": terms, "triage_score": score, "review_required": True,
            "fetch_status": snap.get("fetch_status"),
            "note": "Activity, releases and keywords are triage signals, not proof of novelty or engineering fitness.",
        })
        snapshots.append(snap)
    counts = {}
    for item in findings:
        counts[item["state"]] = counts.get(item["state"], 0) + 1
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NONE": 3}
    findings.sort(key=lambda x: (order.get(x["priority"], 3), -x["triage_score"], x["source_id"]))
    return {
        "schema_id": "VAIXLNS.ENGINEERING_INNOVATION_DISCOVERY_REPORT",
        "schema_version": "1.0.0", "observed_at": now(),
        "manifest_id": manifest.get("schema_id"), "manifest_version": manifest.get("schema_version"),
        "baseline_available": bool(previous), "source_count": len(sources),
        "successful_source_count": sum(x.get("fetch_status") == "SUCCESS" for x in snapshots),
        "failed_source_count": sum(x.get("fetch_status") != "SUCCESS" for x in snapshots),
        "state_counts": counts,
        "disclaimer": "Activity and release signals do not establish scientific novelty, correctness, license compatibility, security, or production readiness.",
        "findings": findings, "source_snapshots": snapshots,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# VAIXLNS Engineering Innovation Discovery", "",
        f"- Observed at: {report.get('observed_at')}",
        f"- Sources: {report.get('source_count')} total; {report.get('successful_source_count')} successful; {report.get('failed_source_count')} failed",
        f"- Baseline available: {report.get('baseline_available')}",
        f"- States: {json.dumps(report.get('state_counts', {}), ensure_ascii=False, sort_keys=True)}", "",
        "> Source activity is an evidence lead, not a claim of novelty or verified engineering quality.", "",
    ]
    rank = {"NEW_RELEASE_SIGNAL": 0, "SOURCE_POLICY_OR_BRANCH_CHANGE": 1, "SOURCE_ACTIVITY_CHANGED": 2,
            "INITIAL_OBSERVATION": 3, "NO_CHANGE_OBSERVED": 4, "SOURCE_FETCH_FAILED": 5}
    for finding in sorted(report.get("findings", []), key=lambda x: (rank.get(x.get("state"), 9), -x.get("triage_score", 0), x.get("source_id", ""))):
        snap = next((x for x in report.get("source_snapshots", []) if x.get("source_id") == finding.get("source_id")), {})
        lines += [
            f"## {finding.get('source_id')} — {finding.get('state')}", "",
            f"- Domain: {finding.get('domain')}",
            f"- Priority: {finding.get('priority')}; triage score: {finding.get('triage_score')}",
            f"- Official source: {finding.get('official_url')}",
            f"- Repository: {finding.get('repository_url')}",
            f"- Integration role: {finding.get('integration_role')}",
            f"- Engineering terms: {', '.join(finding.get('engineering_terms') or []) or 'none matched'}",
            f"- Change types: {', '.join(finding.get('change_types') or []) or 'none'}", "",
        ]
        if snap.get("fetch_status") != "SUCCESS":
            lines += [f"- Fetch result: {snap.get('error_code', 'unknown error')}", ""]
            continue
        lines += [
            f"- Description: {snap.get('description') or 'not provided'}",
            f"- Last source activity: {snap.get('pushed_at') or 'unknown'}",
            f"- License metadata: {snap.get('license_spdx') or 'unknown'}; verify the actual license before integration",
            "- Recent releases:",
        ]
        releases = snap.get("recent_releases", [])
        if releases:
            for release in releases:
                lines.append(f"  - [{release.get('name') or release.get('tag')}]({release.get('url')}) — {release.get('published_at') or 'date unknown'}")
                body = (release.get("body") or "").replace("\n", " ").strip()
                if body:
                    lines.append(f"    - Notes: {body[:500]}")
        else:
            lines.append("  - No releases returned by the source API.")
        lines.append("- Recent commits:")
        commits = snap.get("recent_commits", [])
        if commits:
            for commit in commits[:5]:
                lines.append(f"  - [{commit.get('title') or commit.get('sha')}]({commit.get('url')}) — {commit.get('committed_at') or 'date unknown'}")
        else:
            lines.append("  - No commit records returned.")
        lines.append("")
    lines += [
        "## Required engineering review", "",
        "1. Read the upstream release notes and linked source changes.",
        "2. Compare the candidate with the VAIXLNS/NEXENT innovation index and previously observed snapshots.",
        "3. Check license, dependency closure, supported platforms, security posture and reproducibility.",
        "4. Run a bounded reference problem with units, tolerances, environment fingerprint and failure cases.",
        "5. Keep the result a proposal until independent verification and explicit VAIXLNS adoption approval.", "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--baseline", type=Path, help="Prior report JSON for change comparison.")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/engineering-discovery"))
    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline and args.baseline.is_file() else None
        report = collect(manifest, baseline, min(max(args.timeout_seconds, 1.0), MAX_TIMEOUT))
        report["manifest_sha256"] = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        args.output_dir.mkdir(parents=True, exist_ok=True)
        json_path = args.output_dir / "engineering-discovery-report.json"
        md_path = args.output_dir / "engineering-discovery-report.md"
        json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        md_path.write_text(render_markdown(report), encoding="utf-8")
        print(json.dumps({
            "json_report": str(json_path), "markdown_report": str(md_path),
            "source_count": report["source_count"], "successful_source_count": report["successful_source_count"],
            "failed_source_count": report["failed_source_count"], "baseline_available": report["baseline_available"],
            "failed_sources": [
                {"source_id": item.get("source_id"), "slug": item.get("slug"), "error_code": item.get("error_code")}
                for item in report["source_snapshots"] if item.get("fetch_status") != "SUCCESS"
            ],
            "state_counts": report["state_counts"],
        }, ensure_ascii=False, indent=2))
        return 0 if report["successful_source_count"] > 0 else 1
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"discovery configuration error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
