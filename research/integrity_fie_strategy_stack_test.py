#!/usr/bin/env python3
from __future__ import annotations
import sys, tempfile, json
from pathlib import Path
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preseason_projection_v2 import fixture_player_week, validate_component_preseason
from fie_strategy_stack import build_league_value_board, draft_actions, actionable_findings, injury_redistribution

scoring={"pass_yd":.04,"pass_td":4,"pass_int":-2,"rush_yd":.1,"rush_td":6,"rec":1,"rec_yd":.1,"rec_td":6}
pv=validate_component_preseason(fixture_player_week(),scoring,pd.DataFrame())
assert pv["governance"]["market_inputs_used"] is False
assert pv["production_activation_allowed"] is False
board=pd.DataFrame([
 {"canonical_player_id":"a","full_name":"A","position_model":"RB","fie_season_mean":250,"fie_diagnostic_mean":250,"market_adp":60,"market_position_rank":30,"confidence":80},
 {"canonical_player_id":"b","full_name":"B","position_model":"RB","fie_season_mean":210,"fie_diagnostic_mean":210,"market_adp":25,"market_position_rank":10,"confidence":80},
 {"canonical_player_id":"c","full_name":"C","position_model":"WR","fie_season_mean":240,"fie_diagnostic_mean":240,"market_adp":40,"market_position_rank":20,"confidence":80},
 {"canonical_player_id":"d","full_name":"D","position_model":"QB","fie_season_mean":300,"fie_diagnostic_mean":300,"market_adp":70,"market_position_rank":15,"confidence":80},
 {"canonical_player_id":"e","full_name":"E","position_model":"TE","fie_season_mean":180,"fie_diagnostic_mean":180,"market_adp":90,"market_position_rank":18,"confidence":80},
])
profile={"league":{"total_rosters":1,"roster_positions":["QB","RB","WR","TE","FLEX","BN"]}}
v,meta=build_league_value_board(board,profile)
assert meta["football_projection_uses_adp"] is False
assert set(["fie_vorp","replacement_points","rank_edge"]).issubset(v.columns)
# Regression: season_board CSV commonly infers Sleeper IDs as int64 while
# immutable market JSON preserves them as strings.  Both identity paths must join.
board_ids=board.copy(); board_ids["sleeper_id"]=[1001,1002,1003,1004,1005]
board_ids["canonical_player_id"]=[2001,2002,2003,2004,2005]
movement=pd.DataFrame([{
    "sleeper_id":"1001","canonical_player_id":"2001",
    "adp_change_from_open":3.0,"adp_change_7d":2.0,"adp_change_21d":1.0,
    "market_snapshot_count":4,"latest_market_as_of":"2026-08-30"
}])
v_ids,_=build_league_value_board(board_ids,profile,movement=movement)
assert float(v_ids.loc[v_ids.full_name.eq("A"),"adp_change_from_open"].iloc[0]) == 3.0
da=draft_actions(v,1,6); assert da.availability_probability.isna().all(); assert (da.availability_probability_status=="blocked_no_empirical_pick_distribution").all()
current={"players":[
 {"canonical_player_id":"x","full_name":"X","team":"T","position_model":"RB","injury_status":"OUT","carry_share_prior4":.6},
 {"canonical_player_id":"y","full_name":"Y","team":"T","position_model":"RB","injury_status":"","carry_share_prior4":.25},
 {"canonical_player_id":"z","full_name":"Z","team":"T","position_model":"RB","injury_status":"","carry_share_prior4":.15},
]}
inj=injury_redistribution(current); assert inj["production_activation"] is False; assert inj["rows"]
f=actionable_findings(v,current); assert f["governance"]["auto_activation"] is False
print("PASS integrity_fie_strategy_stack_test")
