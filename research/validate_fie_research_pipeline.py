#!/usr/bin/env python3
"""Governance-aware validator for one league's unified research pipeline."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path
import pandas as pd
from fie_research_pipeline_contract import (
    MODEL_DECISIONS, OFFENSE, READINESS_SCHEMA, league_row, load_json, load_profile,
    pipeline_dir, profile_fingerprint, roster_signature, scoring_signature,
)

def finite(v):
    try: return math.isfinite(float(v))
    except Exception: return False

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--league-id',required=True); ap.add_argument('--season',type=int,required=True); ap.add_argument('--output-dir',default=''); a=ap.parse_args(argv)
    out=Path(a.output_dir) if a.output_dir else pipeline_dir(a.league_id,a.season)
    r=load_json(out/'readiness.json',{}); assert r.get('schema')==READINESS_SCHEMA
    row=league_row(a.league_id); profile=load_profile(a.league_id,row); league=r.get('league') or {}
    assert str(league.get('id'))==str(a.league_id); assert league.get('profile_fingerprint')==profile_fingerprint(row,profile); assert league.get('scoring_signature')==scoring_signature(row,profile); assert league.get('roster_signature')==roster_signature(profile)
    g=r.get('governance') or {}; assert g.get('adp_in_football_model') is False; assert g.get('automatic_promotion') is False; assert g.get('canonical_model_modified') is False; assert g.get('production_activation_from_research_pipeline') is False
    positions=r.get('positions') or {}
    for pos in OFFENSE:
        meta=positions.get(pos) or {}; assert meta.get('decision') in MODEL_DECISIONS
        # Research readiness never changes the selected production model by itself.
        if not g.get('promotion_override_present'):
            assert meta.get('selected_production_model')=='M9'; assert meta.get('research_final_model')=='M9'; assert meta.get('current_challenger_projection_activated') is False
    board=pd.read_csv(out/'final_player_board.csv',low_memory=False); assert not board.empty
    assert board['league_id'].astype(str).eq(str(a.league_id)).all(); assert board['season'].astype(int).eq(int(a.season)).all()
    offense=board[board.position.astype(str).isin(OFFENSE)]
    if not offense.empty:
        assert offense.projection_points.notna().all(); assert offense.model_selected.astype(str).eq('M9').all() if not g.get('promotion_override_present') else True
    meta=load_json(out/'board-meta.json',{}); assert meta.get('adp_in_football_model') is False; assert meta.get('automatic_promotion') is False; assert 'build_league_value_board_on_M9' in str(meta.get('canonical_offense_value_source'))
    rankings=load_json(out/'rankings.json',{}); assert str(rankings.get('league_id'))==str(a.league_id); assert rankings.get('automatic_promotion') is False
    print(json.dumps({'status':'PASS','league_id':a.league_id,'rows':len(board),'positions':sorted(board.position.astype(str).unique().tolist())},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
