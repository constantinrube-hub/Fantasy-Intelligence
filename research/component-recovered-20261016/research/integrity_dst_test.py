#!/usr/bin/env python3
"""Deterministic D/ST contract, scorer, attribution and integration tests."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd

from dst_contract import dst_enabled, dst_profile_fields, dst_scoring_settings, is_dst_scoring_key
from fie_dst import build_dst_team_week, predict_dst_from_bundle, score_dst_stats

ROOT=Path(__file__).resolve().parents[1]

STANDARD={
 'blk_kick':2,'def_st_ff':1,'def_st_fum_rec':1,'def_st_td':6,'def_td':6,'ff':1,'fum_rec':2,'int':2,
 'pts_allow_0':10,'pts_allow_1_6':7,'pts_allow_7_13':4,'pts_allow_14_20':1,'pts_allow_28_34':-1,'pts_allow_35p':-4,
 'sack':1,'safe':2,
}
GENESIS={**STANDARD,'blk_kick_ret_yd':.04,'def_4_and_stop':.5,'def_kr_yd':.1,'def_pass_def':.5,'def_pr_yd':.1,'fum_ret_yd':.04,'int_ret_yd':.04}

def test_contract():
    p={'roster_positions':['QB','RB','WR','TE','FLEX','DEF','BN'],'scoring_settings':STANDARD,'total_rosters':12,'format':'REDRAFT'}
    f=dst_profile_fields(p)
    assert f['dst_enabled'] is True and f['dst_starter_slots']==1
    assert dst_enabled(['QB','RB','BN']) is False
    assert set(dst_scoring_settings(STANDARD))==set(STANDARD)
    assert all(is_dst_scoring_key(k) for k in GENESIS)

def test_scoring_buckets():
    base={'sack':4,'int':2,'ff':1,'fum_rec':1,'def_td':0,'safe':0,'blk_kick':0,'points_allowed':17}
    z=score_dst_stats(base,STANDARD)
    assert z['exact'],z
    assert abs(z['points']-12.0)<1e-9,z  # 4 sacks + 4 INT + 1 FF + 2 FR + 1 PA bucket
    for pa,expect in [(0,10),(1,7),(6,7),(7,4),(13,4),(14,1),(20,1),(21,0),(27,0),(28,-1),(34,-1),(35,-4),(50,-4)]:
        z=score_dst_stats({'points_allowed':pa},STANDARD)
        # With all other known rules absent, sparse-zero handling remains exact.
        assert z['exact']
        assert abs(z['points']-expect)<1e-9,(pa,z)

def test_genesis_extras():
    st={'points_allowed':21,'sack':2,'int':1,'int_ret_yd':25,'fum_ret_yd':10,'def_pass_def':5,'def_4_and_stop':2,'def_kr_yd':100,'def_pr_yd':30,'blk_kick_ret_yd':5}
    z=score_dst_stats(st,GENESIS)
    expected=2+2+25*.04+10*.04+5*.5+2*.5+100*.1+30*.1+5*.04
    assert z['exact'] and abs(z['points']-expected)<1e-9,(z,expected)

def test_points_allowed_attribution():
    common={'game_id':'2026_01_B_A','season':2026,'week':1,'home_team':'A','away_team':'B'}
    rows=[
      # B offensive TD against A: counts 6.
      {**common,'posteam':'B','defteam':'A','touchdown':1,'td_team':'B','yards_gained':40,'sack':0,'interception':0,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':None,'field_goal_result':None,'two_point_conv_result':None},
      # PAT after that TD: counts 1.
      {**common,'posteam':'B','defteam':'A','touchdown':0,'td_team':None,'yards_gained':0,'sack':0,'interception':0,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':'good','field_goal_result':None,'two_point_conv_result':None},
      # B field goal: counts 3.
      {**common,'posteam':'B','defteam':'A','touchdown':0,'td_team':None,'yards_gained':20,'sack':0,'interception':0,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':None,'field_goal_result':'made','two_point_conv_result':None},
      # A's offense throws a pick-six to B. It must NOT count against A D/ST PA.
      {**common,'posteam':'A','defteam':'B','touchdown':1,'td_team':'B','yards_gained':0,'sack':0,'interception':1,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':None,'field_goal_result':None,'two_point_conv_result':None,'return_yards':30},
      # Sleeper counts the ensuing PAT against A D/ST.
      {**common,'posteam':'B','defteam':'A','touchdown':0,'td_team':None,'yards_gained':0,'sack':0,'interception':0,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':'good','field_goal_result':None,'two_point_conv_result':None},
      # A sacks B once.
      {**common,'posteam':'B','defteam':'A','touchdown':0,'td_team':None,'yards_gained':-8,'sack':1,'interception':0,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':None,'field_goal_result':None,'two_point_conv_result':None},
    ]
    tw=build_dst_team_week(pd.DataFrame(rows))
    a=tw[tw.team=='A'].iloc[0]
    assert a.points_allowed==11,(a.points_allowed,tw[['team','points_allowed']].to_dict('records'))
    assert a.sack==1

def test_market_context_normalization():
    common={'game_id':'2026_01_B_A','season':2026,'week':1,'home_team':'A','away_team':'B'}
    rows=[
      {**common,'posteam':'B','defteam':'A','touchdown':0,'td_team':None,'yards_gained':5,'sack':0,'interception':0,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':None,'field_goal_result':None,'two_point_conv_result':None},
      {**common,'posteam':'A','defteam':'B','touchdown':0,'td_team':None,'yards_gained':5,'sack':0,'interception':0,'fumble_forced':0,'fumble_lost':0,'safety':0,'extra_point_result':None,'field_goal_result':None,'two_point_conv_result':None},
    ]
    sched=pd.DataFrame([{'game_id':'2026_01_B_A','spread_line':6.0,'total_line':44.0}])
    tw=build_dst_team_week(pd.DataFrame(rows),sched)
    a=tw[tw.team=='A'].iloc[0]; b=tw[tw.team=='B'].iloc[0]
    assert a.spread_line==6.0 and abs(a.opponent_implied_points-19.0)<1e-9,(a.spread_line,a.opponent_implied_points)
    assert b.spread_line==-6.0 and abs(b.opponent_implied_points-25.0)<1e-9,(b.spread_line,b.opponent_implied_points)

def test_integration_files():
    contracts=json.loads((ROOT/'config/contracts/runtime-contracts.json').read_text())
    dst=[r for r in contracts['scoring_rule_families'] if r['id'].startswith('team_dst')]
    assert dst and all(r.get('weekly_supported') is True for r in dst)

    # D/ST is now a modular runtime surface. Do not couple the integrity gate
    # to obsolete literal navigation strings from the legacy monolithic shell.
    ui=(ROOT/'app/decision-ui.js').read_text()
    js=(ROOT/'app/dst-intelligence.js').read_text()

    assert 'dstPanel' in ui
    assert 'FIEDST' in js and 'Replacement' in js
    assert 'hasDST' in js
    assert "position||'').toUpperCase()==='DEF'" in js

if __name__=='__main__':
    for fn in [test_contract,test_scoring_buckets,test_genesis_extras,test_points_allowed_attribution,test_market_context_normalization,test_integration_files]: fn()
    print('OK: D/ST scorer, attribution, league gating and runtime integration')
