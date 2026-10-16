#!/usr/bin/env python3
"""FIE M8: Team, Trenches and Matchup Intelligence.

The public baseline models mechanisms that are actually observable in FIE's
historical backbone: QB pressure environment, defensive pass-rush production,
coverage scheme/disruption and run-front context.  It does *not* call those
signals offensive-line grades.  True OL/DL inputs may be supplied through the
versioned optional source contract and are validated independently.

All matchup features remain residual challengers on top of M4 OOS projections.
A difficult defense can affect efficiency and volume in opposite directions, so
M8 exports separate efficiency-pressure and game-environment components rather
than one generic matchup multiplier.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from fie_research import CONTROL_BUILD, LATEST_COMPLETED_SEASON
from fie_m2 import FOLDS
from fie_m4 import feature_frame
from statistical_guardrails import promotion_gate
from fie_m7 import OFFENSE_POSITIONS, load_oos, residual_family_validation, add_derived_driver_features, model as residual_model, _serialize_fitted_residual_spec
from performance_source_contract import (
    TRENCH_COLUMNS, COVERAGE_COLUMNS, validate_team_source, prefixed_optional,
    validate_player_trench_source, aggregate_player_trenches_to_team, lag_team_features,
)

RESEARCH_BUILD = "V9.4-M8"
MILESTONE = "M8"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: str) -> dict:
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else {}


def _num(s) -> pd.Series:
    return pd.to_numeric(s, errors="coerce")


def add_missing_priors(df: pd.DataFrame) -> pd.DataFrame:
    d = df.sort_values(["canonical_player_id", "season", "week"]).copy()
    g = d.groupby(["canonical_player_id", "season"], group_keys=False)
    for c in ["def_sacks", "def_qb_hits", "tackles_for_loss", "def_pass_defended", "def_interceptions"]:
        if c in d.columns and f"{c}_prior4" not in d.columns:
            d[f"{c}_prior4"] = g[c].transform(lambda x: _num(x).shift(1).rolling(4, min_periods=2).mean())
    return d


def weighted_team_mean(g: pd.DataFrame, value: str, weight: Optional[str] = None) -> Optional[float]:
    if value not in g.columns:
        return None
    x = _num(g[value])
    ok = x.notna()
    if not ok.any():
        return None
    if weight and weight in g.columns:
        w = _num(g[weight]).clip(lower=0).where(ok)
        if w.notna().any() and float(w.fillna(0).sum()) > 0:
            return float(np.average(x[ok], weights=w[ok].fillna(0.0)))
    return float(x[ok].mean())


def sum_team(g: pd.DataFrame, value: str) -> Optional[float]:
    if value not in g.columns:
        return None
    x = _num(g[value]).dropna()
    return None if x.empty else float(x.sum())


def _percentile_by_week(d: pd.DataFrame, col: str, invert: bool = False) -> pd.Series:
    if col not in d.columns:
        return pd.Series(np.nan, index=d.index)
    x = _num(d[col])
    r = x.groupby([d.season, d.week]).rank(pct=True, method="average")
    return 1.0 - r if invert else r


def build_team_context(df: pd.DataFrame) -> pd.DataFrame:
    """One pregame row per team-week from lagged player features only."""
    d = add_missing_priors(df)
    rows: List[dict] = []
    for (season, week, team), g in d.groupby(["season", "week", "team"], dropna=False, sort=False):
        qb = g[g.position_model.eq("QB")]
        rush = g[g.position_model.isin(["EDGE", "IDL"])]
        cov = g[g.position_model.isin(["LB", "S", "CB"])]
        front = g[g.position_model.isin(["EDGE", "IDL", "LB", "S"])]
        rows.append({
            "season": int(season), "week": int(week), "team": str(team),
            # Offense pressure environment.  This includes OL + QB + previous opponents
            # and is deliberately not labelled an OL grade.
            "off_pressure_environment": weighted_team_mean(qb, "pfr_times_pressured_pct_prior4", "snap_share_prior4"),
            "off_sack_environment": weighted_team_mean(qb, "pfr_times_sacked_prior4", "snap_share_prior4"),
            "off_time_to_throw": weighted_team_mean(qb, "ngs_avg_time_to_throw_prior4", "snap_share_prior4"),
            "off_cpoe": weighted_team_mean(qb, "ngs_completion_percentage_above_expectation_prior4", "snap_share_prior4"),
            # Defensive pass-rush production and pressure context.
            "def_hurries_prior4": sum_team(rush, "pfr_def_times_hurried_prior4"),
            "def_hits_prior4": sum_team(rush, "pfr_def_times_hitqb_prior4"),
            "def_sacks_prior4": sum_team(rush, "def_sacks_prior4"),
            "def_pressure_context_rate": weighted_team_mean(rush, "def_part_pressure_context_rate_prior4", "defense_snap_share_prior4"),
            # Coverage scheme is separate from disruption/quality.
            "def_man_rate": weighted_team_mean(cov, "def_part_man_context_rate_prior4", "defense_snap_share_prior4"),
            "def_zone_rate": weighted_team_mean(cov, "def_part_zone_context_rate_prior4", "defense_snap_share_prior4"),
            "def_pass_defended_prior4": sum_team(cov, "def_pass_defended_prior4"),
            "def_interceptions_prior4": sum_team(cov, "def_interceptions_prior4"),
            # Run-front public context; box usage is scheme, TFL is disruption.
            "def_box_rate": weighted_team_mean(front, "def_part_avg_defenders_in_box_prior4", "defense_snap_share_prior4"),
            "def_tfl_prior4": sum_team(front, "tackles_for_loss_prior4"),
        })
    t = pd.DataFrame(rows)
    if t.empty:
        return t
    # Comparable 0-1 components within each historical week.  Missing components
    # remain missing rather than becoming neutral without disclosure.
    t["public_protection_environment_index"] = pd.concat([
        _percentile_by_week(t, "off_pressure_environment", invert=True),
        _percentile_by_week(t, "off_sack_environment", invert=True),
    ], axis=1).mean(axis=1, skipna=True)
    t["public_pass_rush_index"] = pd.concat([
        _percentile_by_week(t, "def_hurries_prior4"),
        _percentile_by_week(t, "def_hits_prior4"),
        _percentile_by_week(t, "def_sacks_prior4"),
        _percentile_by_week(t, "def_pressure_context_rate"),
    ], axis=1).mean(axis=1, skipna=True)
    t["public_coverage_disruption_index"] = pd.concat([
        _percentile_by_week(t, "def_pass_defended_prior4"),
        _percentile_by_week(t, "def_interceptions_prior4"),
    ], axis=1).mean(axis=1, skipna=True)
    t["public_run_front_index"] = pd.concat([
        _percentile_by_week(t, "def_tfl_prior4"),
    ], axis=1).mean(axis=1, skipna=True)
    # Pass rush and coverage are not independent football mechanisms. This explicit
    # synergy challenger asks whether disruption is amplified when both units are
    # strong, without pretending we know individual rusher-to-DB responsibility.
    if "public_pass_rush_index" in t and "public_coverage_disruption_index" in t:
        t["public_pressure_coverage_synergy_index"] = _num(t["public_pass_rush_index"]) * _num(t["public_coverage_disruption_index"])
    return t


def merge_optional_trenches(team: pd.DataFrame, source: pd.DataFrame, metric_prefix: str = "") -> pd.DataFrame:
    if source.empty:
        return team
    q = source.copy()
    if metric_prefix:
        q = q.rename(columns={c: metric_prefix + c for c in q.columns if c not in {"season","week","team"}})
    p = prefixed_optional(q)
    return team.merge(p, on=["season", "week", "team"], how="left")


def opponent_join(df: pd.DataFrame, team: pd.DataFrame) -> pd.DataFrame:
    if team.empty or "opponent_team" not in df.columns:
        return df.copy()
    cols = [c for c in team.columns if c not in {"team"}]
    opp = team[cols + ["team"]].rename(columns={"team": "opponent_team", **{
        c: f"opp_{c}" for c in cols if c not in {"season", "week"}
    }})
    return df.merge(opp, on=["season", "week", "opponent_team"], how="left")


def add_matchup_features(df: pd.DataFrame, team: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Dict[str, List[str]]]]:
    d = opponent_join(df, team)
    # Player-specific opponent interactions.  Direction is learned by Ridge; no
    # manually chosen fantasy-point bonus is embedded here.
    defs = {
        "m8_qb_pressure_collision": ("pfr_times_pressured_pct_prior4", "opp_public_pass_rush_index"),
        "m8_qb_ttt_passrush": ("ngs_avg_time_to_throw_prior4", "opp_public_pass_rush_index"),
        "m8_qb_accuracy_coverage": ("ngs_completion_percentage_above_expectation_prior4", "opp_public_coverage_disruption_index"),
        "m8_qb_accuracy_man": ("ngs_completion_percentage_above_expectation_prior4", "opp_def_man_rate"),
        "m8_rb_efficiency_runfront": ("ngs_rush_yards_over_expected_per_att_prior4", "opp_public_run_front_index"),
        "m8_rb_box_collision": ("ngs_percent_attempts_gte_eight_defenders_prior4", "opp_def_box_rate"),
        "m8_wr_airshare_passrush": ("ngs_percent_share_of_intended_air_yards_prior4", "opp_public_pass_rush_index"),
        "m8_wr_separation_coverage": ("ngs_avg_separation_prior4", "opp_public_coverage_disruption_index"),
        "m8_wr_separation_man": ("ngs_avg_separation_prior4", "opp_def_man_rate"),
        "m8_te_airshare_passrush": ("ngs_percent_share_of_intended_air_yards_prior4", "opp_public_pass_rush_index"),
        "m8_te_separation_coverage": ("ngs_avg_separation_prior4", "opp_public_coverage_disruption_index"),
        "m8_te_separation_man": ("ngs_avg_separation_prior4", "opp_def_man_rate"),
        "m8_qb_pressure_coverage_synergy": ("pfr_times_pressured_pct_prior4", "opp_public_pressure_coverage_synergy_index"),
        "m8_wr_air_synergy": ("ngs_percent_share_of_intended_air_yards_prior4", "opp_public_pressure_coverage_synergy_index"),
        "m8_te_air_synergy": ("ngs_percent_share_of_intended_air_yards_prior4", "opp_public_pressure_coverage_synergy_index"),
    }
    for name, (a, b) in defs.items():
        if a in d.columns and b in d.columns:
            d[name] = _num(d[a]) * _num(d[b])

    # True OL/DL challenger interactions only exist when the optional source does.
    premium_defs = {
        "m8_true_pass_protection_mismatch": ("premium_ol_pass_block_win_rate", "opp_premium_dl_pass_rush_win_rate"),
        "m8_true_pressure_mismatch": ("premium_ol_pressure_allowed_rate", "opp_premium_dl_pressure_rate"),
        "m8_true_run_block_mismatch": ("premium_ol_run_block_win_rate", "opp_premium_dl_run_stop_win_rate"),
    }
    for name, (a, b) in premium_defs.items():
        if a in d.columns and b in d.columns:
            if name == "m8_true_pass_protection_mismatch" or name == "m8_true_run_block_mismatch":
                d[name] = _num(d[a]) - _num(d[b])
            else:
                d[name] = _num(d[a]) * _num(d[b])

    playeragg_defs = {
        "m8_playeragg_pass_protection_mismatch": ("premium_playeragg_ol_pass_block_win_rate", "opp_premium_playeragg_dl_pass_rush_win_rate"),
        "m8_playeragg_pressure_mismatch": ("premium_playeragg_ol_pressure_allowed_rate", "opp_premium_playeragg_dl_pressure_rate"),
        "m8_playeragg_run_block_mismatch": ("premium_playeragg_ol_run_block_win_rate", "opp_premium_playeragg_dl_run_stop_win_rate"),
        "m8_playeragg_weak_link_pass": ("premium_playeragg_ol_pass_block_win_rate_weak_link", "opp_premium_playeragg_dl_pass_rush_win_rate_weak_link"),
    }
    for name,(a,b) in playeragg_defs.items():
        if a in d.columns and b in d.columns:
            d[name] = _num(d[a]) - _num(d[b]) if "pressure" not in name else _num(d[a]) * _num(d[b])

    charted_coverage_defs = {
        "m8_charted_qb_accuracy_coverage": ("ngs_completion_percentage_above_expectation_prior4", "opp_premium_def_coverage_success_rate"),
        "m8_charted_qb_two_high": ("ngs_avg_intended_air_yards_prior4", "opp_premium_def_two_high_rate"),
        "m8_charted_wr_separation_coverage": ("ngs_avg_separation_prior4", "opp_premium_def_coverage_success_rate"),
        "m8_charted_wr_press": ("ngs_avg_separation_prior4", "opp_premium_def_press_rate"),
        "m8_charted_te_separation_coverage": ("ngs_avg_separation_prior4", "opp_premium_def_coverage_success_rate"),
    }
    for name,(a,b) in charted_coverage_defs.items():
        if a in d.columns and b in d.columns: d[name] = _num(d[a]) * _num(d[b])

    catalog = {
        "QB": {
            "public_pass_rush_matchup": [x for x in ["opp_public_pass_rush_index", "m8_qb_pressure_collision", "m8_qb_ttt_passrush"] if x in d],
            "public_coverage_matchup": [x for x in ["opp_public_coverage_disruption_index", "opp_def_man_rate", "opp_def_zone_rate", "m8_qb_accuracy_coverage", "m8_qb_accuracy_man"] if x in d],
            "public_defensive_synergy_matchup": [x for x in ["opp_public_pressure_coverage_synergy_index", "m8_qb_pressure_coverage_synergy"] if x in d],
            "true_trench_matchup": [x for x in list(premium_defs) + list(playeragg_defs) if x in d],
            "charted_coverage_matchup": [x for x in ["opp_premium_def_coverage_success_rate","opp_premium_def_two_high_rate","opp_premium_def_press_rate","m8_charted_qb_accuracy_coverage","m8_charted_qb_two_high"] if x in d],
        },
        "RB": {
            "public_run_front_matchup": [x for x in ["opp_public_run_front_index", "opp_def_box_rate", "m8_rb_efficiency_runfront", "m8_rb_box_collision"] if x in d],
            "true_trench_matchup": [x for x in ["m8_true_run_block_mismatch", "m8_playeragg_run_block_mismatch"] if x in d],
        },
        "WR": {
            "public_pressure_receiving_matchup": [x for x in ["opp_public_pass_rush_index", "m8_wr_airshare_passrush"] if x in d],
            "public_coverage_receiving_matchup": [x for x in ["opp_public_coverage_disruption_index", "opp_def_man_rate", "opp_def_zone_rate", "m8_wr_separation_coverage", "m8_wr_separation_man"] if x in d],
            "public_defensive_synergy_matchup": [x for x in ["opp_public_pressure_coverage_synergy_index", "m8_wr_air_synergy"] if x in d],
            "charted_coverage_matchup": [x for x in ["opp_premium_def_coverage_success_rate","opp_premium_def_press_rate","opp_premium_def_man_rate","m8_charted_wr_separation_coverage","m8_charted_wr_press"] if x in d],
            "true_trench_matchup": [x for x in ["m8_true_pass_protection_mismatch", "m8_true_pressure_mismatch", "m8_playeragg_pass_protection_mismatch", "m8_playeragg_pressure_mismatch", "m8_playeragg_weak_link_pass"] if x in d],
        },
        "TE": {
            "public_pressure_receiving_matchup": [x for x in ["opp_public_pass_rush_index", "m8_te_airshare_passrush"] if x in d],
            "public_coverage_receiving_matchup": [x for x in ["opp_public_coverage_disruption_index", "opp_def_man_rate", "opp_def_zone_rate", "m8_te_separation_coverage", "m8_te_separation_man"] if x in d],
            "public_defensive_synergy_matchup": [x for x in ["opp_public_pressure_coverage_synergy_index", "m8_te_air_synergy"] if x in d],
            "charted_coverage_matchup": [x for x in ["opp_premium_def_coverage_success_rate","opp_premium_def_press_rate","opp_premium_def_man_rate","m8_charted_te_separation_coverage"] if x in d],
            "true_trench_matchup": [x for x in ["m8_true_pass_protection_mismatch", "m8_true_pressure_mismatch", "m8_playeragg_pass_protection_mismatch", "m8_playeragg_pressure_mismatch", "m8_playeragg_weak_link_pass"] if x in d],
        },
    }
    return d, catalog


def sequential_activation_composite(df: pd.DataFrame, oos: pd.DataFrame, catalog: Dict[str, Dict[str, List[str]]], aggregate: List[dict], m7: dict) -> dict:
    """Revalidate M8 as one combined residual model after the validated M7 feature set.

    Individual M8 families are first screened against canonical M4 OOS projections.
    This second gate asks the production-relevant question: does adding *all* passed
    matchup families improve a chronologically retrained M7-only residual model?
    The exported spec is one combined correction, so M7 and M8 are never added as
    independent point bonuses and correlated effects cannot be double counted.
    """
    passed={(r.get('position'),r.get('family')) for r in aggregate if r.get('status')=='validated_candidate'}
    m7_specs=(m7.get('driver_research',{}).get('activation_composite',{}).get('model_specs') or {})
    keys=['season','week','canonical_player_id','position_model']
    folds=[]; agg_rows=[]; specs={}
    for pos in OFFENSE_POSITIONS:
        m8_features=[]
        for fam,members in catalog.get(pos,{}).items():
            if (pos,fam) in passed:
                m8_features.extend([f for f in members if f in df.columns])
        m8_features=list(dict.fromkeys(m8_features))
        if not m8_features:
            continue
        m7_features=[f for f in (m7_specs.get(pos,{}).get('features') or []) if f in df.columns]
        combined=list(dict.fromkeys(m7_features+m8_features))
        keep=keys+combined
        z=oos.merge(df[keep].drop_duplicates(keys),on=keys,how='left')
        z=z[z.position_model.eq(pos)].copy()
        z['fantasy_points']=pd.to_numeric(z.fantasy_points,errors='coerce')
        z['fie_projection']=pd.to_numeric(z.fie_projection,errors='coerce')
        z['residual']=z.fantasy_points-z.fie_projection
        for train_seasons,test_season in FOLDS:
            tr=z[z.season.isin(train_seasons)].dropna(subset=['residual']).copy()
            te=z[z.season.eq(test_season)].dropna(subset=['fantasy_points','fie_projection']).copy()
            if len(tr)<120 or len(te)<35:
                continue
            # M7-only chronological challenger, when M7 itself previously cleared.
            if m7_features:
                tr7=tr[tr[m7_features].notna().any(axis=1)].copy(); te7=te[te[m7_features].notna().any(axis=1)].copy()
                if len(tr7)<100 or len(te7)<25:
                    continue
                m7pipe=residual_model();m7pipe.fit(tr7[m7_features],tr7.residual)
                m7corr=pd.Series(np.nan,index=te.index,dtype=float)
                idx=te7.index
                m7corr.loc[idx]=np.clip(m7pipe.predict(te7[m7_features]),-8.0,8.0)
            else:
                m7corr=pd.Series(0.0,index=te.index,dtype=float)
            trc=tr[tr[combined].notna().any(axis=1)].copy(); tec=te[te[combined].notna().any(axis=1)].copy()
            valid_idx=tec.index.intersection(m7corr.dropna().index)
            if len(trc)<100 or len(valid_idx)<25:
                continue
            pipe=residual_model();pipe.fit(trc[combined],trc.residual)
            corr=np.clip(pipe.predict(te.loc[valid_idx,combined]),-8.0,8.0)
            y=te.loc[valid_idx,'fantasy_points'].to_numpy(float)
            base=(te.loc[valid_idx,'fie_projection']+m7corr.loc[valid_idx]).to_numpy(float)
            adj=te.loc[valid_idx,'fie_projection'].to_numpy(float)+corr
            bmae=float(np.mean(np.abs(y-base))); amae=float(np.mean(np.abs(y-adj)))
            folds.append({'position':pos,'test_season':int(test_season),'n_train':int(len(trc)),'n_test':int(len(valid_idx)),
                          'baseline':'M7_COMPOSITE' if m7_features else 'M4_FIE',
                          'm7_features':m7_features,'m8_features':m8_features,'combined_features':combined,
                          'baseline_mae':bmae,'combined_mae':amae,
                          'incremental_mae_improvement':float((bmae-amae)/bmae) if bmae>0 else None})
        pf=[r for r in folds if r['position']==pos and r.get('incremental_mae_improvement') is not None]
        vals=[r['incremental_mae_improvement'] for r in pf];weights=[r['n_test'] for r in pf]
        gate=promotion_gate(vals,weights=weights,min_mean=.01,min_folds=4,require_positive_ci=True) if vals else {'robust':False,'ci95_low':None,'ci95_high':None}
        ar={'position':pos,'status':'validated_candidate' if gate.get('robust') else 'diagnostic_only','folds':len(pf),
            'n_test':int(sum(weights)) if weights else 0,'baseline':'M7_COMPOSITE' if m7_features else 'M4_FIE',
            'mean_incremental_mae_improvement':float(np.mean(vals)) if vals else None,
            'bootstrap_ci95_low':gate.get('ci95_low'),'bootstrap_ci95_high':gate.get('ci95_high'),
            'm7_features':m7_features,'m8_features':m8_features}
        agg_rows.append(ar)
        if ar['status']=='validated_candidate':
            spec=_serialize_fitted_residual_spec(z,combined)
            if spec:
                spec['gate']=ar;spec['baseline']='canonical M4/FIE weekly projection'
                spec['component_features']={'m7':m7_features,'m8':m8_features}
                spec['semantics']='single jointly revalidated M7+M8 residual correction; do not add a separate M7 correction'
                specs[pos]=spec
    return {'status':'validated_candidate' if specs else 'diagnostic_only',
            'rule':'M8 may influence live projections only through this sequential combined spec. If M7 is active, the combined M7+M8 correction replaces, rather than stacks on top of, the M7-only correction.',
            'folds':folds,'aggregate':agg_rows,'model_specs':specs}


def write_team_context(team: pd.DataFrame, derived_dir: str) -> Optional[str]:
    if team.empty or not derived_dir:
        return None
    p = Path(derived_dir) / "m8_team_matchup_context.csv.gz"
    p.parent.mkdir(parents=True, exist_ok=True)
    team.to_csv(p, index=False, compression="gzip")
    return str(p)


def summarize_team_context(team: pd.DataFrame) -> dict:
    if team.empty:
        return {"rows": 0, "teams": 0, "seasons": []}
    return {
        "rows": int(len(team)), "teams": int(team.team.nunique()),
        "seasons": sorted(int(x) for x in team.season.dropna().unique()),
        "public_pass_rush_coverage": float(team.public_pass_rush_index.notna().mean()) if "public_pass_rush_index" in team else 0.0,
        "public_coverage_coverage": float(team.public_coverage_disruption_index.notna().mean()) if "public_coverage_disruption_index" in team else 0.0,
        "public_run_front_coverage": float(team.public_run_front_index.notna().mean()) if "public_run_front_index" in team else 0.0,
        "public_pressure_coverage_synergy_coverage": float(team.public_pressure_coverage_synergy_index.notna().mean()) if "public_pressure_coverage_synergy_index" in team else 0.0,
    }


def source_ledger(health, player_health=None, coverage_health=None) -> List[dict]:
    player_health = player_health or health
    coverage_health = coverage_health or health
    return [
        {
            "analysis": "true_offensive_line_unit_quality", "source": health.path,
            "status": "available_challenger" if health.status == "ok" and any(c.startswith("ol_") for c in health.columns) else "blocked_optional_source_not_available",
            "reason": health.reason or "Requires historical point-in-time OL team metrics; public pressure environment is not relabelled as OL quality.",
        },
        {
            "analysis": "true_defensive_line_unit_quality", "source": health.path,
            "status": "available_challenger" if health.status == "ok" and any(c.startswith("dl_") for c in health.columns) else "blocked_optional_source_not_available",
            "reason": health.reason or "Requires historical point-in-time DL pass-rush/run-stop metrics.",
        },
        {
            "analysis": "player_level_ol_dl_performance", "source": player_health.path,
            "status": "available_challenger" if player_health.status == "ok" else "blocked_optional_source_not_available",
            "reason": player_health.reason or "Player-week OL/DL grades are snap-weighted into explicit unit aggregates; weakest-link features remain separate challengers.",
        },
        {
            "analysis": "charted_team_coverage_quality_and_scheme", "source": coverage_health.path,
            "status": "available_challenger" if coverage_health.status == "ok" else "blocked_optional_source_not_available",
            "reason": coverage_health.reason or "Team coverage charting is lagged before use and validated separately from public disruption proxies.",
        },
        {
            "analysis": "individual_wr_db_responsibility", "source": "none",
            "status": "blocked_missing_coverage_responsibility_history",
            "reason": "Team coverage/scheme context is available publicly; individual WR-CB responsibility cannot be inferred from nearest defender or a nominal CB1 label.",
        },
        {
            "analysis": "individual_blocker_rusher_assignment", "source": "none",
            "status": "blocked_missing_assignment_history",
            "reason": "Team-level OL/DL challengers are supported; player-vs-player blocker/rusher effects require audited assignment-level history.",
        },
    ]


def run(args) -> dict:
    df, _, _, m1_core, _, enrichment = feature_frame(args)
    df = add_derived_driver_features(df)
    max_season = int(pd.to_numeric(df.season, errors="coerce").max()) if len(df) else LATEST_COMPLETED_SEASON
    trench_raw, health = validate_team_source(args.trench_source, TRENCH_COLUMNS, max_season=max_season)
    trench = lag_team_features(trench_raw, [c for c in TRENCH_COLUMNS if c in trench_raw])
    player_trench, player_health = validate_player_trench_source(args.trench_player_source, max_season=max_season)
    player_units_raw = aggregate_player_trenches_to_team(player_trench)
    player_units = lag_team_features(player_units_raw, [c for c in player_units_raw.columns if c not in {"season","week","team","player_trench_rows"}])
    coverage_raw, coverage_health = validate_team_source(args.coverage_source, COVERAGE_COLUMNS, max_season=max_season)
    coverage = lag_team_features(coverage_raw, [c for c in COVERAGE_COLUMNS if c in coverage_raw])
    team = build_team_context(df)
    team = merge_optional_trenches(team, trench)
    team = merge_optional_trenches(team, player_units, metric_prefix="playeragg_")
    team = merge_optional_trenches(team, coverage)
    enriched, catalog = add_matchup_features(df, team)
    oos = load_oos(args.derived_dir, args.fixture, enriched)
    folds, agg = residual_family_validation(enriched, oos, catalog)
    path = write_team_context(team, args.derived_dir)
    validated = sorted({f"{r['position']}:{r['family']}" for r in agg if r.get("status") == "validated_candidate"})
    m1 = load_json(args.m1_bundle) or m1_core
    m7 = load_json(args.m7_bundle)
    sequential = sequential_activation_composite(enriched, oos, catalog, agg, m7)
    return {
        "schema_version": 8, "milestone": MILESTONE, "control_build": CONTROL_BUILD,
        "research_build": RESEARCH_BUILD, "generated_at": utc_now(), "status": "complete",
        "steps_completed": [34, 35, 36, 37],
        "scoring_signature": m7.get("scoring_signature") or m1.get("scoring", {}).get("signature"),
        "methodology": {
            "step34": "Build pregame team pressure, pass-rush, coverage-scheme/disruption and run-front context from lagged public player signals. Public pressure environment is not an OL grade.",
            "step35": "Optionally join versioned point-in-time true OL/DL team metrics and player-week OL/DL performance. Player grades are snap-weighted into explicit unit aggregates with separate weakest-link challengers; missing optional data stays blocked.",
            "step36": "Create player-specific opponent interactions for QB pressure/coverage, RB run fronts, and WR/TE pressure+coverage. Scheme and efficiency are separate components.",
            "step37": "Validate every matchup family as an incremental residual correction after M4 FIE. No generic strength-of-schedule multiplier is activated from descriptive history.",
        },
        "team_matchup_context": {
            "summary": summarize_team_context(team), "derived_table": path,
            "public_component_semantics": {
                "public_protection_environment_index": "observed prior QB pressure/sack environment; OL+QB+past-opponent mixture, not OL talent",
                "public_pass_rush_index": "lagged DL/EDGE hurry-hit-sack and pressure-context composite",
                "public_coverage_disruption_index": "lagged pass-defense/interception disruption composite; man/zone rates are exported separately as scheme",
                "public_run_front_index": "lagged run-front disruption proxy; does not claim player-level run-block attribution",
                "public_pressure_coverage_synergy_index": "team-level interaction between lagged pass-rush and coverage disruption; captures DL/DB ecosystem synergy without individual assignment claims",
            },
        },
        "matchup_validation": {"folds": folds, "aggregate": agg, "validated_candidate_families": validated,
                               "sequential_activation": sequential,
                               "activation_status": "SEQUENTIAL_SPEC_AVAILABLE" if sequential.get("model_specs") else "DIAGNOSTIC_ONLY_UNTIL_CONSUMER_GATE"},
        "optional_trench_source": health.__dict__,
        "optional_player_trench_source": player_health.__dict__,
        "optional_coverage_source": coverage_health.__dict__,
        "optional_source_timing": "All realised team/player weekly charting is shifted before rolling into the prediction week; same-game leakage is prohibited.",
        "player_trench_aggregation": {"rows": int(len(player_units)), "rule": "snap-weighted where charted workload is supplied; weak-link metrics exported separately"},
        "source_ledger": source_ledger(health, player_health, coverage_health),
        "dst_bridge": {
            "status": "challenger_contract_ready",
            "features": ["public_pass_rush_index", "public_coverage_disruption_index", "public_pressure_coverage_synergy_index", "public_run_front_index", "def_man_rate", "def_zone_rate"],
            "rule": "D/ST may consume only validated M8 component families; raw defense outcomes continue to be projected once and league scoring is applied afterwards.",
        },
        "offense_feedback_bridge": {
            "status": "challenger_contract_ready",
            "rule": "Opponent efficiency effects and opportunity/game-script effects are separate. A difficult defense is never encoded as an automatic volume reduction.",
        },
        "upstream": {"m1_status": m1.get("status"), "m7_status": m7.get("status")},
        "limitations": [
            "Individual WR-DB and blocker-rusher assignments remain blocked without responsibility/assignment history.",
            "Public pressure environment contains QB behavior and prior opponent effects and therefore cannot be presented as pure OL quality.",
            "Coverage scheme rates describe how a defense plays, not whether it plays well; disruption is modelled separately.",
        ],
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE M8 Team/Trenches/Matchup research")
    p.add_argument("--derived-dir", default="data/research/derived")
    for n in range(1, 8):
        p.add_argument(f"--m{n}-bundle", default=f"data/research/milestone{n}.json")
    p.add_argument("--cache-dir", default=".cache/fie-research")
    p.add_argument("--seasons", default=f"2019-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--trench-source", default="")
    p.add_argument("--trench-player-source", default="")
    p.add_argument("--coverage-source", default="", help="Optional realised team-week coverage charting; automatically lagged before use")
    p.add_argument("--output", default="data/research/milestone8.json")
    p.add_argument("--fixture", action="store_true")
    a = p.parse_args(argv)
    if isinstance(a.seasons, str):
        lo, hi = map(int, a.seasons.split("-")); a.seasons = list(range(lo, hi + 1))
    return a


def main(argv=None):
    args = parse_args(argv); bundle = run(args)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2, allow_nan=False))
    print(f"Wrote {out} status={bundle['status']} validated={len(bundle['matchup_validation']['validated_candidate_families'])}")


if __name__ == "__main__":
    main()
