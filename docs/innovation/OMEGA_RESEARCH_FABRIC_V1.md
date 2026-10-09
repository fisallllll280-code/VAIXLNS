# Ω Research Fabric v1

**State:** deterministic local incremental index + opt-in public search adapters + explicitly configured read-only server adapters.  
**Authority:** VAIXLNS governance; this module is an evidence-discovery projection, not the canonical genome.  
**Systems:** VAIXLNS, VLNS, VX, NEXNET; historical NEXENT/VV/XV references remain discoverable.

## Purpose and limits

The fabric indexes local project files, extracts system and Ω identifiers and engineering signal classes, then combines local results with explicit public-source discovery and configured server search endpoints. A persistent SQLite/FTS5 index avoids FTS writes for content-identical files between runs.

This is not a universal crawler and cannot claim to search every worldwide source. It queries the enabled providers, local project, and server adapters listed by the operator. Remote records are discovery leads, not engineering proof.

## Local indexing and retrieval

~~~bash
python scripts/omega_research_fabric.py --root . --output build/omega-research-results.json
python scripts/omega_research_fabric.py --root . --query "VX proof provenance" --output build/omega-research-results.json
~~~

## Explicit global research

Network access is opt-in, through public API adapters for Crossref, OpenAlex, arXiv, and GitHub repository search.

~~~bash
python scripts/omega_research_fabric.py --root . --query "deterministic engineering verification" --research --limit 10 --output build/omega-research-results.json
~~~

Official API references:
- Crossref REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- OpenAlex API: https://help.openalex.org/api/
- arXiv API: https://info.arxiv.org/help/api/index.html
- GitHub REST search: https://docs.github.com/en/rest/search/search

Optional environment variables: GITHUB_TOKEN, OPENALEX_API_KEY, VAIXLNS_MAILTO. Values are never printed. GitHub uses repository search, not code search. Provider results and limits vary; network calls use HTTPS, bounded response sizes, short timeouts, and at most 25 results per provider.

## Configured read-only server adapters

Create a reviewed JSON manifest, for example:

~~~json
{
  "schema": "vaixlns.omega-server-manifest.v1",
  "servers": [
    {
      "server_id": "vx-dev",
      "base_url": "https://vx.example.internal",
      "health_path": "/health",
      "search_path": "/search"
    }
  ]
}
~~~

~~~bash
python scripts/omega_research_fabric.py --root . --query "event replay proof" --server-manifest config/omega-servers.json --output build/omega-research-results.json
~~~

The adapter issues GET-only requests. The health path must return JSON; the search path should return JSON shaped as: { "results": [ { "id": "...", "omega_id": "...", "title": "...", "url": "...", "summary": "..." } ] }. Only HTTPS is accepted for non-loopback hosts; embedded credentials and path traversal are rejected. No credentials are sent in v1. A server being healthy does not prove that its search index is complete or its results correct.

## Ω-shaped result contract

The output schema is vaixlns.omega-research-fabric.v1 and includes:
- index summary: changed / unchanged / deleted files and inventory SHA-256;
- local_results: file path, full-file SHA-256, matched snippet, Ω references, system references, engineering signal types and retrieval score;
- remote_discoveries: stable provider/source identity, URL, title, abstract metadata, normalized-record hash and DISCOVERED_UNVERIFIED state;
- provider_status and server_status: explicit adapter outcomes;
- result_sha256: fingerprint of the result object before this field is attached.

Hash semantics matter. Local SHA-256 covers full file bytes. A remote content hash covers normalized returned metadata, not the complete paper or repository. Neither a search hit nor a high ranking establishes correctness, originality, security, or runtime behavior.

## Performance model

- SQLite persists under .vaixl_ns, excluded from the file walk.
- Every inspected file gets a content hash; a matching hash skips database and FTS updates.
- Changed content is updated and deleted paths are removed.
- FTS5 indexes bounded UTF-8 text (up to 2 MB per file), while the hash covers full bytes.
- Result limits, timeouts and byte caps bound external requests.
- Retrieval ranking is a relevance heuristic. Benchmark real repositories before claiming measured latency improvements.

## State and security rules

- Indexed code is never executed.
- Public network search requires --research; server calls require an explicit manifest.
- Remote findings are DISCOVERED_UNVERIFIED, never automatically VERIFIED or CANONICAL.
- No live LLM dispatch, embeddings, full-text PDF ingestion, arbitrary web crawling, privileged server actions, repository-wide write access, or production deployment is included.
- Additional source adapters and authenticated server connectors require separate contract tests, security review, and governance approval.

Offline tests: python -m unittest tests.test_omega_research_fabric -v
