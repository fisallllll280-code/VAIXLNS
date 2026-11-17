# VAIXLNS Conversation Source Ingestion Fabric v1

**State:** IMPLEMENTED ON FEATURE BRANCH; LOCAL SYNTHETIC TESTS PASS; NOT MERGED  
**Branch:** `feat/conversation-source-intake-v1`  
**Task contract:** `.claude/contracts/CONV-INGEST-001.json`  
**Owner:** VAIXLNS / Ω.000 Memory Mind  
**Related fabrics:** Canonical Nexus, VX, XV, VV, ARC-X, Zero-Loss Index

## 1. Decision

Project conversations and user-supplied session exports are first-class source artifacts. They must not remain only as assistant summaries, UI chat history, or manually copied README prose.

This adapter adds a preservation-first intake path to the existing VAIXLNS Zero-Loss Index. It does **not** create a competing index or a new canonical root. It produces immutable source blobs and private normalized records that can later be reconciled into the existing source index, atomic record schema, Nexus graph, and ARC-X evidence chain.

## 2. Existing gap closed

The current repository Zero-Loss Index explicitly limits its scanner to the repository checkout. Before this adapter:
- ChatGPT conversation sources were marked `NOT_CONNECTED_TO_THIS_BUILD`.
- uploaded attachments were not connected to the repository-only scanner;
- a source-specific export adapter was required before claiming conversation ingestion.

This branch implements a **local export adapter**, not a live ChatGPT connector.

## 3. Source boundary

Accepted explicit local inputs:
- ChatGPT export ZIP containing exactly one `conversations.json`;
- direct `conversations.json`;
- UTF-8 `.txt` and `.md` transcripts;
- other files (including image/PDF/binary attachments) preserved as opaque source blobs pending a separately approved extraction adapter.

No automatic account scraping, private session API access, or implicit Library sync is performed. The project owner must explicitly supply the export or files.

## 4. Preservation model

For each input:
1. Read a regular, non-symlink source file within configured byte limits.
2. Calculate SHA-256 over the exact original bytes.
3. Derive a content identity `SRC-*` and a per-occurrence identity `OCC-*`.
4. Preserve exact bytes under `raw/<sha256>.bin`.
5. Add an append-only private occurrence record to `manifests/sources.jsonl`.
6. Emit a private normalized record where parsing is supported.
7. Leave unsupported or malformed sources preserved and explicitly opaque/quarantined.

Repeated identical content reuses the raw content blob but retains each distinct source occurrence. Immutable destination collisions fail closed. The default is dry-run; persistence requires `--apply`.

For ChatGPT conversation JSON, the adapter retains the original conversation object, the complete `mapping` object, parent/child edges, `current_node`, message objects, timestamps and source identifiers. Alternate branches are not linearized or discarded.

For transcript files, decoded text is retained without editorial rewriting. The raw byte copy remains authoritative.

## 5. Private/public separation

**Private vault only**
- raw ZIP, JSON, transcript and attachment bytes;
- normalized conversation records and all message text;
- conversation titles, timestamps, user/message IDs and source filenames;
- private source occurrence manifest.

The vault must be outside every Git checkout. Do not place raw session content in the public VAIXLNS repository.

**Public repository**
- adapter code, schema, tests and this architecture contract;
- aggregate progress status only;
- no raw conversation text, titles, original filenames, user identifiers, attachment data, or per-source content hashes from the owner's actual conversation corpus.

A hash is a content fingerprint, not a privacy guarantee. Do not publish real-source hashes merely because they omit readable text.

## 6. Canonical pipeline and authority

```text
OWNER-SUPPLIED SOURCE
        |
        v
SOURCE IDENTITY + SHA-256 + OCCURRENCE
        |
        v
PRIVATE RAW VAULT (IMMUTABLE)
        |
        +---- unsupported / malformed ----> OPAQUE or QUARANTINED
        |
        v
NORMALIZATION (STRUCTURE PRESERVED)
        |
        v
ZERO-LOSS SOURCE / ATOMIC RECORD CANDIDATES
        |
        v
NEXUS LINK CANDIDATES + LINEAGE
        |
        v
ARC-X CLAIM / EVIDENCE RECONSTRUCTION
        |
        v
VV INDEPENDENT REVIEW
        |
        v
GOVERNANCE / CANONICAL ADMISSION (SEPARATE DECISION)
```

Intake does not grant canonical authority. Extracted claims are not automatically true. A normalized conversation is a source record, not proof that every statement inside the conversation is correct. Automatic extraction must remain SOURCE / ATOMIC / UNRESOLVED as appropriate; it must never promote an idea to `CANONICAL`, `IMPLEMENTED` or `VERIFIED`.

## 7. Placement within the existing architecture

- **Ω.000 Memory Mind:** source identity, immutable retrieval, lineage, history, conflict and gap tracking.
- **NEXENT / XV:** discover and derive candidate entities, terminology, architecture hypotheses and task plans from preserved sources.
- **Canonical Nexus:** link source records to systems, capabilities, contracts and dependencies only when the relation is explicit or evidenced.
- **VX:** execute authorized extraction/indexing tasks under bounded resource and path policies.
- **VV:** independently verify parser behavior, branch preservation, privacy projection and regression behavior.
- **ARC-X:** bind claims to their exact source locations and evidence; preserve contradictions and source disagreements.

The six responsibilities remain separate. No memory or discovery component can approve its own canonical update.

## 8. Run

Dry-run first:

```bash
python scripts/ingest_conversation_sources.py \
  --source /secure/export/conversations.zip \
  --source /secure/transcripts/session-01.txt \
  --vault-dir /secure/private/VAIXLNS_SOURCE_VAULT
```

Persist only after inspecting the dry-run report:

```bash
python scripts/ingest_conversation_sources.py \
  --source /secure/export/conversations.zip \
  --source /secure/transcripts/session-01.txt \
  --vault-dir /secure/private/VAIXLNS_SOURCE_VAULT \
  --apply
```

The CLI accepts repeated `--source` arguments. Its default vault boundary rejects every Git checkout. The optional privacy-minimized public manifest format is defined by `schemas/conversation-source-manifest.v1.schema.json`; it should be used only when publishing per-source hashes has been reviewed for privacy implications.

## 9. Limits

- This is a local, owner-supplied export adapter, not live ChatGPT synchronization.
- It does not retrieve unexported conversations from the account.
- It does not OCR images or extract PDF/office document semantics.
- Attachments and unsupported binary files are byte-preserved and left pending.
- A plain SHA-256 hash proves byte identity relative to those bytes, not truth, authorship, authorization, completeness or correctness.
- A successful parse does not mean all historical ChatGPT sessions were supplied.
- The historical `0001–2750` range remains approximate until the original row-by-row index is acquired and reconciled.

## 10. Verification

Synthetic local tests cover:
- JSON conversation and branched mapping preservation;
- ZIP path traversal safety (archive is read but never extracted);
- verbatim text source retention;
- idempotent immutable storage;
- duplicate byte content with separate occurrence provenance;
- public projection content-minimization;
- Git-checkout vault rejection;
- malformed JSON quarantine without source loss;
- opaque binary preservation.

Exact commands:

```bash
python -m py_compile scripts/ingest_conversation_sources.py tests/test_conversation_source_ingestion.py
python -m unittest discover -s tests -p 'test_conversation_source_ingestion.py' -v
python -m json.tool schemas/conversation-source-manifest.v1.schema.json >/dev/null
```

The local synthetic test result is 9/9 passing. GitHub Actions has not yet run for this feature branch; do not treat local tests as CI evidence or independent VV approval.

## 11. Next governed transitions

1. Obtain an owner-supplied full ChatGPT export and any additional conversation artifacts not included in this workspace.
2. Reconcile the private vault with the complete supplied project corpus by byte hash and per-source occurrence.
3. Select/confirm a dedicated private GitHub destination before transferring any raw sources.
4. Add an approved private-vault snapshot receipt and a privacy-reviewed public aggregate status record.
5. Run the adapter's CI and independent VV review on the exact pull-request head.
6. Reconcile source-derived atomic candidates into the existing Zero-Loss views and Nexus without overwriting historical records.
7. Canonical promotion remains a separate explicit governance decision.

**No raw session material has been committed to this public repository.**
