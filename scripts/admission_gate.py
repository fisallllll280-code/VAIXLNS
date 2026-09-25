#!/usr/bin/env python3
"""Mechanical first-pass admission gate for a VAIXLNS repository.

This gate checks repository structure and emits a machine-readable verdict.
It does not pretend that structural presence proves runtime correctness.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

REQUIRED = {
    "identity": ["README.md"],
    "contract": ["VAIXLNS_REPOSITORY_CONTRACT.md"],
    "conformance": [".github/workflows/vaixlns-conformance.yml"],
}

def exists(root: Path, candidates: list[str]) -> bool:
    return any((root / p).exists() for p in candidates)

def main() -> int:
    root = Path(os.getenv('VAIXLNS_REPOSITORY_ROOT', '.')).resolve()
    result = {}
    result['identity'] = 'PASS' if exists(root, REQUIRED['identity']) else 'FAIL'
    result['contract'] = 'PASS' if exists(root, REQUIRED['contract']) else 'FAIL'
    result['conformance'] = 'PASS' if exists(root, REQUIRED['conformance']) else 'FAIL'
    has_src = (root / 'src').exists() or (root / 'app').exists() or (root / 'lib').exists()
    has_tests = (root / 'tests').exists() or (root / 'test').exists()
    has_workflow = (root / '.github' / 'workflows').exists()
    result['source'] = 'PASS' if has_src else 'N/A'
    result['build'] = 'PASS' if has_workflow else 'FAIL'
    result['execution'] = 'N/A' if not has_src else 'PENDING_RUNTIME_EVIDENCE'
    result['tests'] = 'PASS' if has_tests else ('N/A' if not has_src else 'FAIL')
    result['security'] = 'PENDING_EVIDENCE'
    result['performance'] = 'PENDING_EVIDENCE'
    result['provenance'] = 'PASS' if exists(root, ['docs', 'registry']) else 'FAIL'
    result['recovery'] = 'N/A' if not has_src else 'PENDING_EVIDENCE'
    result['evidence'] = 'PASS' if (root / 'docs').exists() else 'FAIL'
    hard = ['identity','contract','conformance','build','provenance','evidence']
    result['admission'] = 'ADMITTED' if all(result[k] == 'PASS' for k in hard) else 'BLOCKED'
    print(json.dumps(result, indent=2))
    return 0 if result['admission'] == 'ADMITTED' else 1

if __name__ == '__main__':
    raise SystemExit(main())