# Automatic Index Path Depth — Protocol V1

## Purpose

The generator `tools/build_index_path_depth.py` builds `registry/index_path_depth.v1.json`
from repository files and their same-repository references. It adds a deterministic
navigation layer without rewriting source documents.

## Depth contract

- Root: `docs/indexes/README.md`.
- Depth `0` is the root index.
- Each directed local Markdown link or resolvable explicit file-path reference contributes one edge.
- A node's depth is the shortest reference-path distance from the root.
- `depth: null` means no path was found; it does not mean the file is invalid or absent.
- `path_chain` records the discovered route. The edge's source line and reference kind provide traceability.
- External URLs are excluded. Traversal outside the repository is blocked. Broken local Markdown links are counted rather than guessed.
- Generated output is excluded from input scanning so the report cannot feed back into itself.

## Historical lineage guard

The repository documents a historical Master Index range of approximately `0001–2750`
across `40+` families but does not expose every original row item-by-item. This feature
computes depth only for paths evidenced by the current repository. It does **not** assign
a historical identifier, infer missing legacy lineage, or promote a proposal to
implemented/verified.

## Run

```bash
python tools/build_index_path_depth.py
python tools/build_index_path_depth.py --check
python -m unittest discover -s tests -p "test_index_path_depth.py"
```

The GitHub Actions workflow regenerates the report during pull requests and, on pushes
to `main`, commits it if the report changed.
