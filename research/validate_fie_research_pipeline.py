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
    try:
        return math.isfinite(float(v))
    except Exception:
        return False


def _truthy_series(s: pd.Series) -> pd.Series:
    """Interpret persisted CSV booleans without treating the string 'False' as truthy."""
    return s.map(lambda v: bool(v) if isinstance(v, bool) else str(v).strip().lower() in {'1','true','yes','y'}).fillna(False)


def validate_offense_projection_contract(offense: pd.DataFrame, *, promotion_override_present: bool = False) -> None:
    """Validate canonical offensive board projection semantics.

    The final board intentionally retains current-catalog rows that have no governed
    M9 projection. Those rows must be explicit UNAVAILABLE / non-actionable entries.
    Every usable, draft-relevant or actionable offensive row must still have a finite
    production projection. This preserves fail-closed behavior without pretending
    unavailable catalog players have model output.
    """
    if offense.empty:
        return

    if not promotion_override_present:
        assert offense.model_selected.astype(str).eq('M9').all(), 'offense contains non-M9 production model without approved override'

    assert 'projection_points' in offense.columns, 'projection_points missing from final board'
    projected = offense.projection_points.notna()
    unavailable = offense.value_label.astype(str).eq('UNAVAILABLE') if 'value_label' in offense.columns else pd.Series(False, index=offense.index)

    # Any row exposed as usable value must have an actual finite canonical projection.
    usable = ~unavailable
    assert projected.loc[usable].all(), 'non-UNAVAILABLE offensive row missing projection_points'
    if projected.any():
        assert offense.loc[projected, 'projection_points'].map(finite).all(), 'non-finite offensive projection_points present'

    # Missing projections are allowed only for rows that are explicitly unavailable
    # and cannot become a draft/actionable recommendation.
    missing = ~projected
    if missing.any():
        assert unavailable.loc[missing].all(), 'missing offensive projections must be labeled UNAVAILABLE'
        if 'draft_relevant' in offense.columns:
            assert not _truthy_series(offense.loc[missing, 'draft_relevant']).any(), 'UNAVAILABLE row with missing projection marked draft_relevant'
        if 'actionable_signal' in offense.columns:
            assert not _truthy_series(offense.loc[missing, 'actionable_signal']).any(), 'UNAVAILABLE row with missing projection marked actionable'

    if 'draft_relevant' in offense.columns:
        draft = _truthy_series(offense['draft_relevant'])
        assert projected.loc[draft].all(), 'draft-relevant offensive row missing projection_points'
    if 'actionable_signal' in offense.columns:
        actionable = _truthy_series(offense['actionable_signal'])
        assert projected.loc[actionable].all(), 'actionable offensive row missing projection_points'


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
    validate_offense_projection_contract(offense, promotion_override_present=bool(g.get('promotion_override_present')))
    meta=load_json(out/'board-meta.json',{}); assert meta.get('adp_in_football_model') is False; assert meta.get('automatic_promotion') is False; assert 'build_league_value_board_on_M9' in str(meta.get('canonical_offense_value_source'))
    rankings=load_json(out/'rankings.json',{}); assert str(rankings.get('league_id'))==str(a.league_id); assert rankings.get('automatic_promotion') is False
    print(json.dumps({'status':'PASS','league_id':a.league_id,'rows':len(board),'positions':sorted(board.position.astype(str).unique().tolist())},indent=2)); return 0
if __name__=='__main__': raise SystemExit(main())
