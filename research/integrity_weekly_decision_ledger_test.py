#!/usr/bin/env python3
"""Stable recommendation identity and separately bound action observations."""
import json,tempfile
from copy import deepcopy
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
    older=w.decision('WINDOW_1C',{**source,'generated_at':None},league,'LINEUP_CHANGE',rec,'2026-10-08T01:00:00Z')
    assert older['issued_at'] is None and older['issued_at_status']=='NOT_DECLARED_BY_OWNER'
    changed=w.decision('WINDOW_1D',{**source,'sha256':'new'},league,'WAIVER_PLAN',rec,'2026-10-08T01:00:00Z')
    assert changed['decision_id']!=first['decision_id'] and changed['recommendation']==first['recommendation']
    for kind in ('LINEUP_CHANGE','STATUS_CHECK','WAIVER_PLAN'):
        frozen=w.decision('WINDOW_1C' if kind!='WAIVER_PLAN' else 'WINDOW_1D',source,league,kind,
                          {**rec,'projection_delta':0},'2026-10-08T01:00:00Z')
        before=deepcopy(frozen);views=w.presentation_views(frozen)
        assert frozen==before
        for level in ('basic','expanded','advanced'):
            assert views[level]['decision_id']==frozen['decision_id']
            assert views[level]['recommendation']==frozen['recommendation']
            assert views[level]['confidence']=='LOW' and views[level]['impact']=={'projection_delta':0}
        views['basic']['recommendation']['recommended_bid']=99
        assert views['advanced']['recommendation']['recommended_bid']==7 and frozen==before
    missing=w.decision('WINDOW_1C',source,league,'STATUS_CHECK',{'player_id':'123'},'2026-10-08T01:00:00Z')
    assert w.presentation_views(missing)['basic']['impact'] is None
    assert w.presentation_views(missing)['basic']['confidence'] is None
    tampered=deepcopy(first);tampered['recommendation']['recommended_bid']=8
    try:w.presentation_views(tampered);raise AssertionError('Changed frozen recommendation accepted')
    except ValueError as exc:assert 'ID_MISMATCH' in str(exc)
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
