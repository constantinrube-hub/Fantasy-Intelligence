#!/usr/bin/env python3
"""Stable recommendation identity and separately bound action observations."""
import json,tempfile
from pathlib import Path
from weekly_pipeline_readiness import stamp,digest
import weekly_decision_ledger as w


def main():
    source={'path':'owner.json','sha256':'abc','status':'AVAILABLE','generated_at':'2026-10-08T01:00:00Z'}
    league={'league_id':'1','season':2026,'week':5,'input_readiness':{'current_scoring_signature':'sig'}}
    rec={'player_id':'123','recommended_bid':7,'confidence':'LOW','rationale':['Original owner reason']}
    first=w.decision('WINDOW_1D',source,league,'WAIVER_PLAN',rec,'2026-10-08T01:00:00Z')
    retry=w.decision('WINDOW_1D',source,league,'WAIVER_PLAN',rec,'2026-10-08T01:00:00Z')
    assert first==retry and first['user_action']['status']=='NOT_OBSERVED' and first['outcome']['status']=='NOT_OBSERVED'
    assert first['ex_ante_quality']=='NOT_ASSESSED' and first['explanation']['synthesized_drivers'] is False
    changed=w.decision('WINDOW_1D',{**source,'sha256':'new'},league,'WAIVER_PLAN',rec,'2026-10-08T01:00:00Z')
    assert changed['decision_id']!=first['decision_id'] and changed['recommendation']==first['recommendation']
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);path=root/'action.json'
        action={'schema':'fie-user-action-source-v1','decision_id':first['decision_id'],'league_id':'1','season':2026,'week':5,
                'observed_at':'2026-10-08T01:30:00Z','actual_action':{'bid':5,'player_id':'123'}}
        path.write_text(json.dumps(action));observation={**action,'source':{'path':'action.json','sha256':digest(path)}}
        bound=w.observe_action(root,{'decisions':[first]},observation,stamp('2026-10-08T02:00:00Z'))
        assert bound['actual_action']['bid']==5 and bound['quality_classification']=='NOT_ASSESSED' and bound['transaction_execution'] is False
        for alteration,reason in [({'week':4},'TARGET'),({'observed_at':'2026-10-08T00:00:00Z'},'TIME'),({'actual_action':{'bid':100}},'PAYLOAD')]:
            try:w.observe_action(root,{'decisions':[first]},{**observation,**alteration},stamp('2026-10-08T02:00:00Z'));raise AssertionError('Invalid action accepted')
            except ValueError as exc:assert reason in str(exc)
        path.write_text('{}')
        try:w.observe_action(root,{'decisions':[first]},observation,stamp('2026-10-08T02:00:00Z'));raise AssertionError('Tampered action source accepted')
        except ValueError as exc:assert 'HASH' in str(exc)
    print('PASS decision ledger: stable IDs, unchanged owner advice, source revisions, unknown adoption/outcomes, action time/target/hash/payload guards')

if __name__=='__main__':main()
