#!/usr/bin/env python3
"""Offline invariants for M9.1c unified integration helper."""
from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from integrate_m91c_research_challenger import (
    CANONICAL_LOCKED_COLUMNS, challenger_map, enrich_board, stable_frame_hash,
)

with tempfile.TemporaryDirectory() as td:
    p=Path(td)/"board.csv"
    board=pd.DataFrame([
        {
            "canonical_player_id":"p1","sleeper_id":"s1","player_id":"p1",
            "name":"Starter","team":"AAA","position":"QB",
            "projection_points":300.0,"projection_ppg":17.65,
            "p10":250.0,"p25":275.0,"p50":300.0,"p75":325.0,"p90":350.0,
            "position_rank":1,"overall_rank":1,"replacement_points":220.0,
            "vorp":80.0,"market_position_rank":2,"market_overall_rank":20,
            "rank_edge_position":1,"rank_edge_overall":19,"value_label":"VALUE",
            "actionable_signal":True,"model_selected":"M9","model_status":"BLOCKED_STATISTICS",
            "projection_source":"MARKET_FALLBACK","projection_basis":"MARKET_BASE",
            "interval_source":"MARKET_BASE",
        }
    ])
    board.to_csv(p,index=False)
    before=stable_frame_hash(board,CANONICAL_LOCKED_COLUMNS)

    m91c=pd.DataFrame([{
        "canonical_player_id":"p1","sleeper_id":"s1",
        "m91c_projection":292.0,"sleeper_market_projection":300.0,
        "m91c_delta_vs_sleeper":-8.0,"m91c_raw_fie_projection":260.0,
        "m91c_signal_z":-2.0,"m91c_signal_percentile":.1,
        "m91c_signal_extremity":.8,"m91c_total_reliability":.6,
        "m91c_correction_cap":10.0,"m91c_role_cohort":"CLEAR_STARTER",
        "m91c_status":"RESEARCH_ONLY_EXACT_REPLAY",
        "m91c_exact_scoring_replay":True,"m91c_team_changed":False,
        "m91c_team_transition_status":"STABLE_TEAM",
    }])
    cmap=challenger_map(m91c,"BLOCKED_MISSING_HISTORICAL_SLEEPER_BASELINE")
    result=enrich_board(p,cmap)
    out=pd.read_csv(p)
    after=stable_frame_hash(out,CANONICAL_LOCKED_COLUMNS)

    assert before==after==result["canonical_locked_hash_after"]
    assert out.loc[0,"model_selected"]=="M9"
    assert out.loc[0,"projection_points"]==300.0
    assert out.loc[0,"vorp"]==80.0
    assert out.loc[0,"position_rank"]==1
    assert out.loc[0,"preseason_challenger_model"]=="M9.1c"
    assert out.loc[0,"preseason_challenger_projection"]==292.0
    assert out.loc[0,"preseason_challenger_delta_vs_sleeper"]==-8.0

print("PASS M9.1c unified integration: challenger evidence attaches without changing canonical production/value fields")
