from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / 'registry' / 'omega' / 'VAIXLNS_GLOBAL_FABRIC.json'

def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    required = {'schema','canonical_root','architecture','lifecycle','repositories','status_policy'}
    missing = required - data.keys()
    if missing: raise SystemExit(f'missing manifest fields: {sorted(missing)}')
    if data['canonical_root'] != 'VAIXLNS': raise SystemExit('canonical root mismatch')
    if data['architecture'] != ['VAIXLNS','V','VV','VX','XV']: raise SystemExit('architecture drift')
    expected = ['INTENT','PLAN','AUTHORIZE','EXECUTE','OBSERVE','VERIFY','PROVE','RECORD','REPLAY','FAILURE','RECOVERY','VERIFY']
    if data['lifecycle'] != expected: raise SystemExit('lifecycle drift')
    if not data['repositories']: raise SystemExit('empty repository inventory')
    print(f"VAIXLNS federation manifest valid: {len(data['repositories'])} repositories")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
