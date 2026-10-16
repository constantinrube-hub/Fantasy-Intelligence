"""No-network source extension checks: unknowns, scope, timestamps and retries."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import gzip,json
from prospective_research_io import now,response,replay_response
from strict_kicker_source_components import components,audit
from capture_retrospective_auction_history import capture,summarize
from freeze_specialist_strategy_choices import choose
from prepare_league_research_evidence import specialists
from evaluate_prospective_waiver import paired_metrics
from publish_weekly_research_view import validate
import pandas as pd


def rejects(fn):
    try:fn()
    except (ValueError,KeyError):return
    raise AssertionError('invalid evidence admitted')


def main():
    with TemporaryDirectory() as folder:
        root=Path(folder);raw=b'{"raw":true}\n';at=now();receipt=response(root,root/'raw','x','url',raw,at,'json')
        path=root/receipt['path'];blob=bytearray(path.read_bytes());blob[9]=0 if blob[9]!=0 else 255
        path.write_bytes(blob);original=path.read_bytes()
        receipt=response(root,root/'raw','x','url',raw,at,'json')
        assert path.read_bytes()==original and replay_response(root,receipt,at)==raw
        rejects(lambda:response(root,root/'raw','x','url',raw+b' ',at,'json'))
        calls=[]
        def fetcher(url):
            calls.append(url);return json.dumps([{'transaction_id':str(len(calls)),'type':'waiver','status':'complete','settings':{'waiver_bid':4},'status_updated':1700000000000}]).encode(),at
        # A coarse platform clock may return the same instant for both runs.
        with patch('capture_retrospective_auction_history.now',return_value=at):
            first=capture(root,2026,3,['1'],fetcher);assert len(calls)==2 and first['unique_observations']==2
            first_bytes=Path(first['path']).read_bytes()
            second=capture(root,2026,3,['1'],lambda _:(_ for _ in ()).throw(AssertionError('complete archive re-fetched')))
            assert second['reused_responses']==2
            assert first['path']!=second['path'] and Path(first['path']).read_bytes()==first_bytes
        future=summarize([({'league_id':'1','round':1,'observed_at':at},[{'transaction_id':'f','type':'waiver','status':'complete','settings':{'waiver_bid':4},'status_updated':9999999999999}])],at)
        assert future['observations'][0]['classification']=='INVALID_FUTURE_OR_MALFORMED_EVENT_TIME'
        assert future['observations'][0]['acquisition_probability'] is None and future['observations'][0]['adoption']=='UNKNOWN'
    assert components({'fgm':0})[0]['fgm_50p']==0
    assert components({'fgm':3,'fgm_0_19':0,'fgm_20_29':1,'fgm_30_39':0,'fgm_40_49':1})[0]['fgm_50p']==1
    assert 'fgm_50p' not in components({'fgm':3,'fgm_20_29':1})[0]
    assert components({'fgm':1,'fgm_20_29':1})[0]['fgm_50p']==0
    assert components({'xpa':3,'xpm':2})[0]['xpmiss']==1
    assert 'xpmiss' not in components({'xpm':2})[0]
    rejects(lambda:components({'xpa':3,'xpm':2,'xpmiss':0}))
    rejects(lambda:components({'fgm':1,'fgm_50p':2}))
    rejects(lambda:components({'fgm':-1}))
    assert not audit({'pts_ppr':9},{'fgm_20_29':3})['exact']
    assert audit({'fgm_20_29':1},{'fgm_20_29':3})['points']==3
    held={'sleeper_id':'1','canonical_player_id':'a','team':'A','mean':2,'bye':False,'held':True,'available':False}
    unknown={'sleeper_id':'2','canonical_player_id':'b','team':'B','mean':None,'bye':False,'held':False,'available':True}
    selected=choose({'candidates':[held,unknown],'initial_hold_sleeper_id':'1','position':'K','hold_basis':'MIDSEASON'})
    assert selected['candidate_coverage']['complete_available_pool'] is False and selected['globally_optimal_claim'] is False
    catalog={'1':{'player_id':'1','position':'K','team':'A','sport':'nfl','gsis_id':'00-0000001'}}
    identity=pd.DataFrame([{'sleeper_id':'1','canonical_player_id':'00-0000001'}]);roster={'players':['1']}
    profile={'roster_positions':['K'],'scoring_settings':{'xpm':1}}
    projection={'player_id':'1','season':'2026','week':6,'season_type':'regular','stats':{'xpm':2}}
    assert specialists(profile,[],roster,catalog,[projection],identity,2026,6)[0]['candidates'][0]['mean']==2
    assert specialists(profile,[],roster,catalog,[{**projection,'week':5}],identity,2026,6)[0]['candidates'][0]['mean'] is None
    metrics=paired_metrics([{'scoring_signature':'s','position':'QB','forecast_mean':None,'baseline_mean':2,'realized_mean':0},
                           {'scoring_signature':'s','position':'QB','forecast_mean':1,'baseline_mean':2,'realized_mean':0}])[0]
    assert metrics['cutoff_rows']==2 and metrics['paired_rows']==1 and metrics['recent_production_baseline']['mae']==2
    assert 'sleeper' not in metrics and metrics['sleeper_comparison'] is False
    from prospective_research_io import gates
    view={'schema':'fie-weekly-research-view-v1','season':2026,'week':6,'target_weeks':[6,7,8],
          'pointer_replaceable':True,'generated_at':now(),'bindings':{},'leagues':[],**gates([])}
    validate(view);rejects(lambda:validate({**view,'forecast_eligible':True}));rejects(lambda:validate({**view,'target_weeks':[6,8,9]}))
    print('PASS extended Week 6 source evidence: gzip header preservation, auction retries, K explicit components, scoped pools, target clocks, paired denominator and readiness authority')


if __name__=='__main__':main()
