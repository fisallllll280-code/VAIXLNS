# Unicode Emoji 18.0 Registry — Proposed Integration

Status: **IMPLEMENTED (offline importer only); full Unicode corpus and CI verification NOT_RUN**.

## Provenance

- Unicode Emoji 18.0 charts: https://www.unicode.org/emoji/charts-18.0/
- Normative technical standard: https://www.unicode.org/reports/tr51/tr51-31.html
- Version-pinned machine-readable input: https://www.unicode.org/Public/18.0.0/emoji/emoji-test.txt
- Avoid chart HTML scraping. The authoritative data file must be downloaded and archived independently under the applicable Unicode data terms. Its exact bytes are fingerprinted by SHA-256 in the output.
- Original source text is **not** checked in or overwritten; original identity/order and content provenance remain independently traceable.

## Execution

```sh
python -m unittest discover -s tests -p 'test_unicode_emoji_registry.py' -v
python tools/unicode_emoji_registry.py --input /path/to/emoji-test.txt --output /tmp/vaixlns-emoji-registry-v18.json
```

No network activity, subprocesses, model calls, or side effects beyond explicitly requested output. The parser checks source version, scalar validity, Unicode sequence equivalence, duplicate identities, and qualification status. It retains group/subgroup, emoji version, and English annotation from the pinned file. The identifier includes **version, codepoint sequence and qualification**, never rendered glyph appearance. Deterministic ordering follows the original file.

## Engineering ownership and admission

- Discovery (optional supporting systems): source location and provenance collection only. `NEXENT-SYM` is a **proposed component label**, not a verified NEXENT deployment.
- VLNS: proposed schema / taxonomy integration; **not wired**.
- VX: local deterministic parser (implemented in VAIXLNS only); **not deployed in VX-runtime**.
- VV: proposed independent validation and UI; **not wired**.
- VAIXLNS: isolated importer and test fixtures; no canonical registry mutation.

Acceptance gates before promotion: independently capture source and hash, parse full pinned corpus, compare counts and codepoint equivalence against a second independent implementation, run CI including ZWJ, skin tones, regional flags, tag sequences and invalid UTF-8/Unicode, preserve provenance receipts, conduct Unicode terms review, and obtain human authorization. Never imply a visually rendered glyph is equivalent to an official Unicode-qualified emoji. `project.genome` and `Ω.000` are protected. Do not merge or publish without explicit approval.
