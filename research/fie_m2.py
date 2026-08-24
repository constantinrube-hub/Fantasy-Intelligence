#!/usr/bin/env python3
"""Fantasy Intelligence Engine V8.4-M2 research pipeline.

Implements roadmap Steps 10-15 on top of Milestone 1 derived tables:
10 position production decomposition, 11 opportunity-based xFP,
12 regression validation, 13 opportunity-change detection,
14 teammate competition models, 15 vacated-opportunity redistribution.

All outputs remain diagnostic_only. Nothing here changes the live V8.2.2
Draft/Waiver/Weekly scoring model.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_research import (
    CONTROL_BUILD, DEFAULT_PPR, POSITIONS, PRIMARY_SEASONS,
    add_pregame_features, build_identity, derive_opportunity, make_fixture,
    merge_pbp_team_opportunity, prep_player_week, prep_snaps, prep_team_week,
    score_rows, scoring_signature,
)

RESEARCH_BUILD = "V8.4-M2"
MILESTONE = "M2"
FOLDS = [(list(range(2019, test_season)), test_season) for test_season in PRIMARY_SEASONS if test_season >= 2022]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite(v) -> bool:
    try:
        return math.isfinite(float(v))
    except Exception:
        return False


def safe_corr(x: pd.Series, y: pd.Series) -> Tuple[Optional[float], int]:
    z = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(z) < 8 or z.x.nunique() < 2 or z.y.nunique() < 2:
        return None, len(z)
    r = spearmanr(z.x, z.y).statistic
    return (None if not np.isfinite(r) else float(r)), len(z)


def rmse(y, p) -> float:
    return float(math.sqrt(mean_squared_error(y, p)))


def model() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=6.0)),
    ])


def clip01(a):
    return np.clip(np.asarray(a, dtype=float), 0.0, 1.0)


def load_tables(derived_dir: Path) -> Tuple[pd.DataFrame, pd.DataFrame]:
    pp = derived_dir / "player_week.csv.gz"
    tp = derived_dir / "team_week.csv.gz"
    if not pp.exists() or not tp.exists():
        raise FileNotFoundError(
            f"Milestone 1 derived tables not found in {derived_dir}. Run fie_research.py first."
        )
    p = pd.read_csv(pp, low_memory=False)
    t = pd.read_csv(tp, low_memory=False)
    return p, t


def fixture_tables() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Rebuild M1 fixture in-memory and add deterministic teammate absences.

    The absence perturbation exists only to exercise Step 15 in CI. It is not a
    synthetic claim about the NFL and never ships as empirical output.
    """
    players, pw_all, tw_all, snaps_all = make_fixture()
    identity, _ = build_identity(players, pd.DataFrame())
    pframes = [pw_all[pw_all.season == s].copy() for s in sorted(pw_all.season.unique())]
    tframes = [tw_all[tw_all.season == s].copy() for s in sorted(tw_all.season.unique())]
    sframes = [snaps_all[snaps_all.season == s].copy() for s in sorted(snaps_all.season.unique())]
    scoring = dict(DEFAULT_PPR)
    pw, _, _ = prep_player_week(pframes, identity, scoring)
    tw = prep_team_week(tframes)
    snaps, _ = prep_snaps(sframes, identity)
    d = derive_opportunity(pw, tw, snaps, pd.DataFrame())
    metrics = [
        "snap_share", "offense_snap_share", "defense_snap_share", "target_share",
        "carry_share", "qb_rush_share", "red_zone_carry_share", "inside_10_carry_share",
        "inside_5_carry_share", "red_zone_target_share", "end_zone_target_share_proxy",
        "pass_rush_opportunity_proxy", "tackle_opportunity_proxy", "coverage_opportunity_proxy",
    ]
    d = add_pregame_features(d, metrics)
    # Force a few historical absence episodes only for integrity testing.
    mask = (
        d["season"].isin([2023, 2024, 2025])
        & d["week"].isin([10, 11])
        & d["position_model"].eq("WR")
        & d["canonical_player_id"].astype(str).str.endswith("0002")
    )
    d = d.loc[~mask].copy()
    return d, tw


def add_team_context(player: pd.DataFrame, team: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    t = team.copy().sort_values(["team", "season", "week"])
    volume = [c for c in [
        "team_plays", "team_dropbacks", "team_pass_attempts", "team_rush_attempts",
        "team_red_zone_plays", "team_goal_line_plays"
    ] if c in t.columns]
    for c in volume:
        t[c] = pd.to_numeric(t[c], errors="coerce")
        t[f"{c}_prior4_team"] = t.groupby("team")[c].transform(lambda s: s.shift(1).rolling(4, min_periods=2).mean())
        t[f"{c}_prior8_team"] = t.groupby("team")[c].transform(lambda s: s.shift(1).rolling(8, min_periods=3).mean())
    # Opponent pregame volume from the opponent's offense.
    opp_cols = ["season", "week", "team"] + [f"{c}_prior4_team" for c in volume] + [f"{c}_prior8_team" for c in volume]
    opp = t[opp_cols].rename(columns={"team": "opponent_team", **{
        f"{c}_prior4_team": f"opponent_{c}_prior4" for c in volume
    }, **{
        f"{c}_prior8_team": f"opponent_{c}_prior8" for c in volume
    }})
    t = t.merge(opp, on=["season", "week", "opponent_team"], how="left")
    # Preserve opponent_team on real M1-derived player rows. Fixture rows may already
    # contain it, so only merge that key when it is absent to avoid _x/_y suffixes.
    keep = ["season", "week", "team"]
    if "opponent_team" not in player.columns:
        keep.append("opponent_team")
    keep += [c for c in t.columns if c != "opponent_team" and (c.endswith("_team") or c.startswith("opponent_team_"))]
    # The opponent_* names above actually start opponent_team_plays..., opponent_team_pass..., etc.
    team_ctx = t[keep].drop_duplicates(["season", "week", "team"])
    p = player.merge(team_ctx, on=["season", "week", "team"], how="left")
    return p, t


def _team_group_sum(df: pd.DataFrame, value: str, eligible: pd.Series) -> pd.Series:
    v = pd.to_numeric(df[value], errors="coerce").where(eligible)
    return v.groupby([df.season, df.week, df.team]).transform("sum")


def _team_group_count(df: pd.DataFrame, value: str, eligible: pd.Series, threshold: float) -> pd.Series:
    v = (pd.to_numeric(df[value], errors="coerce").fillna(0) >= threshold) & eligible
    return v.groupby([df.season, df.week, df.team]).transform("sum")


def _team_hhi(df: pd.DataFrame, value: str, eligible: pd.Series) -> pd.Series:
    x = pd.to_numeric(df[value], errors="coerce").fillna(0).where(eligible, 0.0)
    sq = x * x
    return sq.groupby([df.season, df.week, df.team]).transform("sum")


def add_competition_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in ["target_share_prior4", "carry_share_prior4", "defense_snap_share_prior4", "snap_share_prior4"]:
        if c not in d: d[c] = np.nan
    recv = d.position_model.isin(["WR", "TE", "RB"])
    rb = d.position_model.eq("RB")
    tackle = d.position_model.isin(["LB", "S"])
    rushers = d.position_model.isin(["EDGE", "IDL"])

    recv_total = _team_group_sum(d, "target_share_prior4", recv)
    d["receiving_competition_index"] = np.where(recv, recv_total - pd.to_numeric(d.target_share_prior4, errors="coerce").fillna(0), np.nan)
    d["receiving_competitor_count"] = np.where(recv, _team_group_count(d, "target_share_prior4", recv, .08) - (pd.to_numeric(d.target_share_prior4, errors="coerce").fillna(0) >= .08).astype(int), np.nan)
    d["receiving_concentration_hhi"] = np.where(recv, _team_hhi(d, "target_share_prior4", recv), np.nan)

    rb_total = _team_group_sum(d, "carry_share_prior4", rb)
    d["backfield_competition_index"] = np.where(rb, rb_total - pd.to_numeric(d.carry_share_prior4, errors="coerce").fillna(0), np.nan)
    d["backfield_competitor_count"] = np.where(rb, _team_group_count(d, "carry_share_prior4", rb, .15) - (pd.to_numeric(d.carry_share_prior4, errors="coerce").fillna(0) >= .15).astype(int), np.nan)

    tk_total = _team_group_sum(d, "defense_snap_share_prior4", tackle)
    d["tackle_competition_index"] = np.where(tackle, tk_total - pd.to_numeric(d.defense_snap_share_prior4, errors="coerce").fillna(0), np.nan)
    pr_total = _team_group_sum(d, "defense_snap_share_prior4", rushers)
    d["pass_rush_support_index"] = np.where(rushers, pr_total - pd.to_numeric(d.defense_snap_share_prior4, errors="coerce").fillna(0), np.nan)
    return d


def add_position_shares(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    for c in ["attempts", "targets", "carries"]:
        if c not in d: d[c] = 0.0
        d[c] = pd.to_numeric(d[c], errors="coerce").fillna(0.0)
    d["qb_pass_attempt_share"] = np.where((d.position_model == "QB") & (pd.to_numeric(d.team_pass_attempts, errors="coerce") > 0), d.attempts / pd.to_numeric(d.team_pass_attempts, errors="coerce"), np.nan)
    d = d.sort_values(["canonical_player_id", "season", "week"])
    g = d.groupby("canonical_player_id", group_keys=False)
    for c in ["qb_pass_attempt_share", "receiving_competition_index", "backfield_competition_index", "tackle_competition_index", "pass_rush_support_index"]:
        if c not in d: continue
        d[f"{c}_prior4"] = g[c].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(4, min_periods=2).mean())
        d[f"{c}_prior8"] = g[c].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(8, min_periods=3).mean())
    return d


def team_oos_predictions(team: pd.DataFrame) -> Tuple[pd.DataFrame, List[dict]]:
    t = team.copy().sort_values(["team", "season", "week"])
    volume = [c for c in ["team_plays", "team_dropbacks", "team_pass_attempts", "team_rush_attempts", "team_red_zone_plays", "team_goal_line_plays"] if c in t.columns]
    # add priors if absent
    for c in volume:
        if f"{c}_prior4_team" not in t:
            t[f"{c}_prior4_team"] = t.groupby("team")[c].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(4, min_periods=2).mean())
            t[f"{c}_prior8_team"] = t.groupby("team")[c].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(8, min_periods=3).mean())
    # Add opponent priors by self-join if not already present.
    for c in volume:
        col = f"opponent_{c}_prior4"
        if col not in t:
            o = t[["season","week","team",f"{c}_prior4_team",f"{c}_prior8_team"]].rename(columns={"team":"opponent_team",f"{c}_prior4_team":col,f"{c}_prior8_team":f"opponent_{c}_prior8"})
            t = t.merge(o,on=["season","week","opponent_team"],how="left")
    out = []
    val = []
    for train_seasons, test_season in FOLDS:
        test_mask = t.season.eq(test_season)
        pred_piece = t.loc[test_mask, ["season","week","team","opponent_team"]].copy()
        for target in volume:
            base = f"{target}_prior4_team"
            fs = [base, f"{target}_prior8_team", f"opponent_{target}_prior4", f"opponent_{target}_prior8"]
            fs = [f for f in fs if f in t.columns]
            tr = t[t.season.isin(train_seasons)].dropna(subset=[target, base]).copy()
            te = t[test_mask].dropna(subset=[target, base]).copy()
            if len(tr) < 100 or len(te) < 20:
                pred_piece[f"pred_{target}"] = np.nan
                continue
            m = model(); m.fit(tr[fs], pd.to_numeric(tr[target], errors="coerce"))
            pp = m.predict(t.loc[test_mask, fs])
            pred_piece[f"pred_{target}"] = np.maximum(0, pp)
            tepred = m.predict(te[fs])
            b = pd.to_numeric(te[base], errors="coerce").to_numpy(float)
            y = pd.to_numeric(te[target], errors="coerce").to_numpy(float)
            mae = mean_absolute_error(y, tepred); bmae = mean_absolute_error(y, b)
            rank, _ = safe_corr(pd.Series(tepred), pd.Series(y))
            val.append({
                "target": target, "train_start": min(train_seasons), "train_end": max(train_seasons), "test_season": test_season,
                "n_test": int(len(te)), "baseline_mae": float(bmae), "model_mae": float(mae), "rmse": rmse(y, tepred),
                "spearman": rank, "mae_improvement_vs_prior4": float((bmae-mae)/bmae) if bmae > 0 else None,
                "features": fs,
            })
        out.append(pred_piece)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(), val


COMPONENTS = {
    "QB": [
        ("snap_share", "snap_share", "pred_snap_share"),
        ("pass_attempt_share", "qb_pass_attempt_share", "pred_qb_pass_attempt_share"),
        ("rush_share", "qb_rush_share", "pred_qb_rush_share"),
    ],
    "RB": [
        ("snap_share", "offense_snap_share", "pred_offense_snap_share"),
        ("carry_share", "carry_share", "pred_carry_share"),
        ("target_share", "target_share", "pred_target_share"),
    ],
    "WR": [
        ("participation", "offense_snap_share", "pred_offense_snap_share"),
        ("target_share", "target_share", "pred_target_share"),
    ],
    "TE": [
        ("participation", "offense_snap_share", "pred_offense_snap_share"),
        ("target_share", "target_share", "pred_target_share"),
    ],
    "EDGE": [("defense_participation", "defense_snap_share", "pred_defense_snap_share")],
    "IDL": [("defense_participation", "defense_snap_share", "pred_defense_snap_share")],
    "LB": [("defense_participation", "defense_snap_share", "pred_defense_snap_share")],
    "S": [("defense_participation", "defense_snap_share", "pred_defense_snap_share")],
    "CB": [("defense_participation", "defense_snap_share", "pred_defense_snap_share")],
}


def component_features(pos: str, target: str, include_competition: bool = True) -> List[str]:
    f = [f"{target}_prior4", f"{target}_prior8", "fp_prior_4", "fp_prior_8"]
    # Generic snap-share history is an additional predictor for non-snap targets.
    # Do not append offense/defense prior columns a second time when they are
    # already the target-specific first two features. Duplicate DataFrame column
    # names are rejected by newer sklearn/narwhals versions in GitHub Actions.
    if target not in {"snap_share", "offense_snap_share", "defense_snap_share"}:
        f += ["snap_share_prior4", "snap_share_prior8"]
    if include_competition:
        if pos in ["WR","TE"] or (pos == "RB" and target == "target_share"):
            f += ["receiving_competition_index", "receiving_competitor_count", "receiving_concentration_hhi"]
        if pos == "RB" and target == "carry_share":
            f += ["backfield_competition_index", "backfield_competitor_count"]
        if pos in ["LB","S"]:
            f += ["tackle_competition_index"]
        if pos in ["EDGE","IDL"]:
            f += ["pass_rush_support_index"]
    # Preserve feature order while guaranteeing uniqueness for DataFrame consumers.
    return list(dict.fromkeys(f))


def _ensure_prior_columns(d: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    z = d.sort_values(["canonical_player_id","season","week"]).copy()
    g = z.groupby("canonical_player_id", group_keys=False)
    for c in cols:
        if c not in z: z[c] = np.nan
        for n, mins in [(4,2),(8,3)]:
            pc=f"{c}_prior{n}"
            if pc not in z:
                z[pc]=g[c].transform(lambda s, n=n, mins=mins: pd.to_numeric(s,errors="coerce").shift(1).rolling(n,min_periods=mins).mean())
    return z


def player_oos_components(df: pd.DataFrame, team_preds: pd.DataFrame, include_competition: bool = True) -> Tuple[pd.DataFrame, List[dict]]:
    d = _ensure_prior_columns(df, ["snap_share","offense_snap_share","defense_snap_share","qb_pass_attempt_share","qb_rush_share","carry_share","target_share"])
    # V8.9 HOTFIX: real M1 player_week rows may not carry opponent_team.
    # Recover it from the time-safe team prediction key before the main merge.
    if "opponent_team" not in d.columns:
        opp_key = team_preds[["season", "week", "team", "opponent_team"]].drop_duplicates(["season", "week", "team"])
        d = d.merge(opp_key, on=["season", "week", "team"], how="left")
    d = d.merge(team_preds, on=["season","week","team","opponent_team"], how="left")
    # Opponent predicted offense becomes defensive opportunity volume.
    opp = team_preds[[c for c in team_preds.columns if c in ["season","week","team","pred_team_plays","pred_team_dropbacks","pred_team_rush_attempts"]]].copy()
    if not opp.empty:
        opp = opp.rename(columns={"team":"opponent_team","pred_team_plays":"pred_defensive_opponent_plays","pred_team_dropbacks":"pred_defensive_opponent_dropbacks","pred_team_rush_attempts":"pred_defensive_opponent_rush_attempts"})
        d = d.merge(opp,on=["season","week","opponent_team"],how="left")
    rows=[]; validations=[]
    for train_seasons, test_season in FOLDS:
        for pos in POSITIONS:
            z=d[d.position_model.eq(pos)].copy()
            if z.empty: continue
            piece=z[z.season.eq(test_season)].copy()
            if piece.empty: continue
            for label,target,predcol in COMPONENTS.get(pos,[]):
                fs=[f for f in component_features(pos,target,include_competition) if f in z.columns and pd.to_numeric(z[f],errors="coerce").notna().any()]
                base=f"{target}_prior4"
                tr=z[z.season.isin(train_seasons)].dropna(subset=[target,base]).copy()
                te=z[z.season.eq(test_season)].dropna(subset=[target,base]).copy()
                if len(tr)<40 or len(te)<10 or not fs:
                    piece[predcol]=np.nan; continue
                m=model(); m.fit(tr[fs],pd.to_numeric(tr[target],errors="coerce"))
                pred=clip01(m.predict(piece[fs])); piece[predcol]=pred
                tep=clip01(m.predict(te[fs])); y=pd.to_numeric(te[target],errors="coerce").to_numpy(float); bp=clip01(pd.to_numeric(te[base],errors="coerce").to_numpy(float))
                mae=float(mean_absolute_error(y,tep)); bmae=float(mean_absolute_error(y,bp)); rank,_=safe_corr(pd.Series(tep),pd.Series(y))
                validations.append({"position":pos,"component":label,"target":target,"train_start":min(train_seasons),"train_end":max(train_seasons),"test_season":test_season,"n_test":int(len(te)),"baseline_mae":bmae,"model_mae":mae,"spearman":rank,"mae_improvement_vs_prior4":float((bmae-mae)/bmae) if bmae>0 else None,"features":fs,"competition_enabled":include_competition})
            # Compose predicted opportunity counts.
            if pos=="QB":
                piece["pred_pass_attempts"] = pd.to_numeric(piece.get("pred_team_pass_attempts"),errors="coerce") * pd.to_numeric(piece.get("pred_qb_pass_attempt_share"),errors="coerce")
                piece["pred_carries"] = pd.to_numeric(piece.get("pred_team_rush_attempts"),errors="coerce") * pd.to_numeric(piece.get("pred_qb_rush_share"),errors="coerce")
            elif pos=="RB":
                piece["pred_carries"] = pd.to_numeric(piece.get("pred_team_rush_attempts"),errors="coerce") * pd.to_numeric(piece.get("pred_carry_share"),errors="coerce")
                piece["pred_targets"] = pd.to_numeric(piece.get("pred_team_pass_attempts"),errors="coerce") * pd.to_numeric(piece.get("pred_target_share"),errors="coerce")
            elif pos in ["WR","TE"]:
                piece["pred_targets"] = pd.to_numeric(piece.get("pred_team_pass_attempts"),errors="coerce") * pd.to_numeric(piece.get("pred_target_share"),errors="coerce")
            else:
                volume = "pred_defensive_opponent_dropbacks" if pos in ["EDGE","IDL","CB"] else "pred_defensive_opponent_plays"
                piece["pred_defensive_opportunities"] = pd.to_numeric(piece.get(volume),errors="coerce") * pd.to_numeric(piece.get("pred_defense_snap_share"),errors="coerce")
            rows.append(piece)
    out=pd.concat(rows,ignore_index=True,sort=False) if rows else pd.DataFrame()
    return out, validations


def decomposition_count_validation(pred: pd.DataFrame) -> List[dict]:
    out=[]
    for pos in POSITIONS:
        z=pred[pred.position_model.eq(pos)].copy()
        if z.empty: continue
        checks=[]
        if pos=="QB": checks=[("pass_attempts","attempts","pred_pass_attempts"),("carries","carries","pred_carries")]
        elif pos=="RB": checks=[("carries","carries","pred_carries"),("targets","targets","pred_targets")]
        elif pos in ["WR","TE"]: checks=[("targets","targets","pred_targets")]
        else:
            actual = "pass_rush_opportunity_proxy" if pos in ["EDGE","IDL"] else ("coverage_opportunity_proxy" if pos=="CB" else "tackle_opportunity_proxy")
            checks=[("defensive_opportunity_proxy",actual,"pred_defensive_opportunities")]
        for label,a,p in checks:
            if a not in z or p not in z: continue
            for season in sorted(z.season.dropna().astype(int).unique()):
                q=z[z.season.eq(season)][[a,p]].apply(pd.to_numeric,errors="coerce").dropna()
                if len(q)<8: continue
                mae=float(mean_absolute_error(q[a],q[p])); rank,_=safe_corr(q[p],q[a])
                out.append({"position":pos,"component":label,"test_season":int(season),"n":int(len(q)),"mae":mae,"rmse":rmse(q[a],q[p]),"spearman":rank})
    return out


def xfp_features(pos: str, realized: bool) -> Tuple[List[str], List[str]]:
    """Return actual opportunity features and their predicted counterparts.

    No realized efficiency/outcome feature (receptions, yards, TDs, tackles, sacks,
    interceptions) is allowed into the opportunity xFP model.
    """
    if pos=="QB":
        a=["attempts","carries","red_zone_carry_share","inside_5_carry_share"]
        p=["pred_pass_attempts","pred_carries","red_zone_carry_share_prior4","inside_5_carry_share_prior4"]
    elif pos=="RB":
        a=["carries","targets","red_zone_carry_share","inside_10_carry_share","inside_5_carry_share","red_zone_target_share"]
        p=["pred_carries","pred_targets","red_zone_carry_share_prior4","inside_10_carry_share_prior4","inside_5_carry_share_prior4","red_zone_target_share_prior4"]
    elif pos in ["WR","TE"]:
        a=["targets","red_zone_target_share","end_zone_target_share_proxy"]
        p=["pred_targets","red_zone_target_share_prior4","end_zone_target_share_proxy_prior4"]
    elif pos in ["EDGE","IDL"]:
        a=["pass_rush_opportunity_proxy","defense_snap_share","defensive_opponent_dropbacks"]
        p=["pred_defensive_opportunities","pred_defense_snap_share","pred_defensive_opponent_dropbacks"]
    elif pos in ["LB","S"]:
        a=["tackle_opportunity_proxy","defense_snap_share","defensive_opponent_plays"]
        p=["pred_defensive_opportunities","pred_defense_snap_share","pred_defensive_opponent_plays"]
    else:
        a=["coverage_opportunity_proxy","defense_snap_share","defensive_opponent_dropbacks"]
        p=["pred_defensive_opportunities","pred_defense_snap_share","pred_defensive_opponent_dropbacks"]
    return (a if realized else p), a


def build_xfp(pred: pd.DataFrame, full: pd.DataFrame) -> Tuple[pd.DataFrame, List[dict]]:
    p=pred.copy(); val=[]
    p["opportunity_xfp_realized"]=np.nan; p["opportunity_xfp_pregame"]=np.nan
    for train_seasons,test_season in FOLDS:
        for pos in POSITIONS:
            tr=full[(full.position_model.eq(pos)) & (full.season.isin(train_seasons))].copy()
            te_idx=p.index[(p.position_model.eq(pos)) & (p.season.eq(test_season))]
            if tr.empty or len(te_idx)<8: continue
            actual_fs,_=xfp_features(pos,True); pred_fs,_=xfp_features(pos,False)
            actual_fs=[f for f in actual_fs if f in tr.columns and pd.to_numeric(tr[f],errors="coerce").notna().any()]
            # For test realized xFP, same opportunity columns must exist in p.
            actual_fs=[f for f in actual_fs if f in p.columns]
            pred_fs=[f for f in pred_fs if f in p.columns]
            if not actual_fs: continue
            tr=tr.dropna(subset=["fantasy_points"]).copy()
            if len(tr)<40: continue
            m=model(); m.fit(tr[actual_fs],pd.to_numeric(tr.fantasy_points,errors="coerce"))
            realized=np.maximum(0,m.predict(p.loc[te_idx,actual_fs]))
            p.loc[te_idx,"opportunity_xfp_realized"]=realized
            # Map predicted columns to actual model feature names by constructing a frame.
            if len(pred_fs)==len(actual_fs):
                X=pd.DataFrame(index=te_idx)
                for af,pf in zip(actual_fs,pred_fs): X[af]=pd.to_numeric(p.loc[te_idx,pf],errors="coerce")
                pre=np.maximum(0,m.predict(X[actual_fs])); p.loc[te_idx,"opportunity_xfp_pregame"]=pre
            q=p.loc[te_idx,["fantasy_points","fp_prior_4","opportunity_xfp_realized","opportunity_xfp_pregame"]].apply(pd.to_numeric,errors="coerce")
            q=q.dropna(subset=["fantasy_points","opportunity_xfp_pregame"])
            if len(q)<8: continue
            y=q.fantasy_points.to_numpy(float); xp=q.opportunity_xfp_pregame.to_numpy(float)
            mae=float(mean_absolute_error(y,xp)); rank,_=safe_corr(q.opportunity_xfp_pregame,q.fantasy_points)
            base=q.dropna(subset=["fp_prior_4"])
            bmae=float(mean_absolute_error(base.fantasy_points,base.fp_prior_4)) if len(base)>=8 else None
            val.append({"position":pos,"test_season":test_season,"n":int(len(q)),"pregame_xfp_mae":mae,"pregame_xfp_rmse":rmse(y,xp),"pregame_xfp_spearman":rank,"recent_fp_mae":bmae,"mae_improvement_vs_recent_fp":float((bmae-mae)/bmae) if bmae and bmae>0 else None,"opportunity_features":actual_fs})
    p["xfp_residual"]=pd.to_numeric(p.fantasy_points,errors="coerce")-pd.to_numeric(p.opportunity_xfp_realized,errors="coerce")
    return p,val


def regression_validation(df: pd.DataFrame) -> List[dict]:
    out=[]
    for pos in POSITIONS:
        z=df[df.position_model.eq(pos)].copy()
        z["future_change"]=pd.to_numeric(z.fp_next3,errors="coerce")-pd.to_numeric(z.fantasy_points,errors="coerce")
        z=z.dropna(subset=["xfp_residual","future_change"])
        if len(z)<30: continue
        corr,n=safe_corr(z.xfp_residual,z.future_change)
        # Within-season/position quantiles avoid era/position scale contamination.
        try: z["bucket"]=pd.qcut(z.xfp_residual,5,labels=False,duplicates="drop")
        except Exception: z["bucket"]=2
        lo=z[z.bucket==z.bucket.min()]; hi=z[z.bucket==z.bucket.max()]
        out.append({
            "position":pos,"n":int(len(z)),"residual_to_future_change_spearman":corr,
            "underperformer_next3_change":float(lo.future_change.mean()) if len(lo) else None,
            "overperformer_next3_change":float(hi.future_change.mean()) if len(hi) else None,
            "mean_reversion_spread":float(lo.future_change.mean()-hi.future_change.mean()) if len(lo) and len(hi) else None,
            "classification":"validated_regression_candidate" if corr is not None and corr < -0.08 else "diagnostic_only",
        })
    return out


CHANGE_METRICS={
    "QB":["snap_share","qb_rush_share"],
    "RB":["offense_snap_share","carry_share","target_share"],
    "WR":["offense_snap_share","target_share"],
    "TE":["offense_snap_share","target_share"],
    "EDGE":["defense_snap_share"],"IDL":["defense_snap_share"],"LB":["defense_snap_share"],"S":["defense_snap_share"],"CB":["defense_snap_share"],
}


def add_change_signals(df: pd.DataFrame) -> pd.DataFrame:
    d=df.sort_values(["canonical_player_id","season","week"]).copy(); g=d.groupby(["canonical_player_id","season"],group_keys=False)
    deltas=[]
    for pos,metrics in CHANGE_METRICS.items():
        for m in metrics:
            if m not in d: continue
            recent=g[m].transform(lambda s: pd.to_numeric(s,errors="coerce").rolling(3,min_periods=2).mean())
            base=g[m].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(3).rolling(5,min_periods=3).mean())
            col=f"change_{m}"; d[col]=recent-base; deltas.append((pos,col,m))
    d["opportunity_change_score"]=np.nan
    # Position-specific robust standardisation; use the largest positive constituent signal.
    for pos in POSITIONS:
        idx=d.position_model.eq(pos)
        cols=[c for p,c,_ in deltas if p==pos]
        if not cols: continue
        zs=[]
        for c in cols:
            x=pd.to_numeric(d.loc[idx,c],errors="coerce"); med=x.median(); mad=(x-med).abs().median()
            scale=float(mad*1.4826) if finite(mad) and mad>1e-6 else float(x.std()) if finite(x.std()) and x.std()>1e-6 else 1.0
            zs.append((x-med)/scale)
        d.loc[idx,"opportunity_change_score"]=pd.concat(zs,axis=1).max(axis=1)
    d["role_breakout_signal"]=(pd.to_numeric(d.opportunity_change_score,errors="coerce")>=1.25)
    return d


def change_validation(df: pd.DataFrame) -> List[dict]:
    out=[]
    for pos in POSITIONS:
        z=df[df.position_model.eq(pos)].copy()
        z["future_vs_prior"]=pd.to_numeric(z.fp_next3,errors="coerce")-pd.to_numeric(z.fp_prior_4,errors="coerce")
        z=z.dropna(subset=["opportunity_change_score","future_vs_prior"])
        if len(z)<30: continue
        sig=z[z.role_breakout_signal]; non=z[~z.role_breakout_signal]
        corr,_=safe_corr(z.opportunity_change_score,z.future_vs_prior)
        out.append({"position":pos,"n":int(len(z)),"signals":int(len(sig)),"signal_rate":float(len(sig)/len(z)),"change_to_future_uplift_spearman":corr,"signal_next3_uplift_vs_prior":float(sig.future_vs_prior.mean()) if len(sig) else None,"non_signal_next3_uplift_vs_prior":float(non.future_vs_prior.mean()) if len(non) else None,"signal_increment":float(sig.future_vs_prior.mean()-non.future_vs_prior.mean()) if len(sig) and len(non) else None,"threshold_z":1.25})
    return out


def competition_validation(df: pd.DataFrame, team_preds: pd.DataFrame) -> List[dict]:
    # Isolate the incremental value of competition by re-running share models without it.
    _, base = player_oos_components(df, team_preds, include_competition=False)
    _, plus = player_oos_components(df, team_preds, include_competition=True)
    key=lambda r:(r["position"],r["component"],r["test_season"])
    bm={key(r):r for r in base}; out=[]
    for r in plus:
        b=bm.get(key(r));
        if not b: continue
        out.append({"position":r["position"],"component":r["component"],"test_season":r["test_season"],"n_test":r["n_test"],"mae_without_competition":b["model_mae"],"mae_with_competition":r["model_mae"],"incremental_mae_improvement":float((b["model_mae"]-r["model_mae"])/b["model_mae"]) if b["model_mae"]>0 else None,"competition_features":[f for f in r["features"] if "competition" in f or "concentration" in f or "support" in f]})
    return out


def _previous_team_players(df: pd.DataFrame, share_col: str, role_positions: Sequence[str], threshold: float) -> pd.DataFrame:
    z=df[df.position_model.isin(role_positions)].copy()
    z=z.sort_values(["canonical_player_id","season","week"])
    # Prior share is already pregame information based on preceding games.
    z[share_col]=pd.to_numeric(z[share_col],errors="coerce")
    return z[z[share_col]>=threshold][["season","week","team","canonical_player_id",share_col,"position_model"]]


def vacated_opportunity(df: pd.DataFrame) -> Tuple[List[dict], List[dict]]:
    """Retrospective redistribution study.

    Absence is detected from historical participation/stat rows, not from a pregame
    injury feed. Therefore this output is explicitly NOT activation-eligible yet.
    """
    d=df.copy(); summaries=[]; episodes=[]
    specs=[
        ("receiving","target_share_prior4",["WR","TE","RB"],.08,"target_share"),
        ("backfield","carry_share_prior4",["RB"],.15,"carry_share"),
        ("tackle_role","defense_snap_share_prior4",["LB","S"],.55,"defense_snap_share"),
        ("pass_rush_role","defense_snap_share_prior4",["EDGE","IDL"],.55,"defense_snap_share"),
    ]
    team_weeks=d[["season","week","team"]].drop_duplicates()
    for kind,prior_col,positions,threshold,current_col in specs:
        z=d[d.position_model.isin(positions)].copy()
        if prior_col not in z or current_col not in z: continue
        # Candidate incumbent from previous game: use each player's prior4 share on the current team-week.
        # If no current row exists, create it from prior week's team affiliation.
        prev=z[["season","week","team","canonical_player_id",prior_col,"position_model"]].copy()
        prev["week"]=pd.to_numeric(prev.week,errors="coerce")+1
        prev=prev.rename(columns={prior_col:"vacated_prior_share","team":"prev_team"})
        current_keys=set(zip(z.season.astype(int),z.week.astype(int),z.team.astype(str),z.canonical_player_id.astype(str)))
        abs_rows=[]
        for r in prev.itertuples(index=False):
            if not finite(r.vacated_prior_share) or float(r.vacated_prior_share)<threshold: continue
            key=(int(r.season),int(r.week),str(r.prev_team),str(r.canonical_player_id))
            if key not in current_keys and ((team_weeks.season.astype(int)==int(r.season))&(team_weeks.week.astype(int)==int(r.week))&(team_weeks.team.astype(str)==str(r.prev_team))).any():
                abs_rows.append({"season":int(r.season),"week":int(r.week),"team":str(r.prev_team),"absent_player":str(r.canonical_player_id),"vacated_share":float(r.vacated_prior_share),"position":r.position_model})
        if not abs_rows: continue
        ab=pd.DataFrame(abs_rows)
        vac=ab.groupby(["season","week","team"],as_index=False).agg(vacated_share=("vacated_share","sum"),absent_players=("absent_player","nunique"))
        cur=z.merge(vac,on=["season","week","team"],how="inner")
        cur["share_gain"]=pd.to_numeric(cur[current_col],errors="coerce")-pd.to_numeric(cur[prior_col],errors="coerce")
        cur["capture_rate"]=np.where(cur.vacated_share>0,np.maximum(0,cur.share_gain)/cur.vacated_share,np.nan)
        for (season,week,team),q in cur.groupby(["season","week","team"]):
            top=q.sort_values("capture_rate",ascending=False).head(3)
            episodes.append({"kind":kind,"season":int(season),"week":int(week),"team":str(team),"vacated_share":float(q.vacated_share.iloc[0]),"absent_players":int(q.absent_players.iloc[0]),"top_captures":[{"player_id":str(r.canonical_player_id),"position":str(r.position_model),"capture_rate":float(r.capture_rate) if finite(r.capture_rate) else None,"share_gain":float(r.share_gain) if finite(r.share_gain) else None} for r in top.itertuples(index=False)]})
        q=cur.dropna(subset=["capture_rate"])
        summaries.append({"kind":kind,"episodes":int(vac.shape[0]),"player_episode_rows":int(len(q)),"mean_vacated_share":float(vac.vacated_share.mean()),"mean_capture_rate":float(q.capture_rate.mean()) if len(q) else None,"median_capture_rate":float(q.capture_rate.median()) if len(q) else None,"detection":"retrospective_row_absence","activation_eligible":False})
    return summaries,episodes[:250]


def aggregate_rows(rows: List[dict], keys: Sequence[str], metrics: Sequence[str]) -> List[dict]:
    if not rows: return []
    d=pd.DataFrame(rows); out=[]
    for vals,q in d.groupby(list(keys),dropna=False):
        if not isinstance(vals,tuple): vals=(vals,)
        r={k:(v.item() if hasattr(v,"item") else v) for k,v in zip(keys,vals)}
        r["folds"]=int(len(q))
        for m in metrics:
            if m in q: r[m]=float(pd.to_numeric(q[m],errors="coerce").mean()) if pd.to_numeric(q[m],errors="coerce").notna().any() else None
        out.append(r)
    return out


def write_m2_derived(df: pd.DataFrame, derived_dir: Optional[str]) -> dict:
    if not derived_dir: return {"written":False,"files":{}}
    p=Path(derived_dir); p.mkdir(parents=True,exist_ok=True)
    cols=[c for c in ["season","week","canonical_player_id","full_name","team","position_model","fantasy_points","fp_prior_4","fp_next3","opportunity_xfp_realized","opportunity_xfp_pregame","xfp_residual","opportunity_change_score","role_breakout_signal","receiving_competition_index","backfield_competition_index","tackle_competition_index","pass_rush_support_index","pred_targets","pred_carries","pred_pass_attempts","pred_defensive_opportunities"] if c in df.columns]
    path=p/"milestone2_player_week.csv.gz"; df[cols].to_csv(path,index=False,compression="gzip")
    return {"written":True,"files":{"milestone2_player_week":{"path":str(path),"rows":int(len(df)),"columns":int(len(cols))}}}


def run(args) -> dict:
    if args.fixture:
        player, team=fixture_tables(); scoring=dict(DEFAULT_PPR); scoring_sig=scoring_signature(scoring); m1_status="fixture"
    else:
        player,team=load_tables(Path(args.m1_derived_dir));
        m1=json.loads(Path(args.m1_bundle).read_text()) if Path(args.m1_bundle).exists() else {}
        scoring=m1.get("scoring",{}).get("settings",DEFAULT_PPR); scoring_sig=m1.get("scoring",{}).get("signature",scoring_signature(scoring)); m1_status=m1.get("status","unknown")
    player,team_ctx=add_team_context(player,team)
    player=add_competition_features(player)
    player=add_position_shares(player)

    team_pred,team_validation=team_oos_predictions(team_ctx)
    pred,component_validation=player_oos_components(player,team_pred,include_competition=True)
    count_validation=decomposition_count_validation(pred)
    pred,xfp_validation=build_xfp(pred,player)
    pred=add_change_signals(pred)
    regression=regression_validation(pred)
    change=change_validation(pred)
    competition=competition_validation(player,team_pred)
    vacated_summary,vacated_episodes=vacated_opportunity(player)
    manifest=write_m2_derived(pred,args.derived_dir)

    comp_agg=aggregate_rows(component_validation,["position","component"],["baseline_mae","model_mae","mae_improvement_vs_prior4","spearman"])
    count_agg=aggregate_rows(count_validation,["position","component"],["mae","rmse","spearman"])
    xfp_agg=aggregate_rows(xfp_validation,["position"],["pregame_xfp_mae","pregame_xfp_rmse","pregame_xfp_spearman","recent_fp_mae","mae_improvement_vs_recent_fp"])
    competition_agg=aggregate_rows(competition,["position","component"],["mae_without_competition","mae_with_competition","incremental_mae_improvement"])

    bundle={
        "schema_version":2,"milestone":MILESTONE,"control_build":CONTROL_BUILD,"research_build":RESEARCH_BUILD,
        "generated_at":utc_now(),"status":"complete","diagnostic_only":True,"m1_status":m1_status,"scoring_signature":scoring_sig,
        "steps_completed":[10,11,12,13,14,15],
        "methodology":{
            "time_safe_folds":["2019-2021 -> 2022","2019-2022 -> 2023","2019-2023 -> 2024","2019-2024 -> 2025"],
            "step10":"team volume and player share/participation are predicted separately, then recombined into position-specific opportunity counts",
            "step11":"opportunity xFP uses opportunity/participation only; realized efficiency outcomes such as receptions, yards, TDs, tackles, sacks and interceptions are excluded from xFP features",
            "step12":"actual minus realized-opportunity xFP is tested for subsequent mean reversion",
            "step13":"role changes compare current three-game opportunity with an older five-game baseline and validate subsequent three-game scoring",
            "step14":"competition indices are tested incrementally by comparing otherwise-identical share models with vs without teammate competition",
            "step15":"vacated opportunity is retrospective until a trustworthy pregame availability feed is joined; it cannot activate live projections yet",
            "route_guardrail":"no proxy is relabeled as true routes",
            "activation":"none in M2; all new signals remain diagnostic_only"
        },
        "decomposition":{"team_validation":team_validation,"component_validation":component_validation,"component_aggregate":comp_agg,"count_validation":count_validation,"count_aggregate":count_agg},
        "xfp":{"validation":xfp_validation,"aggregate":xfp_agg},
        "regression_validation":regression,
        "opportunity_change_validation":change,
        "competition_validation":{"folds":competition,"aggregate":competition_agg,"definitions":{
            "receiving_competition_index":"sum of other WR/TE/RB pregame target-share priors on the same team",
            "backfield_competition_index":"sum of other RB pregame carry-share priors on the same team",
            "tackle_competition_index":"sum of other LB/S pregame defensive-snap priors",
            "pass_rush_support_index":"sum of other EDGE/IDL pregame defensive-snap priors; sign is learned, not assumed"
        }},
        "vacated_opportunity":{"summary":vacated_summary,"episodes":vacated_episodes,"activation_eligible":False},
        "derived_tables":manifest,
        "limitations":[
            "M2 opportunity xFP is position-level expected scoring from opportunity, not yet a fully charted per-target/per-carry tracking model.",
            "True all-route participation remains unavailable in the public-core pipeline and is never inferred from snap share.",
            "Vacated opportunity is detected retrospectively from row absence in M2; current-week use requires a trustworthy pregame availability/injury layer.",
            "EDGE/IDL/DB opportunity counts remain public-core proxies until richer historical pass-rush/coverage participation is parsed in Step 16.",
            "No M2 output changes live Draft, Waiver, Weekly, Trade or Team scores."
        ]
    }
    return bundle


def parse_args(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--m1-derived-dir",default="data/research/derived")
    p.add_argument("--m1-bundle",default="data/research/milestone1.json")
    p.add_argument("--derived-dir",default="data/research/derived")
    p.add_argument("--output",default="data/research/milestone2.json")
    p.add_argument("--fixture",action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    args=parse_args(argv); b=run(args); out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(b,indent=2,allow_nan=False)); print(f"Wrote {out} status={b['status']} steps={b['steps_completed']}")


if __name__=="__main__": main()
