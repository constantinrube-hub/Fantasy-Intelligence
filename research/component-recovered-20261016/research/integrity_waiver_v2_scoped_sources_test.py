"""Scoped attribution, unknown membership and historical position regressions."""
import pandas as pd
from unittest.mock import patch
import waiver_v2_scoped_sources as owner
from waiver_v2_outcomes import EVENT_WEEKLY_RULES

def main():
    from scoring_relevance import position_relevant
    assert position_relevant("fg_ret_yd","DEF")
    assert not any(position_relevant("fg_ret_yd",p) for p in ["QB","RB","WR","TE"])
    games=pd.DataFrame([{'game_id':'a','home_team':'KC','away_team':'DEN'},{'game_id':'b','home_team':'BUF','away_team':'NYJ'}])
    rows=pd.DataFrame([{'canonical_player_id':str(i),'season':2025,'week':1,'team':t,'position_model':p,'fantasy_points_exact':8.,'outcome_complete':True,'exact_scoring':True,'outcome_status':'COMPLETE_EXACT','outcome_blocker_codes':''} for i,(t,p) in enumerate([('KC','WR'),('BUF','WR'),('KC','QB'),(None,None)])])
    bad=[{'rule':'kr_yd','season':2025,'week':1,'game_id':'a','canonical_player_id':None}]
    result=owner.mask_outcomes(rows,{'kr_yd':.04},bad,games)
    assert result.outcome_complete.tolist()==[False,True,True,False]
    assert result.fantasy_points_exact.iloc[1]==8 and result.fantasy_points_exact.iloc[2]==8
    assert owner.mask_outcomes(rows,{'kr_yd':0},bad,games).outcome_complete.all()
    specific=[{**bad[0],'game_id':None,'canonical_player_id':'1'}]
    result=owner.mask_outcomes(rows,{'kr_yd':.04},specific,games)
    assert result.outcome_complete.tolist()==[True,False,True,False]
    template=rows.iloc[:2].copy();template['position_model']=['QB','TE'];template['fantasy_points_exact']=0.
    template['outcome_status']=['COMPLETE_EXACT','CONFIRMED_BYE']
    stats=template[['canonical_player_id','season','week','team']].copy();stats['position_model']='TE'
    weekly=stats[['canonical_player_id','season','week']].copy();weekly[EVENT_WEEKLY_RULES['kr_yd']]=[47.,100.]
    audit=pd.DataFrame({'proof_ready':pd.Series([],dtype=bool)});owner._PROOF_CACHE=None
    with patch.object(owner,'slow_profile_outcomes',return_value=(template,audit,[])):
        result,_,_=owner.profile_outcomes(pd.DataFrame(),stats,pd.DataFrame(),games,pd.DataFrame(),weekly,{'kr_yd':{'support_status':'EXACT_EVENT_READY'}},[],{'kr_yd':.04})
    assert result.fantasy_points_exact.tolist()==[0.,0.], 'Use historical roster QB scope and retain proven bye zero'
    owner._PROOF_CACHE=None
    print('PASS scoped sources: local game/player exclusions, unknown-membership zeros, historical position and bye preservation')
if __name__=='__main__':main()
