#!/usr/bin/env python3
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from preseason_projection_v2 import fixture_player_week, validate_component_preseason, build_season_profiles
from fie_strategy_stack import build_league_value_board, draft_actions, actionable_findings, injury_redistribution
from build_fie_strategy_stack import json_safe

scoring={"pass_yd":.04,"pass_td":4,"pass_int":-2,"rush_yd":.1,"rush_td":6,"rec":1,"rec_yd":.1,"rec_td":6,"fum_lost":-2}
# Fumble replay regression: only split nflverse columns are present, no aggregate.
fx=fixture_player_week().copy()
fx["rushing_fumbles"]=0.0
fx["receiving_fumbles"]=0.0
fx["sack_fumbles"]=0.0
fx["rushing_fumbles_lost"]=0.0
fx["receiving_fumbles_lost"]=0.0
fx["sack_fumbles_lost"]=0.0
if "fumbles" in fx: fx=fx.drop(columns=["fumbles"])
if "fumbles_lost" in fx: fx=fx.drop(columns=["fumbles_lost"])
fx.loc[fx.index[::137],"rushing_fumbles"]=1.0
fx.loc[fx.index[::137],"rushing_fumbles_lost"]=1.0
prof=build_season_profiles(fx,pd.DataFrame())
assert "prev__fumbles" in prof.columns and prof["prev__fumbles"].notna().any()
assert "prev__fumbles_lost" in prof.columns and prof["prev__fumbles_lost"].notna().any()
pv=validate_component_preseason(fx,scoring,pd.DataFrame())
assert pv["governance"]["market_inputs_used"] is False
assert pv["production_activation_allowed"] is False
for pos in ["QB","RB","WR","TE"]:
    audit=pv["per_position"].get(pos,{})
    assert not any(x.get("key") in {"fum","fum_lost"} for x in audit.get("scoring_unsupported",[])), (pos,audit)

board=pd.DataFrame([
 {"canonical_player_id":"a","sleeper_id":1001,"full_name":"A One","position_model":"RB","fie_season_mean":250,"fie_diagnostic_mean":250,"market_adp":60,"market_position_rank":30,"confidence":80},
 {"canonical_player_id":"b","sleeper_id":1002,"full_name":"B Two","position_model":"RB","fie_season_mean":120,"fie_diagnostic_mean":120,"market_adp":260,"market_position_rank":90,"confidence":80},
 {"canonical_player_id":"c","sleeper_id":1003,"full_name":"C Three","position_model":"WR","fie_season_mean":240,"fie_diagnostic_mean":240,"market_adp":40,"market_position_rank":20,"confidence":80},
 {"canonical_player_id":"d","sleeper_id":1004,"full_name":"D Four","position_model":"QB","fie_season_mean":300,"fie_diagnostic_mean":300,"market_adp":70,"market_position_rank":15,"confidence":80},
 {"canonical_player_id":"e","sleeper_id":1005,"full_name":"E Five","position_model":"TE","fie_season_mean":180,"fie_diagnostic_mean":180,"market_adp":90,"market_position_rank":18,"confidence":80},
 # Massive raw rank edge, but outside watchlist and below replacement: never TARGET.
 {"canonical_player_id":"deep","sleeper_id":1999,"full_name":"Deep Noise","position_model":"WR","fie_season_mean":20,"fie_diagnostic_mean":20,"market_adp":680,"market_position_rank":400,"confidence":95},
 # Bad identity/catalog row: never actionable.
 {"canonical_player_id":None,"sleeper_id":None,"full_name":"Aaron","position_model":"WR","fie_season_mean":100,"fie_diagnostic_mean":100,"market_adp":670,"market_position_rank":390,"confidence":90},
])
profile={"league":{"total_rosters":12,"roster_positions":["QB","RB","RB","WR","WR","TE","FLEX","K","DEF","BN","BN","BN","BN","BN","BN"]}}
current={"players":[
 {"canonical_player_id":"a","sleeper_id":"1001","full_name":"A One","team":"AAA","position_model":"RB","active":True},
 {"canonical_player_id":"b","sleeper_id":"1002","full_name":"B Two","team":"BBB","position_model":"RB","active":True},
 {"canonical_player_id":"c","sleeper_id":"1003","full_name":"C Three","team":"CCC","position_model":"WR","active":True},
 {"canonical_player_id":"d","sleeper_id":"1004","full_name":"D Four","team":"DDD","position_model":"QB","active":True},
 {"canonical_player_id":"e","sleeper_id":"1005","full_name":"E Five","team":"EEE","position_model":"TE","active":True},
 {"canonical_player_id":"deep","sleeper_id":"1999","full_name":"Deep Noise","team":"FFF","position_model":"WR","active":True},
]}
# mixed int/string identity joins remain supported
movement=pd.DataFrame([{"sleeper_id":"1001","canonical_player_id":"a","adp_change_from_open":3.0,"adp_change_7d":2.0,"adp_change_21d":1.0,"market_snapshot_count":4,"latest_market_as_of":"2026-08-30"}])
v,meta=build_league_value_board(board,profile,movement=movement,current=current)
assert meta["football_projection_uses_adp"] is False
assert meta["draft_relevance"]["draft_horizon"] == 180 and meta["draft_relevance"]["watchlist_horizon"] == 270
assert set(["fie_vorp","replacement_points","rank_edge","draft_relevant","actionable_draft_signal"]).issubset(v.columns)
assert float(v.loc[v.full_name.eq("A One"),"adp_change_from_open"].iloc[0]) == 3.0
assert not bool(v.loc[v.full_name.eq("Deep Noise"),"actionable_draft_signal"].iloc[0])
assert v.loc[v.full_name.eq("Aaron"),"value_label"].iloc[0] in {"IRRELEVANT","UNAVAILABLE"}
# Any actionable value must have non-negative VORP.
vals=v[v.value_label.isin(["STRONG_VALUE","VALUE"])]
assert vals.empty or (pd.to_numeric(vals.fie_vorp,errors="coerce")>=0).all()
da=draft_actions(v,1,6)
assert da.availability_probability.isna().all(); assert (da.availability_probability_status=="blocked_no_empirical_pick_distribution").all()
f=actionable_findings(v,current)
assert f["governance"]["auto_activation"] is False
for row in f["findings"]:
    if row["surface"]=="DRAFT" and row["action"]=="TARGET": assert row["evidence"]["fie_vorp"] >= 0
    if row["surface"]=="DRAFT": assert row["player_id"]
inj_current={"players":[
 {"canonical_player_id":"x","full_name":"X","team":"T","position_model":"RB","injury_status":"OUT","carry_share_prior4":.6},
 {"canonical_player_id":"y","full_name":"Y","team":"T","position_model":"RB","injury_status":"","carry_share_prior4":.25},
 {"canonical_player_id":"z","full_name":"Z","team":"T","position_model":"RB","injury_status":"","carry_share_prior4":.15},
]}
inj=injury_redistribution(inj_current); assert inj["production_activation"] is False; assert inj["rows"]
bad={"player_id":np.nan,"nested":{"metric":np.float64(np.nan),"missing":pd.NA},"ok":1.25}
safe=json_safe(bad); assert safe["player_id"] is None and safe["nested"]["metric"] is None and safe["nested"]["missing"] is None
json.dumps(safe,allow_nan=False)
print("PASS integrity_fie_strategy_stack_test V9.7.1/V10.4.1")
