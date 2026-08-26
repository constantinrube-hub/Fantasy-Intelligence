#!/usr/bin/env python3
from __future__ import annotations
import json, tempfile
from pathlib import Path
import pandas as pd
from kicker_contract import kicker_profile_fields, kicker_scoring_settings, is_kicker_scoring_key
from fie_kicker import score_kicker_stats, build_kicker_week, fit_models

def eq(a,b,eps=1e-9): assert abs(a-b)<eps,(a,b)

def main():
    standard={'fgm_0_19':3,'fgm_20_29':3,'fgm_30_39':3,'fgm_40_49':4,'fgm_50p':5,'fgmiss':-1,'xpm':1,'xpmiss':-1}
    st={'fgm_0_19':1,'fgm_40_49':1,'fgm_50_59':1,'fgm_60p':1,'fgmiss':1,'xpm':2,'xpmiss':1}
    z=score_kicker_stats(st,standard);eq(z['points'],3+4+10-1+2-1);assert z['exact'],z
    genesis={'fgm_yds':.1,'fgmiss_0_19':-4,'fgmiss_20_29':-3,'fgmiss_30_39':-2,'fgmiss_40_49':-1,'xpm':1}
    z=score_kicker_stats({'made_distances':[58,41],'miss_distances':[27,46],'xpm':3},genesis);eq(z['points'],9.9-3-1+3);assert z['exact'],z
    assert is_kicker_scoring_key('fgm_yds') and is_kicker_scoring_key('fgmiss_30_39') and not is_kicker_scoring_key('sack')
    pf=kicker_profile_fields({'roster_positions':['QB','K','BN'],'scoring_settings':genesis,'total_rosters':16,'format':'DYNASTY','position_limits':{'K':2}});assert pf['kicker_enabled'] and pf['kicker_starter_slots']==1 and 'fgm_yds' in pf['kicker_scoring_settings']
    # Synthetic play-level extraction covers distance and XP outcomes.
    pbp=pd.DataFrame([
      {'game_id':'g1','season':2025,'week':1,'posteam':'DAL','defteam':'NYG','home_team':'DAL','field_goal_attempt':1,'extra_point_attempt':0,'play_type':'field_goal','field_goal_result':'made','kick_distance':58,'posteam_score_post':3},
      {'game_id':'g1','season':2025,'week':1,'posteam':'DAL','defteam':'NYG','home_team':'DAL','field_goal_attempt':1,'extra_point_attempt':0,'play_type':'field_goal','field_goal_result':'missed','kick_distance':46,'posteam_score_post':3},
      {'game_id':'g1','season':2025,'week':1,'posteam':'DAL','defteam':'NYG','home_team':'DAL','field_goal_attempt':0,'extra_point_attempt':1,'play_type':'extra_point','extra_point_result':'good','posteam_score_post':10},
    ])
    kw=build_kicker_week(pbp);assert len(kw)==1; r=kw.iloc[0];eq(r.fgm_50_59,1);eq(r.fgmiss_40_49,1);eq(r.fgm_yds,58);eq(r.xpm,1)
    print('Kicker Intelligence integrity: PASS')
if __name__=='__main__':main()
