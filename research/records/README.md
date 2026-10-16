# Research Records

Store one JSON research record per file using the schema at `schemas/research-comparison-record.schema.json`.

Rules:
- Stable IDs are never reused.
- Preserve original sources and record lineage.
- Do not place secrets, private user data, or credentials in records.
- Do not mark a record VERIFIED without evidence references, recorded results, and accepted review metadata.
- Prefer immutable source URLs and pinned commit SHAs or document versions.
- Treat empty collections as no records yet, not as proof that the research domain is complete.
