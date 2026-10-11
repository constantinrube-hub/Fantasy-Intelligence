#!/usr/bin/env python3
"""Independent projection fields and active observed-exposure regressions."""
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from unittest.mock import patch
import weekly_portfolio_surface as w
from build_current_snapshot import forecast_artifact_identity


def row(**changes):
    return {'sleeper_id':'123','canonical_player_id':'gsis-1','full_name':'Player','team':'AAA','position_model':'WR',
            'fie_weekly_projection':10,'sleeper_weekly_projection':12,'decision_weekly_projection':12,
            'weekly_activation_eligible':False,'p10':6,'p90':18,**changes}


def main():
    player=w.projection(row(),2026,5,'sig')
    assert player['fie_mean']==10 and player['sleeper_mean']==12 and player['fie_minus_sleeper']==-2
    assert player['p50'] is None and player['fie_median'] is None and player['interval_coverage']=='PARTIAL'
    assert player['status']=='RESEARCH_OR_DIAGNOSTIC' and player['decision_mean']==12
    assert w.baseline_source({'scoring_signature':'sig'},2026,5)['status']=='NOT_DECLARED_BY_CURRENT_OWNER'
    receipt={'season':2026,'week':5,'scoring_signature':'sig','status':'ARCHIVED_PROJECTION_STATS_MATCH',
             'archive_sha256':'a'*64,'source_observed_at':'2026-10-08T12:00:00Z'}
    baseline=w.baseline_source({'scoring_signature':'sig','sleeper_baseline_receipt':receipt},2026,5)
    assert baseline['status']=='ARCHIVED_PROJECTION_STATS_MATCH'
    assert baseline['scoring_comparability_certified'] is False
    assert w.baseline_source({'scoring_signature':'sig','sleeper_baseline_receipt':{**receipt,'status':'ARCHIVED_PROJECTION_STATS_DIFFER'}},2026,5)['status']=='ARCHIVED_PROJECTION_STATS_DIFFER'
    for bad in ({**receipt,'week':4},{**receipt,'scoring_signature':'other'},
                {**receipt,'status':'FABRICATED'}):
        try:
            w.baseline_source({'scoring_signature':'sig','sleeper_baseline_receipt':bad},2026,5)
            raise AssertionError('Invalid baseline source receipt accepted')
        except ValueError:
            pass
    missing=w.projection(row(fie_weekly_projection=None,sleeper_weekly_projection=0),2026,5,'sig')
    assert missing['fie_mean'] is None and missing['fie_coverage']=='UNSUPPORTED' and missing['sleeper_mean']==0
    assert missing['fie_minus_sleeper'] is None
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        import json
        artifacts={}
        for label in ('M4','M5','M6'):
            path=root/f'{label}.json'
            bundle={'research_build':f'{label}-2026'}
            path.write_text(json.dumps(bundle),encoding='utf-8')
            artifacts[label]=forecast_artifact_identity(str(path),bundle,label)
            assert artifacts[label]['status']=='BOUND' and len(artifacts[label]['sha256'])==64
        bound=w.projection(row(),2026,5,'sig',artifacts)
        assert bound['model_identity_status']=='ARTIFACT_BOUND_MODEL_UNDECLARED'
        assert bound['model_id'] is None and bound['fie_forecast_source']['m4_sha256']==artifacts['M4']['sha256']
        other={**artifacts,'M4':{**artifacts['M4'],'sha256':'f'*64}}
        assert w.projection(row(),2026,5,'sig',other)['fie_forecast_source']['m4_sha256']=='f'*64
        assert 'fie_forecast_source' not in row()  # Per-league identity stays out of the shared player base.
        assert w.forecast_source(None,artifacts) is None
        assert w.forecast_source(10,{**artifacts,'M6':{'status':'NOT_BOUND'}})['status']=='SOURCE_BUNDLES_NOT_BOUND'
        assert forecast_artifact_identity(str(root/'M4.json'),{},'M4')['status']=='NOT_BOUND'
        assert forecast_artifact_identity(str(root/'M4.json'),{'research_build':'replaced'},'M4')['status']=='NOT_BOUND'
        for bad in ({**artifacts,'M4':{**artifacts['M4'],'sha256':'not-a-digest'}},
                    {**artifacts,'M4':{**artifacts['M4'],'artifact':'M5'}}):
            try:
                w.forecast_source(10,bad)
                raise AssertionError('Invalid forecast source accepted')
            except ValueError as exc:
                assert 'ARTIFACTS_INVALID' in str(exc)
    try:
        w.projection(row(p10=20,p90=10),2026,5,'sig')
        raise AssertionError('Invalid interval accepted')
    except ValueError:
        pass
    exact=row(fie_weekly_projection=None,canonical_player_id=None)
    alias=row(sleeper_id='123.0')
    for rows in ([exact,alias],[alias,exact]):
        assert w.projection_index({'players':rows})['123'] is exact
    try:
        w.projection_index({'players':[exact,exact.copy()]})
        raise AssertionError('Duplicate exact Sleeper ID accepted')
    except ValueError:
        pass
    specialist={**player,'position':'K','owned_by_user':True,'submitted_starter':True,'rostered_in_league':True}
    specialized={'league_id':'1','status':'BOUND_CURRENT_ROSTER','roster_positions':['K'],'active_operational_scope':True,'players':[specialist]}
    boards=w.specialist_boards([specialized])
    assert boards['K'][0]['owned']==[specialist] and boards['K'][0]['strategy_recommendation'] is None
    assert boards['DST'][0]['status']=='NOT_APPLICABLE_NO_ROSTER_SLOT'
    specialized['active_operational_scope']=False
    assert w.specialist_boards([specialized])['K'][0]['status']=='NOT_APPLICABLE_RESEARCH_ONLY'
    observed={**player,'owned_by_user':True,'submitted_starter':True}
    active={'league_id':'1','active_operational_scope':True,'scoring_signature':'a','players':[observed]}
    eliminated={'league_id':'2','active_operational_scope':False,'scoring_signature':'b','players':[observed]}
    counts=w.exposure([active,eliminated])
    assert counts[0]['owned_league_count']==1 and counts[0]['starting_league_count']==1
    assert counts[0]['owned_contexts'][0]['scoring_signature']=='a'
    displayed=w.markdown({'season':2026,'week':5,'status':'PARTIAL','roster_exposure':[],
                          'note':'Source and scoring are distinct.',
                          'leagues':[{'league_id':'1','status':'BOUND_CURRENT_ROSTER','scoring_signature':'sig',
                                      'sleeper_baseline_source':baseline,'players':[]}]})
    assert 'ARCHIVED_PROJECTION_STATS_MATCH' in displayed and '(scoring unverified)' in displayed
    with tempfile.TemporaryDirectory() as td:
        # Test freshness failure through the real league path before identity resolution.
        import json
        root=Path(td); (root/'data/research/leagues/1').mkdir(parents=True)
        for generated in ('2026-10-08T03:00:00Z','2026-10-07T00:00:00Z'):
            core={'generated_at':generated,'stale_after_seconds':21600}
            with patch.object(w,'load_current_snapshot',return_value={}),patch.object(w,'verified_core',return_value=(root/'core.json',core)):
                try:
                    w.league_surface(root,'1',2026,5,datetime(2026,10,8,1,tzinfo=timezone.utc),'user')
                    raise AssertionError('Future or stale core accepted')
                except ValueError as exc:
                    assert 'STALE_OR_FUTURE' in str(exc)
    print('PASS portfolio surface: independent means, null median, intervals, exact identity precedence, lifecycle/scoring isolation, stale/future core rejection')

if __name__=='__main__':main()
