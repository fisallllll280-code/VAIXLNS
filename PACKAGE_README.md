# VAIXLNS Knowledge Genome Engineering Slice

This package adds a deterministic, non-destructive file-level inventory probe to the VAIXLNS ARC-X / Ω.000 engineering path.

- `scripts/knowledge_genome.py`: standard-library scanner and baseline comparison.
- `schemas/knowledge-genome.schema.json`: report contract.
- `tests/test_knowledge_genome.py`: deterministic and safety-focused tests.
- `docs/KNOWLEDGE_GENOME_ENGINEERING_V1.md`: integration, scope and admission criteria.
- `.github/workflows/knowledge-genome.yml`: CI test and smoke run.

No GitHub repository state is changed by running the scanner. This package itself is an implementation candidate until tests and the target repository's CI provide execution evidence.
