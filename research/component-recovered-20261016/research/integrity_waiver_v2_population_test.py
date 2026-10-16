"""Closed-source zero proof, conservative exclusions and frozen forecasts."""
import copy
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from waiver_v2_population import META,ACTORS,EVENT_RULES,POSITIVE_STATS,certify,extend,stress,scope,run,close_identity_calendar
from build_waiver_v2_outcome_ledger import scoring_signature
from build_waiver_v2_label_batch import label_frame


def reject(action):
    try:action()
    except (ValueError,AssertionError):return
    raise AssertionError('Invalid population evidence accepted')


def fixture():
    ids=['00-0000001','00-0000002','00-0000003']
    pbp=[]
    for play,clock in [(1,3600),(2,100),(3,0)]:
        row={column:0 for column in META};row.update({column:None for column in ACTORS})
        row.update({'game_id':'g','season':2025,'week':3,'season_type':'REG','home_team':'A','away_team':'B',
                    'play_id':play,'play_type':'pass' if play==2 else None,'game_seconds_remaining':clock,
                    'two_point_conv_result':None,'total_home_score':0,'total_away_score':0,
                    'posteam':'A','posteam_score_post':0,'defteam_score_post':0})
        if play==2:row.update({'pass_attempt':1,'complete_pass':1,'passer_player_id':ids[0],'receiver_player_id':ids[0]})
        pbp.append(row)
    games=pd.DataFrame([{'game_id':'g','season':2025,'week':3,'game_type':'REG','home_team':'A','away_team':'B','home_score':0,'away_score':0}])
    roster=pd.DataFrame([{'canonical_player_id':i,'season':2025,'week':3,'team':'A','position_model':'WR','roster_complete':True} for i in ids])
    stats=pd.DataFrame([{**roster.iloc[0].to_dict(),**{c:0 for c in POSITIVE_STATS},'receiving_yards':3}])
    identity=pd.DataFrame([{'gsis_id':i,'canonical_player_id':i} for i in ids])
    support={key:{'support_status':'EXACT_EVENT_READY'} for key in EVENT_RULES}
    return pd.DataFrame(pbp),games,roster,stats,identity,support


def main():
    p,g,r,s,i,e=fixture()
    proof,audit,actors,missing=certify(p,g,r,s,i,e,[2025])
    assert set(proof.canonical_player_id)=={'00-0000002','00-0000003'} and audit.proof_ready.all()
    # A missing role invalidates the whole week, even if score/clock still match.
    broken=p.copy();broken.loc[1,'receiver_player_id']=None
    assert certify(broken,g,r,s,i,e,[2025])[0].empty
    broken=p.copy();broken.loc[2,'game_seconds_remaining']=1
    assert certify(broken,g,r,s,i,e,[2025])[0].empty
    broken=p.copy();broken.loc[2,'total_home_score']=6
    assert certify(broken,g,r,s,i,e,[2025])[0].empty
    broken=p.copy();broken['assist_tackle_1_player_id']=None;broken.loc[2,'assist_tackle_1_player_id']='unknown-name'
    assert certify(broken,g,r,s,i,e,[2025])[0].empty
    broken=p.copy();broken.loc[1,'pass_attempt']=np.nan
    assert certify(broken,g,r,s,i,e,[2025])[0].empty
    # Deleted/non-scoring occurrences conservatively prevent a player's zero.
    extra=p.iloc[0].copy();extra['play_id']=4;extra['play_deleted']=1;extra['td_player_id']='00-0000002'
    proof=certify(pd.concat([p,pd.DataFrame([extra])]),g,r,s,i,e,[2025])[0]
    assert set(proof.canonical_player_id)=={'00-0000003'}
    abandoned=g.copy();abandoned.loc[0,'home_score']=np.nan
    assert certify(p,abandoned,r,s,i,e,[2025])[0].empty
    absent_game=g.copy();absent_game.loc[0,'game_id']='another'
    reject(lambda:certify(p,absent_game,r,s,i,e,[2025]))
    more=g.copy();more.loc[1]=['h',2025,3,'REG','C','D',0,0]
    assert certify(p,more,r,s,i,e,[2025])[0].empty
    # Published positive scorer missing in the actor index blocks the whole week.
    lost=s.copy();lost.loc[0,'canonical_player_id']='00-0000002'
    assert certify(p,g,r,lost,i,e,[2025])[0].empty
    sparse=r.iloc[:1]
    assert certify(p,g,sparse,s,i,e,[2025])[0].empty
    uncertain=r.copy();uncertain['roster_complete']=False
    assert certify(p,g,uncertain,s,i,e,[2025])[0].empty
    bad=copy.deepcopy(e);bad['fum']['support_status']='BLOCKED_SOURCE_INCOMPLETE'
    reject(lambda:certify(p,g,r,s,i,bad,[2025]))
    reject(lambda:certify(p.drop(columns='fumbled_1_player_id'),g,r,s,i,e,[2025]))
    proof=certify(p,g,r,s,i,e,[2025])[0]
    outcomes=r.copy();outcomes['scoring_signature']='sig';outcomes['exact_scoring']=True
    outcomes['outcome_complete']=False;outcomes['outcome_status']='BLOCKED_PLAYER_STATS_INCOMPLETE'
    outcomes['fantasy_points_exact']=np.nan;outcomes['outcome_blocker_codes']='BLOCKED_PLAYER_STATS_INCOMPLETE'
    outcomes.loc[0,'fantasy_points_exact']=3.0;outcomes.loc[0,'outcome_complete']=True;outcomes.loc[0,'outcome_status']='COMPLETE_EXACT'
    expanded,count=extend(outcomes,proof,'certificate-hash')
    assert count==2 and expanded.outcome_complete.all() and expanded.fantasy_points_exact.tolist()==[3,0,0]
    diagnostic=outcomes.copy();diagnostic.loc[1,'fantasy_points_exact']=9.0
    assert extend(diagnostic,proof,'certificate-hash')[1]==1
    mismatch=proof.copy();mismatch['team']='B'
    assert extend(outcomes,mismatch,'certificate-hash')[1]==0
    unknown=outcomes.copy();unknown['exact_scoring']=False
    assert extend(unknown,proof,'certificate-hash')[1]==0
    reject(lambda:extend(outcomes,pd.concat([proof,proof]),'certificate-hash'))
    bad_proof=proof.copy();bad_proof['fantasy_points_proven']=1
    reject(lambda:extend(outcomes,bad_proof,'certificate-hash'))
    # Official franchise aliases are canonical, while different teams block.
    alias_g=g.copy();alias_g['home_team']='OAK'
    alias_r=r.copy();alias_r['team']='OAK'
    alias_p=p.copy();alias_p['home_team']='LV';alias_p['posteam']='LV'
    assert not certify(alias_p,alias_g,alias_r,s,i,e,[2025])[0].empty
    # A corrected admin ID may sort after the final scoring event. That does
    # not replace the completed scoreboard; post-play OT scores count too.
    final_p=p.copy();final_p.loc[1,'posteam_score_post']=6;final_p.loc[2,'total_home_score']=6
    final_p.loc[0,'play_id']=100
    final_g=g.copy();final_g['home_score']=6
    assert not certify(final_p,final_g,r,s,i,e,[2025])[0].empty
    # Forecast and feature bytes/values never change; only new outcomes join.
    labels=pd.DataFrame([{'canonical_player_id':'p','season':2025,'week':1,'fp_next3_weeks_exact':0.0,'fp_next3_weeks_full_horizon':True}])
    forecasts=pd.DataFrame([{'canonical_player_id':'p','season':2025,'week':1,'prediction':8.0,'fp_prior_4':10.0,
                             'fp_next3_weeks_exact':np.nan,'label_complete':False,'feature_admissible':True}])
    before=forecasts.copy(deep=True);report,joined=stress(forecasts,labels)
    pd.testing.assert_frame_equal(before,forecasts)
    assert joined.prediction.iloc[0]==8 and joined.target_population.iloc[0]=='NEWLY_OBSERVABLE_TARGET'
    assert report[0]['cohorts']['newly_observable']['metrics']['mae_gain']==2
    changed=forecasts.copy();changed['label_complete']=True;changed['fp_next3_weeks_exact']=3.0
    reject(lambda:stress(changed,labels))
    actual={'rec':1};sig=scoring_signature(actual)
    scope(actual,sig,{'allowed_rules':['rec'],'scoring_signatures':[sig]})
    reject(lambda:scope({'rec':2},sig,{'allowed_rules':['rec'],'scoring_signatures':[sig]}))
    reject(lambda:scope(actual,sig,{'allowed_rules':[],'scoring_signatures':[sig]}))
    # Whole-NFL absence uses an earlier identity anchor; future team/position
    # stays unknown and target-only rows cannot become decision opportunities.
    anchor=outcomes.iloc[1:2].copy();anchor['week']=1
    proof,audit,actors,_=certify(p,g,r,s,i,e,[2025])
    events=pd.DataFrame(columns=['canonical_player_id','season','week'])
    closed,global_proofs=close_identity_calendar(anchor,s,events,audit,actors,g,{'rec':1},e)
    new=closed[closed.target_only_row]
    assert len(new)==1 and new.week.iloc[0]==3 and new.fantasy_points_exact.iloc[0]==0
    assert pd.isna(new.team.iloc[0]) and pd.isna(new.position_model.iloc[0])
    assert global_proofs.identity_anchor_week.iloc[0]==1 and not new.future_membership_verified.iloc[0]
    # No same-season identity known before W3 means no backward label invention.
    late=anchor.copy();late['week']=4
    assert close_identity_calendar(late,s,events,audit,actors,g,{'rec':1},e)[1].empty
    # A scoring player on another team is not assigned the previous team's zero.
    traded=anchor.copy();traded['canonical_player_id']='00-0000001';traded['team']='B'
    scored,scored_proof=close_identity_calendar(traded,s,events,audit,actors,g,{'rec_yd':0.1},e)
    observed=scored[scored.target_only_row]
    assert np.isclose(observed.fantasy_points_exact.iloc[0],0.3) and observed.team.iloc[0]=='A'
    assert scored_proof.proof_basis.iloc[0]=='EXACT_PUBLISHED_PLAYER_WEEK'
    unsupported=copy.deepcopy(e);unsupported['fum']['support_status']='BLOCKED_SOURCE_INCOMPLETE'
    assert close_identity_calendar(traded,s,events,audit,actors,g,{'fum':-1},unsupported)[1].empty
    with TemporaryDirectory() as td:
        root=Path(td);reject(lambda:run(root/'absent',root/'absent',root))
    print('PASS population certificates: actor/game/source completeness, no missing-row imputation, immutable outcomes and frozen-forecast stress')


if __name__=='__main__':main()
