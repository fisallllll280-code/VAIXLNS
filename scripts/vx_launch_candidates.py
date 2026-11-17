"""Read-only proposal ranking from the existing source-bound VAIXLNS innovation index.
Scores represent engineering triage priority, NEVER likelihood of commercial success.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

KEYWORDS = {
    'release_assurance': ('proof', 'verification', 'test', 'assurance', 'replay', 'evidence'),
    'agent_workflow': ('agent', 'orchestrat', 'workflow', 'runtime', 'capability'),
    'index_recovery': ('index', 'memory', 'recover', 'lineage', 'archive'),
    'commerce': ('econom', 'financ', 'exchange', 'market', 'revenue'),
}

def shortlist(payload: dict, *, source_revision: str, limit: int = 10) -> dict:
    if not isinstance(payload, dict) or not isinstance(payload.get('items'), list):
        raise ValueError('Expected innovation-operation index with items array')
    if not isinstance(source_revision, str) or len(source_revision) != 40 or any(c not in '0123456789abcdef' for c in source_revision):
        raise ValueError('Pinned full source revision SHA required')
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 50:
        raise ValueError('limit must be between 1 and 50')
    candidates = []
    seen = set()
    for item in payload['items']:
        if not isinstance(item, dict):
            continue
        uid, name = item.get('canonical_id'), item.get('name')
        refs = item.get('source_refs', [])
        if not isinstance(uid, str) or not uid or uid in seen or not isinstance(name, str) or not name.strip():
            continue
        seen.add(uid)
        if not isinstance(refs, list) or not refs or not all(isinstance(r, str) and r for r in refs):
            continue
        haystack = ' '.join([name, str(item.get('family','')), str(item.get('description',''))]).lower()
        groups = [g for g, keys in KEYWORDS.items() if any(k in haystack for k in keys)]
        if not groups:
            continue
        evidence = item.get('evidence_refs') if isinstance(item.get('evidence_refs'), list) else []
        score = 10 * len(groups) + (5 if item.get('status') == 'IMPLEMENTED' else 0) + (3 if evidence else 0)
        candidates.append({'id':uid,'name':name,'themes':groups,'review_priority':score,
                           'source_refs':refs,'source_status':item.get('status','UNKNOWN'),
                           'market_demand':'UNKNOWN','success_probability':None,
                           'next_gate':'VALIDATE_CUSTOMER_PAIN_AND_DELIVERY_EVIDENCE'})
    candidates.sort(key=lambda x:(-x['review_priority'], x['id']))
    return {'schema':'vx-launch-candidates-v1','source_revision':source_revision,
            'selection':'DETERMINISTIC_TRIAGE_NOT_PROBABILITY',
            'records_examined':len(payload['items']), 'candidate_count':len(candidates),
            'shortlist':candidates[:limit], 'automatic_outreach':False,
            'automatic_publication':False, 'external_spend_sar':0}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--index',type=Path,default=Path('registry/innovation-operation-index.v1.json'))
    p.add_argument('--revision',required=True)
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    raw=args.index.read_bytes()
    result=shortlist(json.loads(raw),source_revision=args.revision)
    result['source_sha256']=hashlib.sha256(raw).hexdigest()
    data=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(data,encoding='utf-8')
    else:
        print(data,end='')
if __name__=='__main__':main()
