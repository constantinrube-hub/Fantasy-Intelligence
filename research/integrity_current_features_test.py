import pandas as pd
from build_current_snapshot import current_player_features

g=pd.DataFrame({
    'week':[1,2,3,4], 'snap_share':[.5,.6,.7,.8], 'target_share':[.1,.2,.3,.4],
    'carry_share':[0,0,0,0], 'red_zone_target_share':[0,.1,.2,.3],
    'pass_play_participation_proxy':[.4,.5,.6,.7], 'opportunity_change_score':[-.1,0,.1,.2]
})
team_hist=pd.DataFrame({
    'team':['AAA']*4+['BBB']*4, 'week':[1,2,3,4]*2,
    'team_plays':[60,62,64,66,55,56,57,58], 'team_pass_attempts':[35,36,37,38,30,31,32,33],
    'team_rush_attempts':[25,26,27,28,25,25,25,25], 'team_red_zone_plays':[8,9,10,11,7,7,8,8],
    'team_goal_line_plays':[2,2,3,3,1,2,2,2]
})
r=current_player_features(g,team_hist,'AAA','BBB',{'receiving_competition_index':.55})
assert r['leakage_safe'] is True and r['as_of_completed_week']==4 and r['window_games']==4
assert abs(r['values']['target_share']-.25)<1e-9
assert r['route_participation_is_proxy'] is True
assert abs(r['values']['receiving_competition_index']-.55)<1e-9
assert 'opponent_team_plays_prior4' in r['values']
print('OK: current-player feature export is leakage-labelled, rolling, and preserves route proxy semantics')
