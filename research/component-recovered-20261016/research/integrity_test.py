#!/usr/bin/env python3
import pandas as pd
from fie_research import prep_pbp_opportunity, scoring_audit, score_rows

pbp=pd.DataFrame([
    {"season":2025,"week":1,"season_type":"REG","posteam":"AAA","yardline_100":18,"rush_attempt":1,"pass_attempt":0,"qb_dropback":0,"rusher_player_id":"RB1","air_yards":None},
    {"season":2025,"week":1,"season_type":"REG","posteam":"AAA","yardline_100":4,"rush_attempt":1,"pass_attempt":0,"qb_dropback":0,"rusher_player_id":"RB1","air_yards":None},
    {"season":2025,"week":1,"season_type":"REG","posteam":"AAA","yardline_100":12,"rush_attempt":0,"pass_attempt":1,"qb_dropback":1,"receiver_player_id":"WR1","air_yards":13},
    {"season":2025,"week":1,"season_type":"REG","posteam":"AAA","yardline_100":8,"rush_attempt":0,"pass_attempt":1,"qb_dropback":1,"receiver_player_id":"TE1","air_yards":4},
    {"season":2025,"week":1,"season_type":"REG","posteam":"AAA","yardline_100":45,"rush_attempt":1,"pass_attempt":0,"qb_dropback":0,"rusher_player_id":"RB2","air_yards":None},
])
team,player=prep_pbp_opportunity(pbp)
r=team.iloc[0]
assert int(r.team_red_zone_plays)==4
assert int(r.team_goal_line_plays)==1
assert int(r.team_red_zone_rushes)==2
assert int(r.team_red_zone_targets)==2
rb=player[player.source_player_id.eq('RB1')].iloc[0]
wr=player[player.source_player_id.eq('WR1')].iloc[0]
assert abs(float(rb.red_zone_carry_share)-1.0)<1e-9
assert abs(float(wr.red_zone_target_share)-0.5)<1e-9
assert abs(float(wr.end_zone_target_share_proxy)-1.0)<1e-9

stats=pd.DataFrame([{"position_model":"TE","receptions":4,"receiving_yards":50,"receiving_tds":1,"passing_yards":0,"rushing_yards":0}])
sc={"rec":1,"bonus_rec_te":0.5,"rec_yd":0.1,"rec_td":6}
a=scoring_audit(stats,sc)
assert a['exact_replay_eligible'] is True
assert abs(float(score_rows(stats,sc).iloc[0])-17.0)<1e-9
print('OK: PBP opportunity reduction + scoring support audit')
