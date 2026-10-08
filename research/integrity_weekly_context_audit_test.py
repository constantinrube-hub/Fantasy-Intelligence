#!/usr/bin/env python3
"""Stored evidence audit target, future, leakage, and tamper checks."""
import json
import tempfile
from pathlib import Path
from weekly_pipeline_readiness import stamp
import weekly_context_audit as w


def main():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);now=stamp('2026-10-08T01:10:00Z')
        missing=w.audit(root,2026,5,now)
        assert missing['status']=='ATTENTION' and all(row['status']=='MISSING' for row in missing['datasets'].values())
        path=root/'data/research/trench/2026/prospective/week_05/trench-evidence-v1.json';path.parent.mkdir(parents=True)
        value={'schema':w.TRENCH_SCHEMA,'season':2026,'target_week':5,'generated_at':'2026-10-07T12:00:00Z',
               'source':{'captured_at':'2026-10-07T11:00:00Z','sha256':'hash'},'max_input_week':4,'through_week':4,
               'target_week_realised_stats_excluded':True,'research_only':True,'feature_owner':{'production_validated':False},
               'team_count':1,'teams':{'AAA':{}},'status':'READY_RESEARCH_ONLY'}
        path.write_text(json.dumps(value));before=path.read_bytes()
        assert w.trench(root,2026,5,now)['status']=='BOUND_RESEARCH_ONLY' and path.read_bytes()==before
        for key,changed,reason in [('max_input_week',5,'LEAKAGE'),('season',2025,'TARGET_MISMATCH'),('team_count',2,'COUNT_MISMATCH')]:
            altered=dict(value);altered[key]=changed;path.write_text(json.dumps(altered))
            result=w.audit(root,2026,5,now);assert result['status']=='BLOCKED' and reason in result['datasets']['TRENCH']['reason']
        value['generated_at']='2026-10-08T02:00:00Z';path.write_text(json.dumps(value))
        assert w.trench(root,2026,5,now)['status']=='NOT_OBSERVED_AS_OF'
    # Real archive smoke uses stored owner validators, never provider calls.
    root=Path(__file__).resolve().parents[1]
    result=w.audit(root,2026,5,stamp('2026-10-08T01:10:00Z'))
    assert set(result['datasets'])=={'AVAILABILITY','WEATHER','TRENCH'}
    assert result['network_access'] is False
    print('PASS context audit: explicit absence, immutable reads, target/leakage/count guards, future evidence exclusion')

if __name__=='__main__':main()
