"""No-network proofs for immutable sources, research inference and report scope."""
from copy import deepcopy
import gzip
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import numpy as np
import pandas as pd
from prospective_research_io import binding, gates, now, sha, verified, write
from capture_week6_research_sources import capture, validate_manifest, SOURCES
from waiver_v2_prospective import current_features, evaluate_rows, forecast, ROOT, validate_lock
from prepare_weekly_report_products import preparation, validate, PRODUCTS
from prepare_league_research_evidence import managed_roster, specialists
from validate_week6_research_write_plan import validate as validate_write_plan
from freeze_specialist_strategy_choices import choose


def rejects(fn):
    try:fn()
    except (ValueError,KeyError):return
    raise AssertionError('invalid source, time, identity or authority accepted')


def source_checks():
    with tempfile.TemporaryDirectory() as folder:
        root=Path(folder)
        def fetch(url):
            if url.endswith('.csv'):
                raw=b'season,week,gsis_id\n2026,5,00-0000001\n'
            else:raw=b'{}' if '/players/' in url or '/league/1'==url.split('sleeper.app/v1')[-1] else b'[]'
            return raw,now()
        path=capture(root,2026,6,fetcher=fetch,league_ids=['1'])
        value=validate_manifest(root,path)
        assert len(value['responses'])==len(SOURCES)+1+5
        assert value['auction_completeness'].startswith('EXPOSED_PAYLOAD')
        assert not value['activation_eligible']
        item=value['responses'][0]
        blob=root/item['path'];raw=gzip.decompress(blob.read_bytes())
        blob.write_bytes(gzip.compress(raw+b'\n',mtime=0))
        rejects(lambda:validate_manifest(root,path))
        write(root/'a.json',{'one':1})
        rejects(lambda:write(root/'a.json',{'one':2}))
        ref=binding(root,root/'a.json','2026-10-13T00:00:00+00:00')
        rejects(lambda:verified(root,ref,'2026-10-12T23:59:59+00:00'))
        rejects(lambda:verified(root,{**ref,'path':'../a.json'},'2026-10-14T00:00:00+00:00'))


def inference_checks():
    history=pd.DataFrame([{'canonical_player_id':'a','season':2026,'week':w,'team':'A','position_model':'QB',
                          'scoring_signature':'sig','fantasy_points_exact':float(w),'outcome_complete':True,'exact_scoring':True} for w in [3,4]])
    stats=pd.DataFrame([{'canonical_player_id':'a','season':2026,'week':w,'attempts':20.,'passing_yards':200.} for w in [3,4]])
    universe=[{'canonical_player_id':'a','position_model':'QB','team':'B'}]
    before=current_features(history,stats,universe,2026,5,'QB')
    assert before.iloc[0].fp_prior_4==3.5 and before.iloc[0].fp_history_count==2
    future=pd.DataFrame([{**history.iloc[0].to_dict(),'week':6,'fantasy_points_exact':9999.}])
    after=current_features(pd.concat([history,future]),stats,universe,2026,5,'QB')
    pd.testing.assert_frame_equal(before.reset_index(drop=True),after.reset_index(drop=True))
    rejects(lambda:current_features(history,stats,universe*2,2026,5,'QB'))
    rejects(lambda:current_features(history,stats,universe,2026,16,'QB'))
    rows=[{'canonical_player_id':'a','season':2026,'completed_week':5,'target_weeks':[6,7,8],
           'scoring_signature':'sig','forecast_mean':4.,'baseline_mean':3.}]
    outcomes=pd.DataFrame([{'canonical_player_id':'a','season':2026,'week':w,'scoring_signature':'sig',
                          'fantasy_points_exact':p,'outcome_complete':True,'exact_scoring':True} for w,p in [(6,0.),(7,3.),(8,6.)]])
    evaluated=evaluate_rows(rows,outcomes,observed_at='2026-11-03T18:00:00+00:00',horizon_end='2026-11-03T08:00:00+00:00')
    assert evaluated[0]['realized_mean']==3. and evaluated[0]['model_absolute_error']==1.
    missing=outcomes[outcomes.week!=7]
    assert evaluate_rows(rows,missing,observed_at='2026-11-03T18:00:00+00:00',horizon_end='2026-11-03T08:00:00+00:00')[0]['realized_mean'] is None
    bad=outcomes.copy();bad.loc[bad.week==7,'outcome_complete']=False
    assert evaluate_rows(rows,bad,observed_at='2026-11-03T18:00:00+00:00',horizon_end='2026-11-03T08:00:00+00:00')[0]['realized_mean'] is None
    rejects(lambda:evaluate_rows(rows,outcomes,observed_at='2026-11-02T18:00:00+00:00',horizon_end='2026-11-03T08:00:00+00:00'))
    badrows=deepcopy(rows);badrows[0]['target_weeks']=[6,8,9]
    rejects(lambda:evaluate_rows(badrows,outcomes,observed_at='2026-11-03T18:00:00+00:00',horizon_end='2026-11-03T08:00:00+00:00'))
    lock={'season':2026,'frozen_at':'2026-10-13T00:00:00+00:00','units':[]}
    rejects(lambda:forecast(lock,'bad',history,stats,universe,season=2026,completed_week=5,captured_at='2026-10-13T00:00:00+00:00',first_kickoff='2026-10-12T00:00:00+00:00'))


def report_and_league_checks():
    def empty(*args,**kwargs):return {'products':{name:{'content':None,'status':'BLOCKED_MISSING_PRODUCT'} for name in PRODUCTS},'sources':{}}
    with patch('prepare_weekly_report_products.bundle',empty):
        value=preparation(ROOT,2026,6,'2026-10-13T00:00:00+00:00')
    assert len(value['products'])==7 and value['complete_product_count']==0
    assert {p['source_week'] for p in value['products'] if p['name'] in {'PLAYER_PERFORMANCE','POST_WEEK_REVIEW'}}=={5}
    drift=deepcopy(value);drift['products'][0]['complete']=True;rejects(lambda:validate(drift))
    drift=deepcopy(value);drift['products'][0]['source_week']=6;rejects(lambda:validate(drift))
    rosters=[{'roster_id':1,'owner_id':'u','players':['k']}]
    users=[{'user_id':'u','display_name':'me'}]
    assert managed_roster(users,rosters,'me')['roster_id']==1
    rejects(lambda:managed_roster(users+[{'user_id':'v','display_name':'me'}],rosters,'me'))
    catalog={'k':{'player_id':'k','sport':'nfl','position':'K','team':'KC','gsis_id':'00-0000001'}}
    identity=pd.DataFrame([{'sleeper_id':'k','canonical_player_id':'00-0000001'}])
    board=specialists({'roster_positions':['K'],'scoring_settings':{'xpm':1}},None,rosters[0],catalog,[],identity)
    assert board[0]['candidates'][0]['available'] is None and board[0]['candidates'][0]['mean'] is None
    assert 'NOT_PRESEASON' in board[0]['hold_basis']
    held={'sleeper_id':'held','canonical_player_id':'DST:A','team':'A','mean':-2.,'bye':False,'held':True,'available':False}
    alt={'sleeper_id':'alt','canonical_player_id':'DST:B','team':'B','mean':5.,'bye':False,'held':False,'available':True}
    choices=choose({'position':'DST','candidates':[held,alt],'initial_hold_sleeper_id':'held','hold_basis':'MIDSEASON'})
    assert choices['choices']['FULL_HOLD']['sleeper_id']=='held' and choices['choices']['FULL_STREAM']['sleeper_id']=='alt'
    assert choices['selected_hold_status'].startswith('BLOCKED')
    unavailable={**alt,'available':None}
    assert choose({'position':'DST','candidates':[held,unavailable],'initial_hold_sleeper_id':'held','hold_basis':'MIDSEASON'})['choices']['FULL_STREAM']['sleeper_id']=='held'


def main():
    source_checks();inference_checks();report_and_league_checks()
    validate_write_plan('refs/heads/main',['data/research/prospective/weekly-sources/raw/2026/h/source.json.gz'])
    rejects(lambda:validate_write_plan('refs/heads/feature',['data/research/prospective/waiver-v2/history/2026/a.json']))
    rejects(lambda:validate_write_plan('refs/heads/main',['data/research/prospective/waiver-v2/locks/2026/model-lock.json']))
    rejects(lambda:validate_write_plan('refs/heads/main',['config/model-config.json']))
    validate_lock(ROOT,ROOT/'data/research/prospective/waiver-v2/locks/2026/revision-1/model-lock.json')
    print('PASS Week 6 research preparation: raw bytes, cutoff parity, full horizons, unknown bids/availability, seven report targets and locked authority')


if __name__=='__main__':main()
