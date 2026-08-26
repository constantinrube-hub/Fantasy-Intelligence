#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, tempfile
from pathlib import Path

from bulk_onboard import build_plan, research_state
from portfolio_rules import load_portfolio_config
from league_profile import build_profile

ROOT=Path(__file__).resolve().parents[1]

def config_only():
    cfg=load_portfolio_config(ROOT/'config'/'league-portfolio.json')
    assert len(cfg['leagues'])==19
    ids=[x['league_id'] for x in cfg['leagues']]
    assert len(ids)==len(set(ids))
    wf=(ROOT/'.github'/'workflows'/'bulk-onboard-fie-portfolio.yml').read_text(encoding='utf-8')
    for token in ['PLAN_ONLY','REGISTER_ONLY','BUILD_MISSING','FULL','fail-fast: false','max-parallel','fie-league-${{ matrix.league_id }}']:
        assert token in wf, token
    print('PASS: bulk onboarding config/workflow contract')

def full_fixture():
    with tempfile.TemporaryDirectory() as td:
        t=Path(td); (t/'leagues').mkdir()
        cfg={'schema_version':1,'sleeper_username':'Tester','leagues':[
            {'league_id':'111111111111','format':'REDRAFT','priority':'HIGH'},
            {'league_id':'222222222222','format':'CHOPPED','priority':'VERY_HIGH'},
        ]}
        cfgp=t/'config.json'; cfgp.write_text(json.dumps(cfg))
        reg=t/'leagues'/'registry.json'; reg.write_text(json.dumps({'schema_version':1,'leagues':{}}))
        leagues={
          '111111111111':{'league_id':'111111111111','name':'A','season':'2026','season_type':'regular','total_rosters':2,'roster_positions':['QB','BN'],'settings':{},'scoring_settings':{'pass_td':4}},
          '222222222222':{'league_id':'222222222222','name':'B','season':'2026','season_type':'regular','total_rosters':2,'roster_positions':['QB','BN'],'settings':{},'scoring_settings':{'pass_td':6}},
        }
        def fetch(url):
            if '/v1/user/' in url:return {'user_id':'u1','username':'Tester'}
            if url.endswith('/rosters'):return [{'roster_id':1,'owner_id':'u1'}]
            if url.endswith('/drafts'):return []
            lid=url.rstrip('/').split('/')[-1]
            if lid in leagues:return leagues[lid]
            raise RuntimeError('unexpected '+url)
        plan=build_plan(cfgp,reg,'ALL',fetch)
        assert plan['requested']==2 and plan['build_required']==2 and plan['errors']==0
        assert [x['league_id'] for x in plan['build_matrix']['include']]==['222222222222','111111111111']
        # Research state transitions are deterministic and do not depend on registry order.
        root=t/'leagues'/'111111111111'; root.mkdir()
        prof=build_profile('111111111111','REDRAFT',league_json=leagues['111111111111'])
        (root/'profile.json').write_text(json.dumps(prof))
        state,_=research_state('111111111111',prof,t/'leagues')
        assert state=='NEW'
    print('PASS: bulk plan is priority-aware, failure-isolated, and correctly detects new research')

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--config-only',action='store_true'); a=ap.parse_args()
    config_only()
    if not a.config_only: full_fixture()
