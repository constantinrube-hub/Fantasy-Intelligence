#!/usr/bin/env python3
"""Fantasy Intelligence Engine V8.5-M3 research pipeline.

Implements roadmap Steps 16-18 on top of Milestones 1-2:
16 position-specific advanced models,
17 retrospective natural-experiment / quasi-experiment analysis,
18 rookie and Y1/Y2 opportunity models.

All outputs remain diagnostic_only. Nothing here changes the frozen V8.2.2
Draft/Waiver/Weekly/Trade/Team scoring logic.
"""
from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    mean_absolute_error,
    mean_squared_error,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from fie_research import (
    CONTROL_BUILD,
    DEFAULT_PPR,
    POSITIONS,
    PRIMARY_SEASONS, LATEST_COMPLETED_SEASON,
    SourceManager,
    build_identity,
    first_col,
    make_fixture,
    normalize_position,
)
from fie_m2 import (
    FOLDS,
    add_change_signals,
    add_competition_features,
    add_position_shares,
    add_team_context,
    fixture_tables,
)
from statistical_guardrails import promotion_gate

RESEARCH_BUILD = "V8.5-M3"
MILESTONE = "M3"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite(v) -> bool:
    try:
        return math.isfinite(float(v))
    except Exception:
        return False


def rmse(y, p) -> float:
    return float(math.sqrt(mean_squared_error(y, p)))


def safe_corr(x: pd.Series, y: pd.Series) -> Tuple[Optional[float], int]:
    z = pd.DataFrame({"x": pd.to_numeric(x, errors="coerce"), "y": pd.to_numeric(y, errors="coerce")}).dropna()
    if len(z) < 8 or z.x.nunique() < 2 or z.y.nunique() < 2:
        return None, int(len(z))
    r = spearmanr(z.x, z.y).statistic
    return (None if not np.isfinite(r) else float(r)), int(len(z))


def ridge_model(alpha: float = 8.0) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=alpha)),
    ])


def read_csv_if(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size < 20:
        return pd.DataFrame()
    return pd.read_csv(path, low_memory=False)


def load_core(args) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict, dict]:
    """Load M1/M2 derived tables and identity, or deterministic fixture equivalents."""
    if args.fixture:
        player, team = fixture_tables()
        players, _, _, _ = make_fixture()
        identity, _ = build_identity(players, pd.DataFrame())
        # Synthetic draft/biographical priors exist only to exercise Step 18 in CI.
        identity = identity.copy().reset_index(drop=True)
        n = len(identity)
        identity["draft_year"] = [2018 + (i % 8) for i in range(n)]
        identity["draft_round"] = [1 + (i % 7) for i in range(n)]
        identity["draft_pick"] = [1 + ((i * 19) % 255) for i in range(n)]
        identity["birth_date"] = [f"{1994 + (i % 7)}-06-15" for i in range(n)]
        identity["height"] = [68 + (i % 10) for i in range(n)]
        identity["weight"] = [185 + (i % 12) * 8 for i in range(n)]
        m2 = {"status": "fixture", "scoring_signature": "fixture"}
        m1 = {"status": "fixture", "scoring": {"settings": DEFAULT_PPR}}
        return player, team, identity, m1, m2

    d = Path(args.derived_dir)
    player = read_csv_if(d / "player_week.csv.gz")
    team = read_csv_if(d / "team_week.csv.gz")
    identity = read_csv_if(d / "player_identity.csv.gz")
    if player.empty or team.empty or identity.empty:
        raise FileNotFoundError("M1 derived player_week/team_week/player_identity tables are required before M3.")
    m2pw = read_csv_if(d / "milestone2_player_week.csv.gz")
    if not m2pw.empty:
        keys = ["season", "week", "canonical_player_id"]
        extras = [c for c in m2pw.columns if c not in keys and c not in player.columns]
        overlap = [c for c in m2pw.columns if c not in keys and c in {
            "opportunity_xfp_realized","opportunity_xfp_pregame","xfp_residual",
            "opportunity_change_score","role_breakout_signal",
            "receiving_competition_index","backfield_competition_index",
            "tackle_competition_index","pass_rush_support_index",
        }]
        cols = keys + sorted(set(extras + overlap))
        player = player.merge(m2pw[cols], on=keys, how="left", suffixes=("", "_m2"))
        for c in overlap:
            mc = f"{c}_m2"
            if mc in player:
                player[c] = player[c].where(player[c].notna(), player[mc]) if c in player else player[mc]
                player.drop(columns=[mc], inplace=True)
    m1 = json.loads(Path(args.m1_bundle).read_text()) if Path(args.m1_bundle).exists() else {}
    m2 = json.loads(Path(args.m2_bundle).read_text()) if Path(args.m2_bundle).exists() else {}
    return player, team, identity, m1, m2


# --------------------------- Step 16 enrichment ---------------------------

def _merge_weekly_by_gsis(base: pd.DataFrame, src: pd.DataFrame, prefix: str, wanted: Sequence[str]) -> Tuple[pd.DataFrame, List[str]]:
    if src.empty:
        return base, []
    s = src.copy()
    idc = first_col(s, ["player_gsis_id", "gsis_id", "player_id"])
    if idc is None or "season" not in s.columns or "week" not in s.columns:
        return base, []
    s = s.rename(columns={idc: "canonical_player_id"})
    if "season_type" in s:
        s = s[s["season_type"].astype(str).str.upper().isin(["REG", "REGULAR", "REGULAR_SEASON"])]
    keep = [c for c in wanted if c in s.columns]
    if not keep:
        return base, []
    for c in keep:
        s[c] = pd.to_numeric(s[c], errors="coerce")
    s = s[["season", "week", "canonical_player_id"] + keep].copy()
    s["canonical_player_id"] = s["canonical_player_id"].astype(str)
    s = s.groupby(["season", "week", "canonical_player_id"], as_index=False)[keep].mean()
    rename = {c: f"{prefix}{c}" for c in keep}
    s = s.rename(columns=rename)
    return base.merge(s, on=["season", "week", "canonical_player_id"], how="left"), list(rename.values())


def _merge_weekly_by_pfr(base: pd.DataFrame, src: pd.DataFrame, identity: pd.DataFrame, prefix: str, wanted: Sequence[str]) -> Tuple[pd.DataFrame, List[str]]:
    if src.empty:
        return base, []
    s = src.copy()
    idc = first_col(s, ["pfr_player_id", "pfr_id", "player_id"])
    if idc is None or "season" not in s.columns or "week" not in s.columns:
        return base, []
    im = identity[[c for c in ["pfr_id", "canonical_player_id"] if c in identity.columns]].dropna()
    if "pfr_id" not in im.columns:
        return base, []
    im["pfr_id"] = im["pfr_id"].astype(str)
    s["_pfr"] = s[idc].astype(str)
    s = s.merge(im.drop_duplicates("pfr_id"), left_on="_pfr", right_on="pfr_id", how="left")
    if "season_type" in s:
        s = s[s["season_type"].astype(str).str.upper().isin(["REG", "REGULAR", "REGULAR_SEASON"])]
    keep = [c for c in wanted if c in s.columns]
    if not keep:
        return base, []
    for c in keep:
        s[c] = pd.to_numeric(s[c], errors="coerce")
    s = s.dropna(subset=["canonical_player_id"])
    s = s[["season", "week", "canonical_player_id"] + keep].groupby(["season", "week", "canonical_player_id"], as_index=False)[keep].mean()
    rename = {c: f"{prefix}{c}" for c in keep}
    s = s.rename(columns=rename)
    return base.merge(s, on=["season", "week", "canonical_player_id"], how="left"), list(rename.values())


def _ids_from_cell(v: object) -> List[str]:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return []
    # GSIS IDs are stable and avoid fragile delimiter assumptions.
    return re.findall(r"00-\d{7,10}", str(v))


def participation_weekly(part: pd.DataFrame) -> pd.DataFrame:
    """Aggregate public participation context without inventing individual routes/rushes.

    Offensive pass-play presence means on field for a team pass play, not route run.
    Defensive pressure presence means on field when the team generated pressure, not individual pressure.
    Uses vectorized list extraction/explode so a season can be reduced without Python-row loops.
    """
    if part.empty or "season" not in part or "week" not in part:
        return pd.DataFrame()
    offc = first_col(part, ["offense_players"])
    defc = first_col(part, ["defense_players"])
    if offc is None and defc is None:
        return pd.DataFrame()
    x = part.copy()
    if "season_type" in x:
        x = x[x.season_type.astype(str).str.upper().eq("REG")].copy()
    passc = first_col(x, ["pass_attempt", "qb_dropback"])
    if passc:
        is_pass = pd.to_numeric(x[passc], errors="coerce").fillna(0).gt(0)
    elif "play_type" in x:
        is_pass = x.play_type.astype(str).str.lower().eq("pass")
    else:
        is_pass = x.get("time_to_throw", pd.Series(np.nan, index=x.index)).notna()
    pressure = x.get("was_pressure", pd.Series(False, index=x.index)).fillna(False).astype(bool)
    man = x.get("defense_man_zone_type", pd.Series("", index=x.index)).astype(str).str.upper().str.contains("MAN")
    zone = x.get("defense_man_zone_type", pd.Series("", index=x.index)).astype(str).str.upper().str.contains("ZONE")
    meta = pd.DataFrame({
        "season":pd.to_numeric(x.season,errors="coerce"),"week":pd.to_numeric(x.week,errors="coerce"),
        "part_play":1,"part_pass_play":is_pass.astype(int),
        "part_pressure_context_plays":(is_pass & pressure).astype(int),
        "part_man_context_plays":(is_pass & man).astype(int),"part_zone_context_plays":(is_pass & zone).astype(int),
        "part_avg_defenders_in_box":pd.to_numeric(x.get("defenders_in_box",pd.Series(np.nan,index=x.index)),errors="coerce"),
        "part_avg_num_pass_rushers":pd.to_numeric(x.get("number_of_pass_rushers",pd.Series(np.nan,index=x.index)),errors="coerce"),
    },index=x.index)
    def side_frame(col: Optional[str], prefix: str) -> pd.DataFrame:
        if col is None:return pd.DataFrame()
        z=meta.copy()
        z["canonical_player_id"]=x[col].astype(str).str.findall(r"00-\d{7,10}")
        z=z.explode("canonical_player_id").dropna(subset=["canonical_player_id","season","week"])
        if z.empty:return pd.DataFrame()
        z["season"]=z.season.astype(int);z["week"]=z.week.astype(int)
        ag=z.groupby(["season","week","canonical_player_id"],as_index=False).agg(
            part_plays=("part_play","sum"),part_pass_plays=("part_pass_play","sum"),
            part_pressure_context_plays=("part_pressure_context_plays","sum"),part_man_context_plays=("part_man_context_plays","sum"),part_zone_context_plays=("part_zone_context_plays","sum"),
            part_avg_defenders_in_box=("part_avg_defenders_in_box","mean"),part_avg_num_pass_rushers=("part_avg_num_pass_rushers","mean"),
        )
        ag["part_pressure_context_rate"]=ag.part_pressure_context_plays/ag.part_pass_plays.replace(0,np.nan)
        ag["part_man_context_rate"]=ag.part_man_context_plays/ag.part_pass_plays.replace(0,np.nan)
        ag["part_zone_context_rate"]=ag.part_zone_context_plays/ag.part_pass_plays.replace(0,np.nan)
        return ag.rename(columns={c:prefix+c for c in ag.columns if c not in ["season","week","canonical_player_id"]})
    a=side_frame(offc,"off_");b=side_frame(defc,"def_")
    if a.empty:return b
    if b.empty:return a
    return a.merge(b,on=["season","week","canonical_player_id"],how="outer")


NGS_PASS = [
    "avg_time_to_throw","avg_intended_air_yards","aggressiveness",
    "completion_percentage_above_expectation","expected_completion_percentage","avg_air_yards_to_sticks",
]
NGS_REC = [
    "avg_separation","avg_cushion","percent_share_of_intended_air_yards",
    "avg_yac","avg_expected_yac","avg_yac_above_expectation","avg_air_distance",
]
NGS_RUSH = [
    "efficiency","percent_attempts_gte_eight_defenders","avg_time_to_los",
    "rush_yards_over_expected","rush_yards_over_expected_per_att","rush_pct_over_expected",
]
PFR_PASS = ["passing_drop_pct","passing_bad_throw_pct","times_sacked","times_blitzed","times_hurried","times_hit","times_pressured","times_pressured_pct"]
PFR_REC = ["receiving_drop","receiving_drop_pct"]
PFR_DEF = ["def_times_blitzed","def_times_hurried","def_times_hitqb"]


def add_fixture_advanced(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    rng = np.random.default_rng(165)
    d = df.copy()
    n = len(d)
    d["ngs_avg_time_to_throw"] = np.where(d.position_model.eq("QB"), 2.65 + rng.normal(0,.12,n), np.nan)
    d["ngs_completion_percentage_above_expectation"] = np.where(d.position_model.eq("QB"), rng.normal(1.5,3,n), np.nan)
    d["ngs_avg_intended_air_yards"] = np.where(d.position_model.eq("QB"), 7.8 + rng.normal(0,1,n), np.nan)
    d["ngs_avg_separation"] = np.where(d.position_model.isin(["WR","TE"]), 2.8 + rng.normal(0,.35,n), np.nan)
    d["ngs_percent_share_of_intended_air_yards"] = np.where(d.position_model.isin(["WR","TE"]), np.clip(pd.to_numeric(d.target_share,errors="coerce").fillna(0)*110+rng.normal(0,4,n),0,80), np.nan)
    d["ngs_avg_yac_above_expectation"] = np.where(d.position_model.isin(["WR","TE"]), rng.normal(.3,1,n), np.nan)
    d["ngs_rush_yards_over_expected_per_att"] = np.where(d.position_model.eq("RB"), rng.normal(.2,.65,n), np.nan)
    d["ngs_percent_attempts_gte_eight_defenders"] = np.where(d.position_model.eq("RB"), np.clip(25+rng.normal(0,8,n),0,100), np.nan)
    d["pfr_times_pressured_pct"] = np.where(d.position_model.eq("QB"), np.clip(25+rng.normal(0,5,n),0,60), np.nan)
    d["pfr_receiving_drop_pct"] = np.where(d.position_model.isin(["WR","TE"]), np.clip(7+rng.normal(0,3,n),0,30), np.nan)
    d["pfr_def_times_hurried"] = np.where(d.position_model.isin(["EDGE","IDL"]), np.maximum(0,rng.normal(2,1,n)), np.nan)
    d["pfr_def_times_hitqb"] = np.where(d.position_model.isin(["EDGE","IDL"]), np.maximum(0,rng.normal(1,.7,n)), np.nan)
    d["off_part_pass_plays"] = np.where(d.position_model.isin(["QB","RB","WR","TE"]), np.maximum(1, pd.to_numeric(d.get("team_pass_attempts",0),errors="coerce").fillna(30)*pd.to_numeric(d.get("offense_snap_share",0),errors="coerce").fillna(0)), np.nan)
    d["def_part_pass_plays"] = np.where(d.position_model.isin(["EDGE","IDL","LB","S","CB"]), np.maximum(1, pd.to_numeric(d.get("defensive_opponent_dropbacks",30),errors="coerce").fillna(30)*pd.to_numeric(d.get("defense_snap_share",0),errors="coerce").fillna(0)), np.nan)
    d["def_part_pressure_context_rate"] = np.where(d.position_model.isin(["EDGE","IDL","LB","S","CB"]), np.clip(.32+rng.normal(0,.05,n),0,1), np.nan)
    d["def_part_man_context_rate"] = np.where(d.position_model.isin(["EDGE","IDL","LB","S","CB"]), np.clip(.35+rng.normal(0,.08,n),0,1), np.nan)
    d["def_part_zone_context_rate"] = np.where(d.position_model.isin(["EDGE","IDL","LB","S","CB"]), 1-pd.to_numeric(d["def_part_man_context_rate"],errors="coerce"), np.nan)
    cols=[c for c in d.columns if c.startswith(("ngs_","pfr_","off_part_","def_part_"))]
    return d,{"fixture":True,"feature_columns":cols,"sources":{"ngs":"synthetic_fixture","pfr":"synthetic_fixture","participation":"synthetic_fixture"}}


def add_public_enrichment(df: pd.DataFrame, identity: pd.DataFrame, cache_dir: str, seasons: Sequence[int]) -> Tuple[pd.DataFrame, dict]:
    sm = SourceManager(Path(cache_dir))
    d = df.copy()
    feature_cols: List[str] = []
    source_rows: Dict[str,int] = {}
    # Global NGS files already contain season/week, so each source is merged once.
    for src, prefix, wanted in [
        ("ngs_passing","ngs_",NGS_PASS),("ngs_receiving","ngs_",NGS_REC),("ngs_rushing","ngs_",NGS_RUSH)
    ]:
        q=sm.load(src,required=False); source_rows[src]=int(len(q))
        if not q.empty: q=q[pd.to_numeric(q.get("season"),errors="coerce").isin(seasons)]
        d,newcols=_merge_weekly_by_gsis(d,q,prefix,wanted); feature_cols += [c for c in newcols if c not in feature_cols]
    # Seasonal PFR files must be concatenated before one merge; repeated yearly merges
    # would create duplicate _x/_y feature names on the all-season player table.
    for src,prefix,wanted in [
        ("pfr_adv_pass","pfr_",PFR_PASS),("pfr_adv_rec","pfr_",PFR_REC),("pfr_adv_def","pfr_",PFR_DEF)
    ]:
        frames=[]
        for season in seasons:
            q=sm.load(src,season,required=False); source_rows[src]=source_rows.get(src,0)+int(len(q))
            if not q.empty: frames.append(q)
        q=pd.concat(frames,ignore_index=True,sort=False) if frames else pd.DataFrame()
        d,newcols=_merge_weekly_by_pfr(d,q,identity,prefix,wanted); feature_cols += [c for c in newcols if c not in feature_cols]
    # Participation is also concatenated after season-level reduction and merged once.
    part_frames=[]
    for season in seasons:
        q=sm.load("participation",season,required=False); source_rows["participation"]=source_rows.get("participation",0)+int(len(q))
        if not q.empty:
            w=participation_weekly(q)
            if not w.empty: part_frames.append(w)
    if part_frames:
        pw=pd.concat(part_frames,ignore_index=True,sort=False)
        newcols=[c for c in pw.columns if c not in ["season","week","canonical_player_id"]]
        d=d.merge(pw,on=["season","week","canonical_player_id"],how="left")
        feature_cols += [c for c in newcols if c not in feature_cols]
    cov={c:float(pd.to_numeric(d[c],errors="coerce").notna().mean()) for c in feature_cols if c in d}
    return d,{"fixture":False,"feature_columns":feature_cols,"coverage":cov,"source_rows":source_rows,"source_health":[s.__dict__ for s in sm.status]}


def add_lagged_advanced(df: pd.DataFrame, cols: Sequence[str]) -> pd.DataFrame:
    d=df.sort_values(["canonical_player_id","season","week"]).copy()
    g=d.groupby(["canonical_player_id","season"],group_keys=False)
    for c in cols:
        if c not in d: continue
        x=pd.to_numeric(d[c],errors="coerce")
        d[c]=x
        d[f"{c}_prior4"]=g[c].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
        d[f"{c}_prior8"]=g[c].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(8,min_periods=3).mean())
    return d


CORE_SPECIAL = {
    "QB":["fp_prior_4","fp_prior_8","snap_share_prior4","qb_rush_share_prior4","inside_5_carry_share_prior4"],
    "RB":["fp_prior_4","fp_prior_8","offense_snap_share_prior4","carry_share_prior4","target_share_prior4","red_zone_carry_share_prior4","inside_5_carry_share_prior4"],
    "WR":["fp_prior_4","fp_prior_8","offense_snap_share_prior4","target_share_prior4","red_zone_target_share_prior4"],
    "TE":["fp_prior_4","fp_prior_8","offense_snap_share_prior4","target_share_prior4","red_zone_target_share_prior4"],
    "EDGE":["fp_prior_4","fp_prior_8","defense_snap_share_prior4","pass_rush_support_index"],
    "IDL":["fp_prior_4","fp_prior_8","defense_snap_share_prior4","pass_rush_support_index"],
    "LB":["fp_prior_4","fp_prior_8","defense_snap_share_prior4","tackle_competition_index"],
    "S":["fp_prior_4","fp_prior_8","defense_snap_share_prior4","tackle_competition_index"],
    "CB":["fp_prior_4","fp_prior_8","defense_snap_share_prior4"],
}
ADV_PREFIX = {
    "QB":["ngs_avg_time_to_throw","ngs_avg_intended_air_yards","ngs_aggressiveness","ngs_completion_percentage_above_expectation","ngs_avg_air_yards_to_sticks","pfr_passing_bad_throw_pct","pfr_times_pressured_pct","pfr_times_sacked"],
    "RB":["ngs_efficiency","ngs_percent_attempts_gte_eight_defenders","ngs_avg_time_to_los","ngs_rush_yards_over_expected_per_att","ngs_rush_pct_over_expected","off_part_pass_plays"],
    "WR":["ngs_avg_separation","ngs_avg_cushion","ngs_percent_share_of_intended_air_yards","ngs_avg_yac_above_expectation","ngs_avg_air_distance","pfr_receiving_drop_pct","off_part_pass_plays"],
    "TE":["ngs_avg_separation","ngs_avg_cushion","ngs_percent_share_of_intended_air_yards","ngs_avg_yac_above_expectation","pfr_receiving_drop_pct","off_part_pass_plays"],
    "EDGE":["pfr_def_times_hurried","pfr_def_times_hitqb","pfr_def_times_blitzed","def_part_pass_plays","def_part_pressure_context_rate","def_part_avg_num_pass_rushers"],
    "IDL":["pfr_def_times_hurried","pfr_def_times_hitqb","pfr_def_times_blitzed","def_part_pass_plays","def_part_pressure_context_rate","def_part_avg_num_pass_rushers"],
    "LB":["pfr_def_times_blitzed","pfr_def_times_hurried","def_part_pass_plays","def_part_pressure_context_rate","def_part_man_context_rate","def_part_zone_context_rate"],
    "S":["pfr_def_times_blitzed","def_part_pass_plays","def_part_man_context_rate","def_part_zone_context_rate","def_part_avg_defenders_in_box"],
    "CB":["def_part_pass_plays","def_part_man_context_rate","def_part_zone_context_rate","def_part_avg_defenders_in_box"],
}


def ensure_core_priors(df: pd.DataFrame) -> pd.DataFrame:
    d=df.sort_values(["canonical_player_id","season","week"]).copy()
    g=d.groupby(["canonical_player_id","season"],group_keys=False)
    for c in ["snap_share","offense_snap_share","defense_snap_share","qb_rush_share","carry_share","target_share","red_zone_carry_share","inside_5_carry_share","red_zone_target_share"]:
        if c in d and f"{c}_prior4" not in d:
            d[f"{c}_prior4"] = g[c].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
    if "fp_prior_4" not in d:
        d["fp_prior_4"]=g["fantasy_points"].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
    if "fp_prior_8" not in d:
        d["fp_prior_8"]=g["fantasy_points"].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(8,min_periods=3).mean())
    return d


def specialized_validation(df: pd.DataFrame, advanced_cols: Sequence[str]) -> Tuple[List[dict], List[dict]]:
    d=ensure_core_priors(df)
    d=add_lagged_advanced(d,advanced_cols)
    fold_rows=[]
    for train_seasons,test_season in FOLDS:
        for pos in POSITIONS:
            z=d[d.position_model.eq(pos)].copy()
            if z.empty: continue
            core=[c for c in CORE_SPECIAL.get(pos,[]) if c in z and pd.to_numeric(z[c],errors="coerce").notna().any()]
            adv=[]
            for raw in ADV_PREFIX.get(pos,[]):
                for suf in ["_prior4","_prior8"]:
                    c=raw+suf
                    if c in z and pd.to_numeric(z[c],errors="coerce").notna().any(): adv.append(c)
            # Public-core specialized fallbacks can still be tested if advanced source coverage is absent.
            if pos in ["EDGE","IDL"]:
                for c in ["def_sacks","def_qb_hits"]:
                    if c in z:
                        pc=f"{c}_prior4"
                        if pc not in z:
                            z[pc]=z.groupby(["canonical_player_id","season"])[c].transform(lambda s:pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
                        core.append(pc)
            if pos in ["LB","S","CB"]:
                for c in ["tackles_solo","def_pass_defended","def_interceptions"]:
                    if c in z:
                        pc=f"{c}_prior4"
                        if pc not in z:
                            z[pc]=z.groupby(["canonical_player_id","season"])[c].transform(lambda s:pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
                        core.append(pc)
            fs=list(dict.fromkeys(core+adv))
            tr=z[z.season.isin(train_seasons)].dropna(subset=["fantasy_points","fp_prior_4"]).copy()
            te=z[z.season.eq(test_season)].dropna(subset=["fantasy_points","fp_prior_4"]).copy()
            if len(tr)<40 or len(te)<10 or len(fs)<2: continue
            m=ridge_model(); m.fit(tr[fs],pd.to_numeric(tr.fantasy_points,errors="coerce"))
            p=m.predict(te[fs]); y=pd.to_numeric(te.fantasy_points,errors="coerce").to_numpy(float)
            recent=pd.to_numeric(te.fp_prior_4,errors="coerce").to_numpy(float)
            recent_mae=float(mean_absolute_error(y,recent)); model_mae=float(mean_absolute_error(y,p)); rank,_=safe_corr(pd.Series(p),pd.Series(y))
            m2mae=None
            if "opportunity_xfp_pregame" in te:
                q=pd.DataFrame({"y":y,"x":pd.to_numeric(te.opportunity_xfp_pregame,errors="coerce")}).dropna()
                if len(q)>=8: m2mae=float(mean_absolute_error(q.y,q.x))
            fold_rows.append({
                "position":pos,"train_start":min(train_seasons),"train_end":max(train_seasons),"test_season":test_season,
                "n_test":int(len(te)),"model_mae":model_mae,"model_rmse":rmse(y,p),"model_spearman":rank,
                "recent_fp_mae":recent_mae,"mae_improvement_vs_recent_fp":float((recent_mae-model_mae)/recent_mae) if recent_mae>0 else None,
                "m2_xfp_mae":m2mae,"mae_improvement_vs_m2_xfp":float((m2mae-model_mae)/m2mae) if m2mae and m2mae>0 else None,
                "features":fs,"advanced_features":adv,"advanced_feature_count":len(adv),
            })
    out=[]
    f=pd.DataFrame(fold_rows)
    if not f.empty:
        for pos,g in f.groupby("position"):
            inc=pd.to_numeric(g.mae_improvement_vs_m2_xfp,errors="coerce").dropna()
            rec=pd.to_numeric(g.mae_improvement_vs_recent_fp,errors="coerce").dropna()
            positive=int((inc>0).sum()) if len(inc) else 0
            mean_inc=float(inc.mean()) if len(inc) else None
            gate=promotion_gate(inc.tolist(),weights=g.loc[inc.index,"n_test"].tolist(),min_mean=.01,min_folds=4,require_positive_ci=True)
            out.append({"position":pos,"folds":int(len(g)),"n_test":int(g.n_test.sum()),
                        "mean_mae":float(np.average(g.model_mae,weights=g.n_test)),
                        "mean_improvement_vs_recent_fp":float(rec.mean()) if len(rec) else None,
                        "mean_improvement_vs_m2_xfp":mean_inc,"positive_folds_vs_m2":positive,
                        "bootstrap_ci95_low":gate["ci95_low"],"bootstrap_ci95_high":gate["ci95_high"],
                        "advanced_feature_count":int(max(g.advanced_feature_count)),
                        "status":"validated_candidate" if gate["robust"] else "diagnostic_only"})
    return fold_rows,out


# --------------------------- Step 17 natural experiments ---------------------------

def add_team_starting_qb(df: pd.DataFrame) -> pd.DataFrame:
    d=df.copy()
    q=d[d.position_model.eq("QB")].copy()
    att=pd.to_numeric(q.get("attempts",pd.Series(0,index=q.index)),errors="coerce").fillna(0)
    q=q.assign(_att=att).sort_values(["season","week","team","_att"],ascending=[True,True,True,False]).drop_duplicates(["season","week","team"])
    q=q[["season","week","team","canonical_player_id"]].rename(columns={"canonical_player_id":"team_starting_qb"})
    d=d.merge(q,on=["season","week","team"],how="left")
    d=d.sort_values(["team","season","week"])
    d["previous_team_qb"]=d.groupby(["team","season"])["team_starting_qb"].shift(1)
    d["qb_change_week"]=d.team_starting_qb.notna() & d.previous_team_qb.notna() & d.team_starting_qb.ne(d.previous_team_qb)
    return d


def _absence_exposure(df: pd.DataFrame, positions: Sequence[str], share: str, threshold: float, label: str) -> pd.Series:
    d=df.sort_values(["canonical_player_id","season","week"]).copy()
    g=d.groupby(["canonical_player_id","season"],group_keys=False)
    if f"{share}_prior4" not in d:
        d[f"{share}_prior4"]=g[share].transform(lambda s:pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
    prior=d[d.position_model.isin(positions) & (pd.to_numeric(d[f"{share}_prior4"],errors="coerce")>=threshold)][["season","week","team","canonical_player_id",f"{share}_prior4"]].copy()
    current=set(zip(d.season.astype(int),d.week.astype(int),d.team.astype(str),d.canonical_player_id.astype(str)))
    missing=[]
    for r in prior.itertuples(index=False):
        if (int(r.season),int(r.week),str(r.team),str(r.canonical_player_id)) not in current:
            missing.append((int(r.season),int(r.week),str(r.team),str(r.canonical_player_id)))
    events={(s,w,t) for s,w,t,_ in missing}
    return pd.Series([(int(r.season),int(r.week),str(r.team)) in events for r in d.itertuples()],index=d.index,name=label)


def experiment_summary(z: pd.DataFrame, event_col: str, outcome_col: str, baseline_col: str, name: str, positions: Sequence[str]) -> dict:
    q=z[z.position_model.isin(positions)].copy()
    q["delta"]=pd.to_numeric(q[outcome_col],errors="coerce")-pd.to_numeric(q[baseline_col],errors="coerce")
    q=q.dropna(subset=["delta",event_col])
    ev=q[q[event_col].astype(bool)]; ctrl=q[~q[event_col].astype(bool)]
    if len(ev)<8:
        return {"experiment":name,"positions":list(positions),"events":int(len(ev)),"controls":int(len(ctrl)),"status":"insufficient_sample"}
    effect=float(ev.delta.mean() - ctrl.delta.mean()) if len(ctrl) else float(ev.delta.mean())
    return {"experiment":name,"positions":list(positions),"events":int(len(ev)),"controls":int(len(ctrl)),
            "event_mean_change":float(ev.delta.mean()),"control_mean_change":float(ctrl.delta.mean()) if len(ctrl) else None,
            "matched_delta_effect":effect,"event_median_change":float(ev.delta.median()),
            "status":"quasi_experimental_signal" if abs(effect)>0.25 else "diagnostic_only",
            "causal_claim":False}


def natural_experiments(df: pd.DataFrame) -> Tuple[List[dict], dict]:
    d=ensure_core_priors(df)
    if "fp_next3" not in d:
        d=d.sort_values(["canonical_player_id","season","week"])
        g=d.groupby(["canonical_player_id","season"],group_keys=False)
        d["fp_next3"]=g.fantasy_points.transform(lambda s:pd.concat([s.shift(-i) for i in [1,2,3]],axis=1).mean(axis=1,skipna=False))
    d=add_team_starting_qb(d)
    # Retrospective teammate-absence exposure. This is natural-experiment research, not a live availability feed.
    d["major_receiver_absence"]= _absence_exposure(d,["WR","TE"],"target_share",.18,"major_receiver_absence")
    d["lead_back_absence"]= _absence_exposure(d,["RB"],"carry_share",.35,"lead_back_absence")
    d["lead_tackler_absence"]= _absence_exposure(d,["LB","S"],"defense_snap_share",.75,"lead_tackler_absence")
    if "opportunity_change_score" not in d:
        d=add_change_signals(d)
    d["sustained_role_jump"]=pd.to_numeric(d.opportunity_change_score,errors="coerce").ge(1.25)
    exps=[
        experiment_summary(d,"qb_change_week","target_share","target_share_prior4","QB change → target share",["WR","TE","RB"]),
        experiment_summary(d,"qb_change_week","fantasy_points","fp_prior_4","QB change → fantasy points",["WR","TE","RB"]),
        experiment_summary(d,"major_receiver_absence","target_share","target_share_prior4","Major receiver absence → teammate target share",["WR","TE","RB"]),
        experiment_summary(d,"lead_back_absence","carry_share","carry_share_prior4","Lead back absence → remaining RB carry share",["RB"]),
        experiment_summary(d,"lead_tackler_absence","fantasy_points","fp_prior_4","Lead LB/S absence → teammate IDP fantasy points",["LB","S"]),
        experiment_summary(d,"sustained_role_jump","fp_next3","fp_prior_4","Sustained role jump → next-3 fantasy scoring",POSITIONS),
    ]
    unsupported={
        "coordinator_change":{"status":"blocked_missing_historical_coordinator_feed","reason":"No time-stamped coordinator/coach source is currently part of the M1-M3 public pipeline; no coaching-change effect is fabricated."},
        "true_alignment_change":{"status":"partial_only","reason":"Public participation identifies players on field plus team-level coverage/personnel context, but does not provide all-player route/alignment tracking for the full window."},
    }
    return exps,unsupported


# --------------------------- Step 18 young-player model ---------------------------

def normalize_name(v: object) -> str:
    return re.sub(r"[^a-z0-9]","",str(v or "").lower())


def load_combine(identity: pd.DataFrame, sm: Optional[SourceManager], fixture: bool) -> pd.DataFrame:
    if fixture:
        z=identity[["canonical_player_id","pfr_id"]].copy()
        n=len(z); rng=np.random.default_rng(181)
        z["combine_forty"]=4.4+rng.normal(0,.18,n); z["combine_vertical"]=34+rng.normal(0,4,n)
        z["combine_broad_jump"]=120+rng.normal(0,8,n); z["combine_cone"]=7+rng.normal(0,.25,n); z["combine_shuttle"]=4.3+rng.normal(0,.18,n)
        return z
    c=sm.load("combine",required=False) if sm else pd.DataFrame()
    if c.empty:return pd.DataFrame(columns=["canonical_player_id"])
    im=identity[[c for c in ["canonical_player_id","pfr_id","full_name"] if c in identity]].copy()
    c=c.copy(); pid=first_col(c,["pfr_id","pfr_player_id"])
    if pid and "pfr_id" in im:
        c["_pfr"]=c[pid].astype(str); im["_pfr"]=im.pfr_id.astype(str); c=c.merge(im[["_pfr","canonical_player_id"]].drop_duplicates("_pfr"),on="_pfr",how="left")
    else:
        nc=first_col(c,["player_name","name"]); c["_name"]=c[nc].map(normalize_name) if nc else ""; im["_name"]=im.full_name.map(normalize_name); c=c.merge(im[["_name","canonical_player_id"]].drop_duplicates("_name"),on="_name",how="left")
    fields={"forty":"combine_forty","vertical":"combine_vertical","broad_jump":"combine_broad_jump","cone":"combine_cone","shuttle":"combine_shuttle","wt":"combine_weight"}
    keep=[k for k in fields if k in c]
    for k in keep:c[k]=pd.to_numeric(c[k],errors="coerce")
    z=c.dropna(subset=["canonical_player_id"])[["canonical_player_id"]+keep].groupby("canonical_player_id",as_index=False)[keep].mean().rename(columns={k:fields[k] for k in keep})
    return z


def young_player_seasons(df: pd.DataFrame, identity: pd.DataFrame, combine: pd.DataFrame) -> pd.DataFrame:
    d=df.copy(); ident=identity.copy()
    # nflverse players generally exposes draft_year/round/pick; support draft_ovr as alternate overall pick.
    dy=first_col(ident,["draft_year"]); dr=first_col(ident,["draft_round"]); dp=first_col(ident,["draft_pick","draft_ovr"])
    if dy is None: ident["draft_year"]=np.nan;dy="draft_year"
    if dr is None: ident["draft_round"]=np.nan;dr="draft_round"
    if dp is None: ident["draft_pick"]=np.nan;dp="draft_pick"
    keep=["canonical_player_id",dy,dr,dp]+[c for c in ["birth_date","height","weight","position"] if c in ident]
    ident=ident[keep].copy().rename(columns={dy:"draft_year",dr:"draft_round",dp:"draft_pick"})
    for c in ["draft_year","draft_round","draft_pick","height","weight"]:
        if c in ident: ident[c]=pd.to_numeric(ident[c],errors="coerce")
    if not combine.empty: ident=ident.merge(combine,on="canonical_player_id",how="left")

    # M3 may receive an M1/M2-enriched player-week table that already contains
    # identity metadata (and, on older bundles, previously suffixed columns such
    # as ``position_identity``).  Re-merging every identity column with pandas'
    # suffix machinery can therefore create a duplicate output name.  Add only
    # metadata that is genuinely absent from the player-week table.  This keeps
    # the merge idempotent across milestones and is compatible with pandas 2.x.
    identity_cols = [c for c in ident.columns if c == "canonical_player_id" or c not in d.columns]
    if len(identity_cols) > 1:
        d=d.merge(ident[identity_cols],on="canonical_player_id",how="left")

    d["experience_year"]=pd.to_numeric(d.season,errors="coerce")-pd.to_numeric(d.draft_year,errors="coerce")+1
    d=d[d.experience_year.isin([1,2])].copy()
    if d.empty:return pd.DataFrame()
    d["birth_date_parsed"]=pd.to_datetime(d.get("birth_date"),errors="coerce")
    d["age_sept1"]=d.apply(lambda r: ((pd.Timestamp(year=int(r.season),month=9,day=1)-r.birth_date_parsed).days/365.25) if pd.notna(r.birth_date_parsed) else np.nan,axis=1)
    # Season outcomes and first-three-week in-season evidence.
    rows=[]
    for (season,pid),g in d.groupby(["season","canonical_player_id"]):
        g=g.sort_values("week"); pos=str(g.position_model.mode().iloc[0]) if len(g.position_model.mode()) else str(g.position_model.iloc[0])
        late=g[g.week>=5]; first3=g[g.week<=3]
        off=float(pd.to_numeric(late.get("offense_snap_share"),errors="coerce").mean()) if "offense_snap_share" in late else np.nan
        deff=float(pd.to_numeric(late.get("defense_snap_share"),errors="coerce").mean()) if "defense_snap_share" in late else np.nan
        targ=float(pd.to_numeric(late.get("target_share"),errors="coerce").mean()) if "target_share" in late else np.nan
        carr=float(pd.to_numeric(late.get("carry_share"),errors="coerce").mean()) if "carry_share" in late else np.nan
        if pos=="QB": meaningful=finite(off) and off>=.60; high=finite(off) and off>=.85
        elif pos=="RB": meaningful=(finite(off) and off>=.40) or (finite(carr) and carr>=.25) or (finite(targ) and targ>=.10); high=(finite(carr) and carr>=.40) or (finite(targ) and targ>=.15)
        elif pos in ["WR","TE"]: meaningful=(finite(off) and off>=.60) or (finite(targ) and targ>=.12); high=(finite(off) and off>=.75) and (finite(targ) and targ>=.18)
        else: meaningful=finite(deff) and deff>=.60; high=finite(deff) and deff>=.80
        base=g.iloc[0]
        row={"season":int(season),"canonical_player_id":pid,"position_model":pos,"experience_year":int(base.experience_year),
             "meaningful_role":int(bool(meaningful)),"high_value_role":int(bool(high)),
             "draft_year":base.get("draft_year"),"draft_round":base.get("draft_round"),"draft_pick":base.get("draft_pick"),"age_sept1":base.get("age_sept1"),
             "height":base.get("height"),"weight":base.get("weight")}
        for c in ["combine_forty","combine_vertical","combine_broad_jump","combine_cone","combine_shuttle","combine_weight"]: row[c]=base.get(c)
        for c in ["offense_snap_share","defense_snap_share","target_share","carry_share","fantasy_points"]:
            row[f"first3_{c}"]=float(pd.to_numeric(first3.get(c),errors="coerce").mean()) if c in first3 and len(first3) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def young_model(features_num: Sequence[str], include_position=True) -> Pipeline:
    cats=["position_model"] if include_position else []
    pre=ColumnTransformer([
        ("num",Pipeline([("imp",SimpleImputer(strategy="median")),("scale",StandardScaler())]),list(features_num)),
        ("cat",Pipeline([("imp",SimpleImputer(strategy="most_frequent")),("oh",OneHotEncoder(handle_unknown="ignore"))]),cats),
    ])
    return Pipeline([("pre",pre),("logit",LogisticRegression(max_iter=1000,C=.8,class_weight="balanced"))])


def young_validation(ys: pd.DataFrame) -> Tuple[List[dict], List[dict], dict]:
    if ys.empty:return [],[],{"rows":0}
    pre=[c for c in ["draft_round","draft_pick","age_sept1","height","weight","combine_forty","combine_vertical","combine_broad_jump","combine_cone","combine_shuttle"] if c in ys]
    inseason=pre+[c for c in ["first3_offense_snap_share","first3_defense_snap_share","first3_target_share","first3_carry_share","first3_fantasy_points"] if c in ys]
    folds=[]
    for variant,fs in [("preseason",pre),("after_week3",inseason)]:
        for train_seasons,test_season in FOLDS:
            tr=ys[ys.season.isin(train_seasons)].copy(); te=ys[ys.season.eq(test_season)].copy()
            if len(tr)<20 or len(te)<4 or tr.meaningful_role.nunique()<2:continue
            m=young_model(fs);m.fit(tr[fs+["position_model"]],tr.meaningful_role)
            prob=m.predict_proba(te[fs+["position_model"]])[:,1]; y=te.meaningful_role.to_numpy(int)
            auc=float(roc_auc_score(y,prob)) if len(np.unique(y))>1 else None
            brier=float(brier_score_loss(y,prob)); pred=(prob>=.5).astype(int)
            folds.append({"variant":variant,"test_season":test_season,"train_start":min(train_seasons),"train_end":max(train_seasons),"n_test":int(len(te)),"positive_rate":float(y.mean()),"brier":brier,"auc":auc,"accuracy":float(accuracy_score(y,pred)),"features":fs})
    agg=[]
    f=pd.DataFrame(folds)
    if not f.empty:
        for variant,g in f.groupby("variant"):
            aucs=pd.to_numeric(g.auc,errors="coerce").dropna(); advantage=(aucs-.50)
            gate=promotion_gate(advantage.tolist(),weights=g.loc[aucs.index,"n_test"].tolist(),min_mean=.10,min_folds=3,require_positive_ci=True)
            agg.append({"variant":variant,"folds":int(len(g)),"n_test":int(g.n_test.sum()),"mean_brier":float(g.brier.mean()),"mean_auc":float(aucs.mean()) if len(aucs) else None,"mean_accuracy":float(g.accuracy.mean()),"auc_advantage_ci95_low":gate["ci95_low"],"auc_advantage_ci95_high":gate["ci95_high"],"status":"validated_candidate" if gate["robust"] else "diagnostic_only"})
    pos=[]
    for p,g in ys.groupby("position_model"):
        pos.append({"position":p,"player_seasons":int(len(g)),"meaningful_role_rate":float(g.meaningful_role.mean()),"high_value_role_rate":float(g.high_value_role.mean()),"rookie_rows":int((g.experience_year==1).sum()),"y2_rows":int((g.experience_year==2).sum())})
    cov={"rows":int(len(ys)),"players":int(ys.canonical_player_id.nunique()),"seasons":[int(ys.season.min()),int(ys.season.max())],"draft_pick_coverage":float(pd.to_numeric(ys.draft_pick,errors="coerce").notna().mean()),"combine_any_coverage":float(ys[[c for c in ys if c.startswith("combine_")]].notna().any(axis=1).mean()) if any(c.startswith("combine_") for c in ys) else 0.0}
    return folds,agg,{"coverage":cov,"position_rates":pos,"definitions":{
        "experience_year":"Y1 when season equals draft year, Y2 the following season",
        "meaningful_role":"position-specific late-season role threshold: QB >=60% offense snaps; RB >=40% offense snaps or >=25% carry share or >=10% target share; WR/TE >=60% offense snaps or >=12% target share; IDP >=60% defense snaps",
        "high_value_role":"stricter position-specific late-season threshold used as a descriptive secondary outcome",
        "preseason_model":"draft capital, age and combine/size only",
        "after_week3_model":"preseason priors plus Weeks 1-3 NFL opportunity/production evidence",
    }}


def write_derived(df: pd.DataFrame, young: pd.DataFrame, derived_dir: Optional[str]) -> dict:
    if not derived_dir:return {"written":False,"files":{}}
    p=Path(derived_dir);p.mkdir(parents=True,exist_ok=True);files={}
    keep=[c for c in ["season","week","canonical_player_id","full_name","team","position_model","fantasy_points","opportunity_xfp_pregame","opportunity_change_score"] if c in df]
    adv=[c for c in df if (c.startswith("ngs_") or c.startswith("pfr_") or c.startswith("off_part_") or c.startswith("def_part_")) and not c.endswith(("_prior4","_prior8"))]
    path=p/"milestone3_player_week.csv.gz";df[keep+adv].to_csv(path,index=False,compression="gzip");files["milestone3_player_week"]={"path":str(path),"rows":int(len(df)),"columns":int(len(keep+adv))}
    yp=p/"milestone3_young_player_season.csv.gz";young.to_csv(yp,index=False,compression="gzip");files["milestone3_young_player_season"]={"path":str(yp),"rows":int(len(young)),"columns":int(len(young.columns))}
    return {"written":True,"files":files}


def run(args) -> dict:
    player,team,identity,m1,m2=load_core(args)
    player,team=add_team_context(player,team)
    player=add_competition_features(player)
    player=add_position_shares(player)
    if "opportunity_change_score" not in player:player=add_change_signals(player)

    if args.fixture:
        enriched,enrichment=add_fixture_advanced(player)
        sm=None
    else:
        enriched,enrichment=add_public_enrichment(player,identity,args.cache_dir,args.seasons)
        sm=SourceManager(Path(args.cache_dir))
    fold_special,agg_special=specialized_validation(enriched,enrichment.get("feature_columns",[]))
    experiments,unsupported=natural_experiments(enriched)
    combine=load_combine(identity,sm,args.fixture)
    young=young_player_seasons(enriched,identity,combine)
    young_folds,young_agg,young_meta=young_validation(young)
    manifest=write_derived(enriched,young,args.derived_dir)

    bundle={
        "schema_version":3,"milestone":MILESTONE,"control_build":CONTROL_BUILD,"research_build":RESEARCH_BUILD,
        "generated_at":utc_now(),"status":"complete","diagnostic_only":True,"m1_status":m1.get("status","unknown"),"m2_status":m2.get("status","unknown"),
        "scoring_signature":m2.get("scoring_signature") or m1.get("scoring",{}).get("signature"),"steps_completed":[16,17,18],
        "methodology":{
            "time_safe_folds":["2019-2021 -> 2022","2019-2022 -> 2023","2019-2023 -> 2024","2019-2024 -> 2025"],
            "step16":"position-specific models add lagged NGS/PFR/participation context where public coverage exists and are compared against recent-FP and M2 opportunity-xFP baselines",
            "step17":"natural experiments use retrospective within-player/team changes (QB changes, major teammate absences, role jumps); effect estimates are explicitly quasi-experimental and never labeled causal",
            "step18":"Y1/Y2 models predict whether a player earns a meaningful late-season role from preseason priors, then compare with an after-Week-3 update",
            "route_guardrail":"participation offense pass-play presence is not true route participation; participation pressure context is not individual pass-rush participation",
            "activation":"none in M3; validated_candidate means eligible for later integration review, not active in live scoring",
        },
        "position_specific":{"enrichment":enrichment,"folds":fold_special,"aggregate":agg_special},
        "natural_experiments":{"results":experiments,"unsupported":unsupported,"causal_claim":False},
        "young_player_model":{"folds":young_folds,"aggregate":young_agg,**young_meta},
        "derived_tables":manifest,
        "limitations":[
            "Public participation data identifies all players on field and team-level pressure/coverage context, but its route field is for the primary receiver; M3 never converts pass-play presence into true routes.",
            "Being on defense during a pressure is not evidence that the individual generated the pressure; M3 labels this pressure context and uses PFR individual hurry/hit fields when available.",
            "NGS receiver separation is observed on targets, so it is treated as lagged conversion/target-quality context rather than proof that separation caused future targets.",
            "Natural experiments are retrospective matched deltas, not randomized causal estimates. Coordinator-change effects remain blocked until a reliable time-stamped coaching source is added.",
            "The Y1/Y2 model currently lacks historical college production and a guaranteed time-safe preseason depth-chart feature; those remain later enrichment opportunities.",
            "No M3 output changes live Draft, Waiver, Weekly, Trade or Team scores.",
        ],
    }
    return bundle


def parse_args(argv=None):
    p=argparse.ArgumentParser(description="Build FIE V8.5-M3 research bundle")
    p.add_argument("--derived-dir",default="data/research/derived")
    p.add_argument("--m1-bundle",default="data/research/milestone1.json")
    p.add_argument("--m2-bundle",default="data/research/milestone2.json")
    p.add_argument("--cache-dir",default=".cache/fie-research")
    p.add_argument("--output",default="data/research/milestone3.json")
    p.add_argument("--seasons",default=f"2019-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--fixture",action="store_true")
    a=p.parse_args(argv)
    if isinstance(a.seasons,str):
        lo,hi=map(int,a.seasons.split("-"));a.seasons=list(range(lo,hi+1))
    return a


def main(argv=None):
    args=parse_args(argv);b=run(args);out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(b,indent=2,allow_nan=False));print(f"Wrote {out} status={b['status']} steps={b['steps_completed']}")


if __name__=="__main__":main()
