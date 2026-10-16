#!/usr/bin/env python3
"""Fantasy Intelligence Engine V8.3-M1 historical research pipeline.

Milestone 1 implements Steps 0-9 from the approved roadmap:
0 freeze/control metadata, 1 historical source/cache pipeline, 2 canonical identity,
3 league-replay fantasy scoring, 4 team opportunity, 5 pure opportunity metrics,
6 opportunity/outcome classification, 7 stability, 8 forward predictiveness,
9 expanding-window time-series validation.

The generated bundle is diagnostic only. It never changes live app rankings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import requests
from scipy.stats import spearmanr, pearsonr
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

CONTROL_BUILD = "V8.2.2"
RESEARCH_BUILD = "V8.3-M1"

def latest_completed_season(now_utc: Optional[datetime] = None) -> int:
    """Conservative rollover-safe end of the historical training window.

    January can still contain the final regular-season games, so the just-ended
    season is not admitted until February. CLI --seasons remains an explicit
    override for operators who have verified completeness earlier.
    """
    d = now_utc or datetime.now(timezone.utc)
    return d.year - (2 if d.month == 1 else 1)

LATEST_COMPLETED_SEASON = latest_completed_season()
PRIMARY_SEASONS = list(range(2019, LATEST_COMPLETED_SEASON + 1))
EXTENDED_SEASONS = list(range(2016, LATEST_COMPLETED_SEASON + 1))
POSITIONS = ["QB", "RB", "WR", "TE", "EDGE", "IDL", "LB", "S", "CB"]

DEFAULT_PPR = {
    "rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0,
    "rush_yd": 0.1, "rush_td": 6.0,
    "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -2.0,
    "fum_lost": -2.0,
    "tkl_solo": 1.5, "tkl_ast": 0.75, "tkl_loss": 1.0,
    "sack": 3.0, "qb_hit": 0.0, "int": 3.0,
    "pass_def": 1.5, "ff": 2.0, "fum_rec": 2.0, "def_td": 6.0,
}

SOURCE_TEMPLATES = {
    # Core Milestone 1 inputs.
    "players": "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv",
    "ff_playerids": "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv",
    "player_week": "https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{season}.csv",
    "team_week": "https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_week_{season}.csv",
    "snaps": "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv",
    "schedules": "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv",

    # Optional Step 1 archive. These are cached for reproducibility and later milestones,
    # but are not silently promoted into the Step 4-9 live feature set.
    "pbp": "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv",
    "participation": "https://github.com/nflverse/nflverse-data/releases/download/pbp_participation/pbp_participation_{season}.csv",
    "ngs_passing": "https://github.com/nflverse/nflverse-data/releases/download/nextgen_stats/ngs_passing.csv",
    "ngs_receiving": "https://github.com/nflverse/nflverse-data/releases/download/nextgen_stats/ngs_receiving.csv",
    "ngs_rushing": "https://github.com/nflverse/nflverse-data/releases/download/nextgen_stats/ngs_rushing.csv",
    "pfr_adv_pass": "https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_pass_{season}.csv",
    "pfr_adv_rush": "https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_rush_{season}.csv",
    "pfr_adv_rec": "https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_rec_{season}.csv",
    "pfr_adv_def": "https://github.com/nflverse/nflverse-data/releases/download/pfr_advstats/advstats_week_def_{season}.csv",
    "rosters": "https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{season}.csv",
    "weekly_rosters": "https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{season}.csv",
    "depth_charts": "https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_{season}.rds",
    "injuries": "https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv",
    "ftn_charting": "https://github.com/nflverse/nflverse-data/releases/download/ftn_charting/ftn_charting_{season}.csv",
    "contracts": "https://github.com/nflverse/nflverse-data/releases/download/contracts/historical_contracts.csv",
    "draft_picks": "https://github.com/nflverse/nflverse-data/releases/download/draft_picks/draft_picks.csv",
    "combine": "https://github.com/nflverse/nflverse-data/releases/download/combine/combine.csv",
}

METRIC_CLASS = {
    "team_plays": "team_opportunity",
    "team_pass_attempts": "team_opportunity",
    "team_rush_attempts": "team_opportunity",
    "team_red_zone_plays": "team_opportunity",
    "team_goal_line_plays": "team_opportunity",
    "defensive_opponent_plays": "team_opportunity",
    "defensive_opponent_dropbacks": "team_opportunity",
    "defensive_opponent_rush_attempts": "team_opportunity",
    "pass_rush_opportunity_proxy": "participation_proxy",
    "tackle_opportunity_proxy": "participation_proxy",
    "coverage_opportunity_proxy": "participation_proxy",
    "snap_share": "participation",
    "offense_snap_share": "participation",
    "defense_snap_share": "participation",
    "pass_play_participation_proxy": "participation_proxy",
    "true_route_participation": "participation_true_route",
    "target_share": "opportunity",
    "carry_share": "opportunity",
    "targets_per_pass_attempt": "opportunity",
    "carries_per_rush_attempt": "opportunity",
    "qb_rush_share": "opportunity",
    "red_zone_carry_share": "opportunity_quality",
    "inside_10_carry_share": "opportunity_quality",
    "inside_5_carry_share": "opportunity_quality",
    "red_zone_target_share": "opportunity_quality",
    "end_zone_target_share_proxy": "opportunity_quality_proxy",
    "receptions": "outcome",
    "receiving_yards": "outcome",
    "receiving_tds": "outcome",
    "rushing_yards": "outcome",
    "rushing_tds": "outcome",
    "passing_yards": "outcome",
    "passing_tds": "outcome",
    "sacks": "outcome",
    "interceptions_def": "outcome",
    "tackles_solo": "outcome",
    "fantasy_points": "outcome",
}

# Public-core opportunity metrics that can be derived without pretending route data exists.
POSITION_METRICS = {
    "QB": ["team_plays", "team_pass_attempts", "team_rush_attempts", "team_red_zone_plays", "team_goal_line_plays", "snap_share", "qb_rush_share", "red_zone_carry_share", "inside_5_carry_share"],
    "RB": ["team_plays", "team_rush_attempts", "team_pass_attempts", "team_red_zone_plays", "team_goal_line_plays", "snap_share", "carry_share", "target_share", "carries_per_rush_attempt", "targets_per_pass_attempt", "red_zone_carry_share", "inside_10_carry_share", "inside_5_carry_share", "red_zone_target_share"],
    "WR": ["team_plays", "team_pass_attempts", "team_red_zone_plays", "snap_share", "target_share", "targets_per_pass_attempt", "pass_play_participation_proxy", "red_zone_target_share", "end_zone_target_share_proxy"],
    "TE": ["team_plays", "team_pass_attempts", "team_red_zone_plays", "snap_share", "target_share", "targets_per_pass_attempt", "pass_play_participation_proxy", "red_zone_target_share", "end_zone_target_share_proxy"],
    "EDGE": ["defensive_opponent_plays", "defensive_opponent_dropbacks", "defense_snap_share", "snap_share", "pass_rush_opportunity_proxy"],
    "IDL": ["defensive_opponent_plays", "defensive_opponent_dropbacks", "defense_snap_share", "snap_share", "pass_rush_opportunity_proxy"],
    "LB": ["defensive_opponent_plays", "defensive_opponent_rush_attempts", "defense_snap_share", "snap_share", "tackle_opportunity_proxy"],
    "S": ["defensive_opponent_plays", "defensive_opponent_dropbacks", "defense_snap_share", "snap_share", "coverage_opportunity_proxy", "tackle_opportunity_proxy"],
    "CB": ["defensive_opponent_plays", "defensive_opponent_dropbacks", "defense_snap_share", "snap_share", "coverage_opportunity_proxy"],
}

ID_COL_CANDIDATES = ["gsis_id", "player_id", "nflverse_id"]
TEAM_COL_CANDIDATES = ["recent_team", "team", "posteam"]
POS_COL_CANDIDATES = ["position", "position_group"]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def finite(v) -> bool:
    try:
        return math.isfinite(float(v))
    except Exception:
        return False


def first_col(df: pd.DataFrame, names: Sequence[str]) -> Optional[str]:
    for n in names:
        if n in df.columns:
            return n
    return None


def num_series(df: pd.DataFrame, names: Sequence[str], default=0.0) -> pd.Series:
    c = first_col(df, names)
    if c is None:
        return pd.Series(default, index=df.index, dtype="float64")
    return pd.to_numeric(df[c], errors="coerce").fillna(default)


def normalize_position(pos: object, player_name: str = "") -> str:
    p = str(pos or "").upper().strip()
    if p in {"QB", "RB", "WR", "TE", "LB"}: return p
    if p in {"EDGE", "ED", "OLB", "DE"}: return "EDGE"
    if p in {"DT", "NT", "DI", "IDL", "DL"}: return "IDL"
    if p in {"S", "FS", "SS"}: return "S"
    if p in {"CB", "DB"}: return "CB"
    return p or "UNK"


def safe_corr(x: pd.Series, y: pd.Series, kind="spearman") -> Tuple[Optional[float], int]:
    z = pd.DataFrame({"x": pd.to_numeric(pd.Series(x).reset_index(drop=True), errors="coerce"), "y": pd.to_numeric(pd.Series(y).reset_index(drop=True), errors="coerce")}).dropna()
    if len(z) < 8 or z.x.nunique() < 2 or z.y.nunique() < 2:
        return None, len(z)
    try:
        r = spearmanr(z.x, z.y).statistic if kind == "spearman" else pearsonr(z.x, z.y).statistic
        return (None if not np.isfinite(r) else float(r)), len(z)
    except Exception:
        return None, len(z)


def rmse(y_true, y_pred) -> float:
    return float(math.sqrt(mean_squared_error(y_true, y_pred)))


def scoring_signature(scoring: dict) -> str:
    raw = json.dumps(scoring, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass
class SourceStatus:
    source: str
    season: Optional[int]
    path: str
    url: str
    ok: bool
    rows: Optional[int] = None
    error: Optional[str] = None


class SourceManager:
    def __init__(self, cache_dir: Path, timeout: int = 90):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.status: List[SourceStatus] = []

    def path_for(self, source: str, season: Optional[int] = None) -> Path:
        suffix = f"_{season}" if season is not None else ""
        url = self.url_for(source, season)
        ext = Path(url.split("?", 1)[0]).suffix or ".bin"
        return self.cache_dir / f"{source}{suffix}{ext}"

    def url_for(self, source: str, season: Optional[int] = None) -> str:
        tmpl = SOURCE_TEMPLATES[source]
        return tmpl.format(season=season) if "{season}" in tmpl else tmpl

    def ensure(self, source: str, season: Optional[int] = None, required=True) -> Optional[Path]:
        p = self.path_for(source, season)
        u = self.url_for(source, season)
        if p.exists() and p.stat().st_size > 50:
            self.status.append(SourceStatus(source, season, str(p), u, True))
            return p
        try:
            with requests.get(u, stream=True, timeout=self.timeout, headers={"User-Agent": "FIE-V8.3-M1/1.0"}) as r:
                r.raise_for_status()
                tmp = p.with_suffix(".tmp")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        if chunk: f.write(chunk)
                tmp.replace(p)
            self.status.append(SourceStatus(source, season, str(p), u, True))
            return p
        except Exception as e:
            self.status.append(SourceStatus(source, season, str(p), u, False, error=str(e)))
            if required: raise
            return None

    def load(self, source: str, season: Optional[int] = None, required=True) -> pd.DataFrame:
        p = self.ensure(source, season, required=required)
        if p is None: return pd.DataFrame()
        try:
            df = pd.read_csv(p, low_memory=False)
            self.status[-1].rows = int(len(df))
            return df
        except Exception as e:
            self.status[-1].ok = False
            self.status[-1].error = f"read_csv: {e}"
            if required: raise
            return pd.DataFrame()


def load_scoring(args) -> Tuple[dict, dict]:
    provenance = {"type": "default_ppr", "league_id": None}
    if args.scoring_json:
        scoring = json.loads(Path(args.scoring_json).read_text())
        provenance = {"type": "json_file", "path": str(args.scoring_json), "league_id": None}
        return scoring, provenance
    league_id = args.league_id or os.environ.get("FIE_LEAGUE_ID")
    if league_id:
        u = f"https://api.sleeper.app/v1/league/{league_id}"
        r = requests.get(u, timeout=30, headers={"User-Agent": "FIE-V8.3-M1/1.0"})
        r.raise_for_status()
        league = r.json()
        scoring = league.get("scoring_settings") or DEFAULT_PPR
        provenance = {"type": "sleeper_league", "league_id": str(league_id), "league_name": league.get("name")}
        return scoring, provenance
    return dict(DEFAULT_PPR), provenance


# Sleeper scoring key -> nflverse raw-stat aliases.
SCORING_MAP = {
    "pass_yd": ["passing_yards"], "pass_td": ["passing_tds"], "pass_int": ["passing_interceptions", "interceptions"],
    "pass_cmp": ["completions"], "pass_att": ["attempts", "passing_attempts"],
    "pass_2pt": ["passing_2pt_conversions"], "pass_fd": ["passing_first_downs"],
    "rush_yd": ["rushing_yards"], "rush_td": ["rushing_tds"], "rush_att": ["carries", "rushing_attempts"],
    "rush_2pt": ["rushing_2pt_conversions"], "rush_fd": ["rushing_first_downs"],
    "rec": ["receptions"], "rec_yd": ["receiving_yards"], "rec_td": ["receiving_tds"], "rec_tgt": ["targets"],
    "rec_2pt": ["receiving_2pt_conversions"], "rec_fd": ["receiving_first_downs"],
    "fum_lost": ["fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost", "sack_fumbles_lost"],
    "tkl_solo": ["tackles_solo", "def_tackles_solo"], "tkl_ast": ["tackles_with_assist", "tackles_assists", "def_tackles_assist"],
    "tkl_loss": ["tackles_for_loss", "def_tackles_for_loss"], "sack": ["def_sacks", "sacks"],
    "qb_hit": ["def_qb_hits", "qb_hits"], "int": ["def_interceptions", "interceptions_defense"],
    "pass_def": ["def_pass_defended", "passes_defended"], "ff": ["def_fumbles_forced", "fumbles_forced"],
    "fum_rec": ["def_fumbles", "fumble_recoveries"], "def_td": ["def_tds", "defensive_tds"],
}

BONUS_RULES = {
    "bonus_pass_yd_300": ("passing_yards", 300), "bonus_pass_yd_400": ("passing_yards", 400),
    "bonus_rush_yd_100": ("rushing_yards", 100), "bonus_rush_yd_200": ("rushing_yards", 200),
    "bonus_rec_yd_100": ("receiving_yards", 100), "bonus_rec_yd_200": ("receiving_yards", 200),
}


def scoring_audit(df: pd.DataFrame, scoring: dict) -> dict:
    supported, unsupported = [], []
    cols = set(df.columns)
    for key, weight in scoring.items():
        if not finite(weight) or float(weight) == 0:
            continue
        if key in {"bonus_rec_te", "rec_te", "bonus_rec_rb", "rec_rb", "bonus_rec_wr", "rec_wr"}:
            if "receptions" in cols and "position_model" in cols:
                supported.append(key)
            else:
                unsupported.append({"key": key, "reason": "required TE/reception field absent"})
            continue
        if key in BONUS_RULES:
            field, _ = BONUS_RULES[key]
            (supported if field in cols else unsupported).append(key if field in cols else {"key": key, "reason": f"source field {field} absent"})
            continue
        aliases = SCORING_MAP.get(key)
        if not aliases:
            unsupported.append({"key": key, "reason": "no Milestone 1 raw-stat mapping"})
        elif any(c in cols for c in aliases):
            supported.append(key)
        else:
            unsupported.append({"key": key, "reason": "mapped raw-stat field absent"})
    return {
        "nonzero_keys": len(supported) + len(unsupported),
        "supported_keys": sorted(supported),
        "unsupported": unsupported,
        "exact_replay_eligible": len(unsupported) == 0,
        "coverage_rate": (len(supported) / (len(supported) + len(unsupported))) if (supported or unsupported) else 1.0,
    }


def score_rows(df: pd.DataFrame, scoring: dict) -> pd.Series:
    out = pd.Series(0.0, index=df.index)
    for key, weight in scoring.items():
        if not finite(weight) or float(weight) == 0: continue
        w = float(weight)
        if key in {"bonus_rec_te", "rec_te", "bonus_rec_rb", "rec_rb", "bonus_rec_wr", "rec_wr"}:
            if "receptions" in df.columns and "position_model" in df.columns:
                target = "TE" if "_te" in key else ("RB" if "_rb" in key else "WR")
                mask = df["position_model"].astype(str).eq(target).astype(float)
                out += pd.to_numeric(df["receptions"], errors="coerce").fillna(0) * mask * w
            continue
        if key in BONUS_RULES:
            field, threshold = BONUS_RULES[key]
            if field in df.columns: out += (pd.to_numeric(df[field], errors="coerce").fillna(0) >= threshold).astype(float) * w
            continue
        aliases = SCORING_MAP.get(key)
        if not aliases: continue
        # fumbles lost may be split across multiple columns; avoid summing generic plus split duplicates.
        if key == "fum_lost":
            if "fumbles_lost" in df.columns:
                vals = pd.to_numeric(df["fumbles_lost"], errors="coerce").fillna(0)
            else:
                vals = sum((pd.to_numeric(df[c], errors="coerce").fillna(0) for c in aliases if c in df.columns), start=pd.Series(0.0, index=df.index))
        else:
            c = first_col(df, aliases)
            if c is None: continue
            vals = pd.to_numeric(df[c], errors="coerce").fillna(0)
        out += vals * w
    return out


def build_identity(players: pd.DataFrame, ffids: Optional[pd.DataFrame] = None) -> Tuple[pd.DataFrame, dict]:
    p = players.copy()
    rename = {}
    wanted = {
        "gsis_id": ["gsis_id", "gsis_it_id"], "pfr_id": ["pfr_id"], "pff_id": ["pff_id"],
        "otc_id": ["otc_id"], "espn_id": ["espn_id"],
        "full_name": ["display_name", "full_name", "football_name"], "position": ["position"],
    }
    for want, opts in wanted.items():
        c = first_col(p, opts)
        if c and c != want: rename[c] = want
    p = p.rename(columns=rename)
    for c in ["gsis_id", "pfr_id", "pff_id", "otc_id", "espn_id", "full_name", "position"]:
        if c not in p.columns: p[c] = None
    if ffids is not None and not ffids.empty:
        f = ffids.copy()
        keep = [c for c in ["gsis_id","pfr_id","pff_id","sleeper_id","espn_id"] if c in f.columns]
        f = f[keep].copy() if keep else pd.DataFrame()
        if not f.empty and "gsis_id" in f.columns:
            f = f.drop_duplicates("gsis_id")
            p = p.merge(f, on="gsis_id", how="left", suffixes=("", "_ff"))
            for c in ["pfr_id","pff_id","espn_id","sleeper_id"]:
                ff = f"{c}_ff"
                if ff in p.columns:
                    p[c] = p[c].fillna(p[ff]) if c in p.columns else p[ff]
                    p = p.drop(columns=[ff])
        elif "sleeper_id" not in p.columns:
            p["sleeper_id"] = None
    elif "sleeper_id" not in p.columns:
        p["sleeper_id"] = None
    p["canonical_player_id"] = p["gsis_id"].fillna("").astype(str)
    miss = p["canonical_player_id"].isin(["", "nan", "None"])
    p.loc[miss, "canonical_player_id"] = "PFR:" + p.loc[miss, "pfr_id"].fillna("").astype(str)
    miss = p["canonical_player_id"].isin(["PFR:", "PFR:nan", "PFR:None"])
    p.loc[miss, "canonical_player_id"] = "NAME:" + p.loc[miss, "full_name"].fillna("").str.lower().str.replace(r"[^a-z0-9]+", "", regex=True)
    p["identity_confidence"] = np.where(p["gsis_id"].notna(), "exact_gsis", np.where(p["pfr_id"].notna(), "exact_pfr", "name_fallback"))
    p["tfg_key"] = p["full_name"].fillna("").str.lower().str.replace(r"[^a-z0-9]+", "", regex=True)
    dup = int(p["canonical_player_id"].duplicated().sum())
    stats = {
        "rows": int(len(p)), "gsis": int(p["gsis_id"].notna().sum()), "pfr": int(p["pfr_id"].notna().sum()),
        "pff": int(p["pff_id"].notna().sum()), "otc": int(p["otc_id"].notna().sum()),
        "espn": int(p["espn_id"].notna().sum()), "sleeper": int(p["sleeper_id"].notna().sum()),
        "tfg_join_key": int((p["tfg_key"] != "").sum()),
        "name_fallback": int((p.identity_confidence == "name_fallback").sum()), "duplicate_canonical_ids": dup,
    }
    return p, stats


def join_identity(player_week: pd.DataFrame, identity: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    df = player_week.copy()
    idc = first_col(df, ID_COL_CANDIDATES)
    if idc is None:
        raise ValueError("weekly player stats have no recognized player ID column")
    df["source_player_id"] = df[idc].astype(str)
    idmap = identity[["gsis_id", "canonical_player_id", "full_name", "position"]].copy()
    idmap["gsis_id"] = idmap["gsis_id"].astype(str)
    df = df.merge(idmap, left_on="source_player_id", right_on="gsis_id", how="left", suffixes=("", "_identity"))
    df["canonical_player_id"] = df["canonical_player_id"].fillna("GSIS:" + df["source_player_id"])
    match = df["full_name"].notna()
    return df, {"player_week_rows": int(len(df)), "exact_identity_matches": int(match.sum()), "unmatched_rows": int((~match).sum()), "match_rate": float(match.mean()) if len(df) else None}


def prep_player_week(frames: List[pd.DataFrame], identity: pd.DataFrame, scoring: dict) -> Tuple[pd.DataFrame, dict, dict]:
    df = pd.concat(frames, ignore_index=True, sort=False)
    df, match = join_identity(df, identity)
    tc = first_col(df, TEAM_COL_CANDIDATES)
    pc = first_col(df, POS_COL_CANDIDATES)
    if tc is None: df["team"] = None
    else: df["team"] = df[tc]
    if pc is None: df["position_raw"] = df.get("position_identity", "")
    else: df["position_raw"] = df[pc]
    if "position_identity" in df.columns:
        df["position_raw"] = df["position_raw"].fillna(df["position_identity"])
    df["position_model"] = [normalize_position(p) for p in df["position_raw"]]
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")
    if "season_type" in df.columns:
        df = df[df["season_type"].astype(str).str.upper().str.startswith("REG")]

    # nflverse renamed QB passing interceptions from `interceptions` to
    # `passing_interceptions`. Preserve a canonical legacy alias in the derived
    # backbone so downstream M4/M7-M9 code and older caches remain compatible.
    if "passing_interceptions" in df.columns:
        current_int = pd.to_numeric(df["passing_interceptions"], errors="coerce")
        if "interceptions" not in df.columns:
            df["interceptions"] = current_int
        else:
            legacy_int = pd.to_numeric(df["interceptions"], errors="coerce")
            df["interceptions"] = legacy_int.where(legacy_int.notna(), current_int)

    audit = scoring_audit(df, scoring)
    df["fantasy_points"] = score_rows(df, scoring)
    return df, match, audit


def prep_team_week(frames: List[pd.DataFrame]) -> pd.DataFrame:
    df = pd.concat(frames, ignore_index=True, sort=False)
    tc = first_col(df, ["team", "recent_team", "posteam"])
    if tc is None: raise ValueError("team weekly stats have no team column")
    df["team"] = df[tc]
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64")
    if "season_type" in df.columns: df = df[df["season_type"].astype(str).str.upper().str.startswith("REG")]
    df["team_pass_attempts"] = num_series(df, ["attempts", "passing_attempts"])
    df["team_rush_attempts"] = num_series(df, ["carries", "rushing_attempts"])
    # sacks count as dropbacks/plays if a clean team-level field exists.
    sacks = num_series(df, ["sacks_suffered", "sacks_allowed"], 0.0)
    df["team_dropbacks"] = df["team_pass_attempts"] + sacks
    df["team_plays"] = df["team_pass_attempts"] + df["team_rush_attempts"] + sacks
    if "opponent_team" not in df.columns: df["opponent_team"] = None
    keep = ["season", "week", "team", "opponent_team", "team_plays", "team_dropbacks", "team_pass_attempts", "team_rush_attempts"]
    base = df[keep].drop_duplicates(["season", "week", "team"])
    defense = base[["season","week","opponent_team","team_plays","team_dropbacks","team_rush_attempts"]].rename(columns={
        "opponent_team":"team", "team_plays":"defensive_opponent_plays",
        "team_dropbacks":"defensive_opponent_dropbacks", "team_rush_attempts":"defensive_opponent_rush_attempts"
    })
    return base.merge(defense, on=["season","week","team"], how="left")


def prep_snaps(frames: List[pd.DataFrame], identity: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    if not frames: return pd.DataFrame(), {"rows": 0, "matched": 0, "match_rate": None}
    df = pd.concat(frames, ignore_index=True, sort=False)
    pfrc = first_col(df, ["pfr_player_id", "player_id"])
    if pfrc is None: return pd.DataFrame(), {"rows": int(len(df)), "matched": 0, "match_rate": 0.0}
    imap = identity[["pfr_id", "canonical_player_id"]].dropna(subset=["pfr_id"]).copy()
    imap["pfr_id"] = imap["pfr_id"].astype(str)
    df["pfr_source"] = df[pfrc].astype(str)
    df = df.merge(imap, left_on="pfr_source", right_on="pfr_id", how="left")
    match = df["canonical_player_id"].notna()
    df["season"] = pd.to_numeric(df["season"], errors="coerce").astype("Int64")
    df["week"] = pd.to_numeric(df["week"], errors="coerce").astype("Int64") if "week" in df.columns else pd.NA
    off = num_series(df, ["offense_pct", "off_pct", "offense_percentage"])
    deff = num_series(df, ["defense_pct", "def_pct", "defense_percentage"])
    off = np.where(off > 1, off / 100.0, off)
    deff = np.where(deff > 1, deff / 100.0, deff)
    df["offense_snap_share"] = off
    df["defense_snap_share"] = deff
    df["snap_share"] = np.maximum(df["offense_snap_share"], df["defense_snap_share"])
    keep = ["season", "week", "canonical_player_id", "offense_snap_share", "defense_snap_share", "snap_share"]
    out = df[keep].dropna(subset=["canonical_player_id"]).copy()
    return out, {"rows": int(len(df)), "matched": int(match.sum()), "match_rate": float(match.mean()) if len(df) else None}


def prep_pbp_opportunity(pbp: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Reduce play-by-play to team/player red-zone opportunity tables.

    End-zone targets are an explicit proxy: air_yards >= yardline_100 on a targeted pass.
    This is useful diagnostically but is not presented as charted end-zone-target data.
    """
    if pbp is None or pbp.empty:
        return pd.DataFrame(), pd.DataFrame()
    p = pbp.copy()
    if "season_type" in p.columns:
        p = p[p["season_type"].astype(str).str.upper().str.startswith("REG")]
    tc = first_col(p, ["posteam", "team"])
    if tc is None or "season" not in p.columns or "week" not in p.columns:
        return pd.DataFrame(), pd.DataFrame()
    p["team"] = p[tc]
    p["season"] = pd.to_numeric(p["season"], errors="coerce").astype("Int64")
    p["week"] = pd.to_numeric(p["week"], errors="coerce").astype("Int64")
    yard = pd.to_numeric(p.get("yardline_100", np.nan), errors="coerce")
    rush = num_series(p, ["rush_attempt"], 0.0).eq(1)
    pass_attempt = num_series(p, ["pass_attempt"], 0.0).eq(1)
    dropback = num_series(p, ["qb_dropback"], 0.0).eq(1)
    opportunity_play = rush | pass_attempt | dropback
    p["_rz"] = opportunity_play & yard.le(20) & yard.gt(0)
    p["_gl"] = opportunity_play & yard.le(5) & yard.gt(0)
    p["_rush_rz"] = rush & yard.le(20) & yard.gt(0)
    p["_rush_i10"] = rush & yard.le(10) & yard.gt(0)
    p["_rush_i5"] = rush & yard.le(5) & yard.gt(0)
    p["_tgt_rz"] = pass_attempt & yard.le(20) & yard.gt(0)
    air = pd.to_numeric(p.get("air_yards", np.nan), errors="coerce")
    p["_tgt_endzone_proxy"] = p["_tgt_rz"] & air.notna() & (air >= yard)

    team = p.groupby(["season","week","team"], as_index=False).agg(
        team_red_zone_plays=("_rz","sum"), team_goal_line_plays=("_gl","sum"),
        team_red_zone_rushes=("_rush_rz","sum"), team_inside_10_rushes=("_rush_i10","sum"),
        team_inside_5_rushes=("_rush_i5","sum"), team_red_zone_targets=("_tgt_rz","sum"),
        team_end_zone_targets_proxy=("_tgt_endzone_proxy","sum")
    )

    frames = []
    rusher = first_col(p, ["rusher_player_id", "rusher_id"])
    if rusher:
        r = p[p[rusher].notna() & (p["_rush_rz"] | p["_rush_i10"] | p["_rush_i5"])].copy()
        if not r.empty:
            r["source_player_id"] = r[rusher].astype(str)
            ra = r.groupby(["season","week","team","source_player_id"], as_index=False).agg(
                player_red_zone_carries=("_rush_rz","sum"), player_inside_10_carries=("_rush_i10","sum"),
                player_inside_5_carries=("_rush_i5","sum")
            )
            frames.append(ra)
    receiver = first_col(p, ["receiver_player_id", "targeted_receiver_player_id", "receiver_id"])
    if receiver:
        q = p[p[receiver].notna() & (p["_tgt_rz"] | p["_tgt_endzone_proxy"])].copy()
        if not q.empty:
            q["source_player_id"] = q[receiver].astype(str)
            qa = q.groupby(["season","week","team","source_player_id"], as_index=False).agg(
                player_red_zone_targets=("_tgt_rz","sum"), player_end_zone_targets_proxy=("_tgt_endzone_proxy","sum")
            )
            frames.append(qa)
    if not frames:
        return team, pd.DataFrame()
    player = frames[0]
    for f in frames[1:]:
        player = player.merge(f, on=["season","week","team","source_player_id"], how="outer")
    player = player.merge(team, on=["season","week","team"], how="left")
    for c in ["player_red_zone_carries","player_inside_10_carries","player_inside_5_carries","player_red_zone_targets","player_end_zone_targets_proxy"]:
        if c not in player.columns: player[c] = 0.0
        player[c] = pd.to_numeric(player[c], errors="coerce").fillna(0.0)
    player["red_zone_carry_share"] = np.where(player.team_red_zone_rushes > 0, player.player_red_zone_carries / player.team_red_zone_rushes, np.nan)
    player["inside_10_carry_share"] = np.where(player.team_inside_10_rushes > 0, player.player_inside_10_carries / player.team_inside_10_rushes, np.nan)
    player["inside_5_carry_share"] = np.where(player.team_inside_5_rushes > 0, player.player_inside_5_carries / player.team_inside_5_rushes, np.nan)
    player["red_zone_target_share"] = np.where(player.team_red_zone_targets > 0, player.player_red_zone_targets / player.team_red_zone_targets, np.nan)
    player["end_zone_target_share_proxy"] = np.where(player.team_end_zone_targets_proxy > 0, player.player_end_zone_targets_proxy / player.team_end_zone_targets_proxy, np.nan)
    keep = ["season","week","team","source_player_id","red_zone_carry_share","inside_10_carry_share","inside_5_carry_share","red_zone_target_share","end_zone_target_share_proxy"]
    return team, player[keep]


def merge_pbp_team_opportunity(team_week: pd.DataFrame, pbp_team) -> pd.DataFrame:
    t = team_week.copy()
    if pbp_team is None or (isinstance(pbp_team, list) and not pbp_team) or (hasattr(pbp_team, "empty") and pbp_team.empty):
        for c in ["team_red_zone_plays","team_goal_line_plays"]:
            t[c] = np.nan
        return t
    po = pd.concat(pbp_team if isinstance(pbp_team, list) else [pbp_team], ignore_index=True, sort=False)
    po = po.drop_duplicates(["season","week","team"])
    t = t.merge(po, on=["season","week","team"], how="left")
    # Defensive environment mirrors the opponent offense, same as core volume.
    rev = po[["season","week","team","team_red_zone_plays","team_goal_line_plays"]].rename(columns={
        "team":"opponent_team", "team_red_zone_plays":"defensive_opponent_red_zone_plays",
        "team_goal_line_plays":"defensive_opponent_goal_line_plays"
    })
    return t.merge(rev, on=["season","week","opponent_team"], how="left")


def derive_opportunity(player_week: pd.DataFrame, team_week: pd.DataFrame, snaps: pd.DataFrame, pbp_player: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    df = player_week.merge(team_week, on=["season", "week", "team"], how="left")
    if not snaps.empty:
        # PFR snap counts are game-level. Weekly collisions are rare but possible; aggregate first.
        s = snaps.groupby(["season", "week", "canonical_player_id"], as_index=False).agg({
            "offense_snap_share": "max", "defense_snap_share": "max", "snap_share": "max"
        })
        df = df.merge(s, on=["season", "week", "canonical_player_id"], how="left")
    else:
        df["offense_snap_share"] = np.nan; df["defense_snap_share"] = np.nan; df["snap_share"] = np.nan

    targets = num_series(df, ["targets"])
    carries = num_series(df, ["carries", "rushing_attempts"])
    df["target_share"] = np.where(df["team_pass_attempts"] > 0, targets / df["team_pass_attempts"], np.nan)
    df["carry_share"] = np.where(df["team_rush_attempts"] > 0, carries / df["team_rush_attempts"], np.nan)
    df["targets_per_pass_attempt"] = df["target_share"]
    df["carries_per_rush_attempt"] = df["carry_share"]
    df["qb_rush_share"] = np.where((df["position_model"] == "QB") & (df["team_rush_attempts"] > 0), carries / df["team_rush_attempts"], np.nan)
    # Proxy only: offensive snap share on pass-heavy weeks is not claimed as true routes.
    df["pass_play_participation_proxy"] = np.where(df["position_model"].isin(["WR", "TE", "RB"]), df["offense_snap_share"], np.nan)
    df["true_route_participation"] = np.nan

    # Role-specific defensive opportunity proxies. They are explicitly labelled proxies,
    # not true pass-rush/coverage/tackle opportunity counts.
    df["pass_rush_opportunity_proxy"] = df["defense_snap_share"] * df["defensive_opponent_dropbacks"]
    df["tackle_opportunity_proxy"] = df["defense_snap_share"] * df["defensive_opponent_plays"]
    df["coverage_opportunity_proxy"] = df["defense_snap_share"] * df["defensive_opponent_dropbacks"]
    if pbp_player is not None and not pbp_player.empty:
        pp = pbp_player.drop_duplicates(["season","week","team","source_player_id"])
        df = df.merge(pp, on=["season","week","team","source_player_id"], how="left")
    for c in ["red_zone_carry_share","inside_10_carry_share","inside_5_carry_share","red_zone_target_share","end_zone_target_share_proxy"]:
        if c not in df.columns: df[c] = np.nan
    return df


def add_pregame_features(df: pd.DataFrame, metrics: Sequence[str]) -> pd.DataFrame:
    df = df.sort_values(["canonical_player_id", "season", "week"]).copy()
    g = df.groupby("canonical_player_id", group_keys=False)
    # Previous performance baseline; no current-week data can enter prediction features.
    df["fp_prior_4"] = g["fantasy_points"].transform(lambda s: s.shift(1).rolling(4, min_periods=2).mean())
    df["fp_prior_8"] = g["fantasy_points"].transform(lambda s: s.shift(1).rolling(8, min_periods=3).mean())
    for m in metrics:
        if m not in df.columns: continue
        df[f"{m}_prior4"] = g[m].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(4, min_periods=2).mean())
        df[f"{m}_prior8"] = g[m].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(8, min_periods=3).mean())
    # Forward outcomes for diagnostic testing. These are labels, never model inputs.
    df["fp_next_week"] = g["fantasy_points"].shift(-1)
    df["fp_next3"] = g["fantasy_points"].transform(lambda s: s.shift(-1)[::-1].rolling(3, min_periods=1).mean()[::-1])
    # ROS mean excludes current week.
    def ros(s: pd.Series) -> pd.Series:
        arr = s.to_numpy(dtype=float)
        out = np.full(len(arr), np.nan)
        for i in range(len(arr)):
            tail = arr[i+1:]
            tail = tail[np.isfinite(tail)]
            if len(tail): out[i] = tail.mean()
        return pd.Series(out, index=s.index)
    df["fp_ros"] = df.groupby(["canonical_player_id", "season"], group_keys=False)["fantasy_points"].apply(ros)
    # Next-season ppg mapped to current season rows.
    seas = df.groupby(["canonical_player_id", "season"], as_index=False)["fantasy_points"].mean().rename(columns={"fantasy_points":"season_ppg"})
    nextmap = seas[["canonical_player_id","season","season_ppg"]].copy()
    nextmap["season"] = nextmap["season"] - 1
    nextmap = nextmap.rename(columns={"season_ppg":"fp_next_season"})
    df = df.merge(nextmap, on=["canonical_player_id","season"], how="left")
    return df


def team_opportunity_forecast_frame(team_week: pd.DataFrame) -> pd.DataFrame:
    t = team_week.sort_values(["team","season","week"]).copy()
    volume_cols=[c for c in ["team_plays","team_dropbacks","team_pass_attempts","team_rush_attempts","team_red_zone_plays","team_goal_line_plays"] if c in t.columns and pd.to_numeric(t[c],errors="coerce").notna().any()]
    for col in volume_cols:
        t[f"{col}_prior4"] = t.groupby("team")[col].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(4,min_periods=2).mean())
        t[f"{col}_prior8"] = t.groupby("team")[col].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(1).rolling(8,min_periods=3).mean())
    opp = t[["season","week","team","team_plays_prior4","team_dropbacks_prior4","team_pass_attempts_prior4","team_rush_attempts_prior4"]].rename(columns={
        "team":"opponent_team",
        "team_plays_prior4":"opp_plays_prior4",
        "team_dropbacks_prior4":"opp_dropbacks_prior4",
        "team_pass_attempts_prior4":"opp_pass_attempts_prior4",
        "team_rush_attempts_prior4":"opp_rush_attempts_prior4",
    })
    return t.merge(opp,on=["season","week","opponent_team"],how="left")


def team_opportunity_validation(team_week: pd.DataFrame) -> List[dict]:
    t=team_opportunity_forecast_frame(team_week)
    folds=[(list(range(2019,2022)),2022),(list(range(2019,2023)),2023),(list(range(2019,2024)),2024),(list(range(2019,2025)),2025)]
    targets=[c for c in ["team_plays","team_dropbacks","team_pass_attempts","team_rush_attempts","team_red_zone_plays","team_goal_line_plays"] if c in t.columns and pd.to_numeric(t[c],errors="coerce").notna().any()]
    out=[]
    for target in targets:
        base=f"{target}_prior4"
        features=[base,f"{target}_prior8","opp_plays_prior4","opp_dropbacks_prior4","opp_pass_attempts_prior4","opp_rush_attempts_prior4"]
        for train_seasons,test_season in folds:
            tr=t[t.season.isin(train_seasons)].dropna(subset=[target,base]).copy()
            te=t[t.season==test_season].dropna(subset=[target,base]).copy()
            if len(tr)<150 or len(te)<40: continue
            base_pred=te[base].to_numpy(float)
            base_mae=float(mean_absolute_error(te[target],base_pred))
            use=[f for f in features if f in tr.columns and pd.to_numeric(tr[f],errors="coerce").notna().any()]
            model=build_model(); model.fit(tr[use],tr[target]); pred=model.predict(te[use])
            mae=float(mean_absolute_error(te[target],pred)); rank,_=safe_corr(pd.Series(pred,index=te.index),te[target],"spearman")
            out.append({"target":target,"train_start":min(train_seasons),"train_end":max(train_seasons),"test_season":test_season,"n_train":int(len(tr)),"n_test":int(len(te)),"baseline_mae":base_mae,"model_mae":mae,"rmse":rmse(te[target],pred),"spearman":rank,"mae_improvement_vs_prior4":float((base_mae-mae)/base_mae) if base_mae>0 else None,"features":use})
    return out


def stability_table(df: pd.DataFrame, metrics: Sequence[str]) -> List[dict]:
    out=[]
    for pos in POSITIONS:
        z=df[df.position_model==pos].copy()
        if z.empty: continue
        for m in POSITION_METRICS.get(pos, []):
            if m not in z.columns: continue
            # Week-to-week within player-season.
            z2=z.sort_values(["canonical_player_id","season","week"]).copy()
            z2["next_metric"] = z2.groupby(["canonical_player_id","season"])[m].shift(-1)
            rw,nw=safe_corr(z2[m], z2["next_metric"], "spearman")
            # 4-week prior average versus following 4-week average.
            z2["prev4"] = z2.groupby(["canonical_player_id","season"])[m].transform(lambda s: pd.to_numeric(s,errors="coerce").rolling(4,min_periods=2).mean())
            z2["next4"] = z2.groupby(["canonical_player_id","season"])[m].transform(lambda s: pd.to_numeric(s,errors="coerce").shift(-1)[::-1].rolling(4,min_periods=2).mean()[::-1])
            r4,n4=safe_corr(z2["prev4"], z2["next4"], "spearman")
            # Year-to-year player-season average.
            ys=z2.groupby(["canonical_player_id","season"],as_index=False)[m].mean()
            ys["next"] = ys.groupby("canonical_player_id")[m].shift(-1)
            yy,ny=safe_corr(ys[m],ys["next"],"spearman")
            score=np.nanmean([v for v in [rw,r4,yy] if v is not None]) if any(v is not None for v in [rw,r4,yy]) else np.nan
            label="insufficient"
            if np.isfinite(score): label="high" if score>=.60 else "medium" if score>=.35 else "low"
            out.append({"position":pos,"metric":m,"classification":METRIC_CLASS.get(m,"diagnostic"),"week_to_week_spearman":rw,"week_to_week_n":nw,"block4_spearman":r4,"block4_n":n4,"year_to_year_spearman":yy,"year_to_year_n":ny,"stability_score":None if not np.isfinite(score) else float(score),"stability_label":label})
    return out


def predictiveness_table(df: pd.DataFrame) -> List[dict]:
    out=[]
    horizons=[("next_week","fp_next_week"),("next3","fp_next3"),("ros","fp_ros"),("next_season","fp_next_season")]
    for pos in POSITIONS:
        z=df[df.position_model==pos].copy()
        if z.empty: continue
        for m in POSITION_METRICS.get(pos, []):
            feat=f"{m}_prior4"
            if feat not in z.columns: continue
            rec={"position":pos,"metric":m,"classification":METRIC_CLASS.get(m,"diagnostic")}
            for label,yc in horizons:
                r,n=safe_corr(z[feat],z[yc],"spearman")
                rec[f"{label}_spearman"]=r; rec[f"{label}_n"]=n
            out.append(rec)
    return out


def build_model() -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=8.0)),
    ])


def validation_table(df: pd.DataFrame) -> List[dict]:
    out=[]
    folds=[(list(range(2019,2022)),2022),(list(range(2019,2023)),2023),(list(range(2019,2024)),2024),(list(range(2019,2025)),2025)]
    for pos in POSITIONS:
        z=df[df.position_model==pos].copy()
        if z.empty: continue
        opp=[f"{m}_prior4" for m in POSITION_METRICS.get(pos,[]) if f"{m}_prior4" in z.columns]
        base_features=["fp_prior_4","fp_prior_8"]
        for train_seasons,test_season in folds:
            train=z[z.season.isin(train_seasons)].dropna(subset=["fp_next_week"]).copy()
            test=z[z.season==test_season].dropna(subset=["fp_next_week"]).copy()
            # Minimums prevent tiny-sample claims.
            if len(train)<80 or len(test)<20: continue
            for model_name,features in [("baseline",base_features),("opportunity",base_features+opp)]:
                use=[f for f in features if f in z.columns and pd.to_numeric(train[f], errors="coerce").notna().any()]
                if not use: continue
                model=build_model(); model.fit(train[use],train["fp_next_week"])
                pred=model.predict(test[use])
                mae=float(mean_absolute_error(test["fp_next_week"],pred)); r=rmse(test["fp_next_week"],pred)
                rank,_=safe_corr(pd.Series(pred,index=test.index),test["fp_next_week"],"spearman")
                out.append({"position":pos,"train_start":min(train_seasons),"train_end":max(train_seasons),"test_season":test_season,"model":model_name,"n_train":int(len(train)),"n_test":int(len(test)),"features":use,"mae":mae,"rmse":r,"spearman":rank})
    # Attach within-fold improvement for UI convenience.
    key={}
    for row in out: key[(row["position"],row["test_season"],row["model"])]=row
    for row in out:
        if row["model"]!="opportunity": continue
        b=key.get((row["position"],row["test_season"],"baseline"))
        row["mae_improvement_vs_baseline"] = None if not b or b["mae"]<=0 else float((b["mae"]-row["mae"])/b["mae"])
    return out


def coverage_summary(df: pd.DataFrame, sources: List[SourceStatus]) -> dict:
    out={"player_weeks":int(len(df)),"seasons":sorted(int(x) for x in df.season.dropna().unique()),"positions":{}}
    for pos in POSITIONS:
        z=df[df.position_model==pos]
        out["positions"][pos]={"rows":int(len(z)),"players":int(z.canonical_player_id.nunique())}
        for m in POSITION_METRICS.get(pos,[]):
            if m in z.columns: out["positions"][pos][m]=float(pd.to_numeric(z[m],errors="coerce").notna().mean()) if len(z) else 0.0
    out["sources"]=[asdict(s) for s in sources]
    return out


def summarize_validation(rows: List[dict]) -> List[dict]:
    # Retain fold rows; also add aggregate per position/model.
    df=pd.DataFrame(rows)
    if df.empty: return rows
    ag=[]
    for (pos,model),g in df.groupby(["position","model"]):
        ag.append({"position":pos,"model":model,"aggregate":True,"folds":int(len(g)),"n_test":int(g.n_test.sum()),"mae":float(np.average(g.mae,weights=g.n_test)),"rmse":float(np.average(g.rmse,weights=g.n_test)),"spearman":float(np.nanmean(g.spearman)) if g.spearman.notna().any() else None})
    # Aggregate improvement.
    amap={(r["position"],r["model"]):r for r in ag}
    for r in ag:
        if r["model"]=="opportunity":
            b=amap.get((r["position"],"baseline"))
            r["mae_improvement_vs_baseline"] = None if not b or b["mae"]<=0 else float((b["mae"]-r["mae"])/b["mae"])
    return rows+ag


def make_fixture() -> Tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,pd.DataFrame]:
    """Deterministic synthetic fixture used only for local integrity tests."""
    rng=np.random.default_rng(73)
    players=[]; pw=[]; tw=[]; snaps=[]
    teams=["AAA","BBB","CCC","DDD"]
    pos_cycle=["QB","RB","WR","WR","TE","DE","DT","LB","S","CB"]
    for ti,t in enumerate(teams):
        for j,p in enumerate(pos_cycle):
            pid=f"00-{ti:02d}{j:02d}"; pfr=f"P{ti}{j}"
            players.append({"gsis_id":pid,"pfr_id":pfr,"display_name":f"Player {t} {j}","position":p})
    for season in range(2019,2026):
        for week in range(1,18):
            for ti,t in enumerate(teams):
                team_pass=30+rng.normal(0,4); team_rush=26+rng.normal(0,4)
                opp=teams[(ti+1)%len(teams)]
                tw.append({"season":season,"week":week,"team":t,"opponent_team":opp,"season_type":"REG","attempts":max(18,team_pass),"carries":max(16,team_rush)})
                for j,p in enumerate(pos_cycle):
                    pid=f"00-{ti:02d}{j:02d}"; pfr=f"P{ti}{j}"
                    base=.15+.045*j; role=max(.05,min(.95,base+rng.normal(0,.04)))
                    targets=0; carries=0
                    if p in ["WR","TE","RB"]: targets=max(0,int(team_pass*role*(.7 if p=="RB" else 1.0)+rng.normal(0,1.2)))
                    if p in ["RB","QB"]: carries=max(0,int(team_rush*role*(1.7 if p=="RB" else .55)+rng.normal(0,1.0)))
                    rec=max(0,int(targets*(.65+rng.normal(0,.05))))
                    recyd=max(0,rec*(9+rng.normal(0,2))); rushyd=max(0,carries*(4.2+rng.normal(0,.7)))
                    row={"season":season,"week":week,"season_type":"REG","player_id":pid,"recent_team":t,"position":p,
                         "attempts":max(0,int(team_pass)) if p=="QB" else 0,"passing_yards":max(0,int(team_pass*7+rng.normal(0,40))) if p=="QB" else 0,
                         "passing_tds":max(0,int(rng.poisson(1.6))) if p=="QB" else 0,"interceptions":max(0,int(rng.poisson(.6))) if p=="QB" else 0,
                         "carries":carries,"rushing_yards":rushyd,"rushing_tds":int(rng.random()<.10*carries/max(carries,1)),
                         "targets":targets,"receptions":rec,"receiving_yards":recyd,"receiving_tds":int(rng.random()<.08*targets/max(targets,1)),
                         "fumbles_lost":0,
                         "tackles_solo":max(0,int(rng.poisson(4))) if p in ["DE","DT","LB","S","CB"] else 0,
                         "tackles_with_assist":max(0,int(rng.poisson(2))) if p in ["DE","DT","LB","S","CB"] else 0,
                         "tackles_for_loss":max(0,int(rng.poisson(.4))) if p in ["DE","DT","LB"] else 0,
                         "def_sacks":max(0,int(rng.poisson(.25))) if p in ["DE","DT"] else 0,
                         "def_interceptions":max(0,int(rng.random()<.04)) if p in ["LB","S","CB"] else 0,
                         "def_pass_defended":max(0,int(rng.poisson(.3))) if p in ["LB","S","CB"] else 0,
                         "def_fumbles_forced":max(0,int(rng.random()<.03)) if p in ["DE","DT","LB","S","CB"] else 0,
                         "def_fumbles":0,"def_tds":0}
                    pw.append(row)
                    snaps.append({"season":season,"week":week,"pfr_player_id":pfr,"offense_pct":role*100 if p in ["QB","RB","WR","TE"] else 0,"defense_pct":role*100 if p not in ["QB","RB","WR","TE"] else 0})
    return pd.DataFrame(players),pd.DataFrame(pw),pd.DataFrame(tw),pd.DataFrame(snaps)


def write_derived_tables(primary: pd.DataFrame, team_week: pd.DataFrame, identity: pd.DataFrame, derived_dir: Optional[str]) -> dict:
    if not derived_dir:
        return {"written": False, "files": {}}
    out = Path(derived_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = {}

    def write(name: str, df: pd.DataFrame):
        path = out / f"{name}.csv.gz"
        df.to_csv(path, index=False, compression="gzip")
        files[name] = {"path": str(path), "rows": int(len(df)), "columns": int(len(df.columns))}

    # Canonical tables for follow-on research. These are not loaded by the browser app.
    pw = primary.copy()
    write("player_week", pw)
    write("team_week", team_week[team_week.season.isin(sorted(primary.season.dropna().astype(int).unique()))].copy())
    write("player_identity", identity.copy())

    ps = pw.groupby(["season", "canonical_player_id", "position_model"], dropna=False).agg(
        games=("week", "nunique"), fantasy_points=("fantasy_points", "sum"),
        fantasy_ppg=("fantasy_points", "mean"), snap_share=("snap_share", "mean"),
        target_share=("target_share", "mean"), carry_share=("carry_share", "mean")
    ).reset_index()
    write("player_season", ps)

    tw = team_week[team_week.season.isin(sorted(primary.season.dropna().astype(int).unique()))].copy()
    ts = tw.groupby(["season", "team"], dropna=False).agg(
        games=("week", "nunique"), team_plays=("team_plays", "sum"), team_dropbacks=("team_dropbacks", "sum"),
        team_pass_attempts=("team_pass_attempts", "sum"), team_rush_attempts=("team_rush_attempts", "sum")
    ).reset_index()
    write("team_season", ts)
    ge_cols = [c for c in ["season","week","team","opponent_team","team_plays","team_dropbacks","team_pass_attempts","team_rush_attempts","defensive_opponent_plays","defensive_opponent_dropbacks","defensive_opponent_rush_attempts"] if c in tw.columns]
    write("game_environment", tw[ge_cols].copy())
    return {"written": True, "files": files}


def run(args) -> dict:
    scoring, scoring_prov = load_scoring(args) if not args.fixture else (dict(DEFAULT_PPR),{"type":"fixture_default_ppr","league_id":None})
    source_manager=SourceManager(Path(args.cache_dir))
    if args.fixture:
        players,pw_all,tw_all,snaps_all=make_fixture()
        ffids=pd.DataFrame()
        pframes=[pw_all[pw_all.season==s].copy() for s in sorted(pw_all.season.unique())]
        tframes=[tw_all[tw_all.season==s].copy() for s in sorted(tw_all.season.unique())]
        sframes=[snaps_all[snaps_all.season==s].copy() for s in sorted(snaps_all.season.unique())]
        # Deterministic fixture opportunity tables exercise the same merge/validation path.
        fixture_team = prep_team_week(tframes)
        pbp_team_frames=[]
        for _,r in fixture_team.iterrows():
            pbp_team_frames.append({"season":r.season,"week":r.week,"team":r.team,"team_red_zone_plays":max(1,round(float(r.team_plays)*.18)),"team_goal_line_plays":max(0,round(float(r.team_plays)*.045)),"team_red_zone_rushes":max(1,round(float(r.team_rush_attempts)*.18)),"team_inside_10_rushes":max(1,round(float(r.team_rush_attempts)*.09)),"team_inside_5_rushes":max(1,round(float(r.team_rush_attempts)*.045)),"team_red_zone_targets":max(1,round(float(r.team_pass_attempts)*.16)),"team_end_zone_targets_proxy":max(1,round(float(r.team_pass_attempts)*.06))})
        pbp_team_frames=[pd.DataFrame(pbp_team_frames)]
        pbp_player_frames=[]
    else:
        players=source_manager.load("players")
        ffids=source_manager.load("ff_playerids", required=False)
        pframes=[];tframes=[];sframes=[];pbp_team_frames=[];pbp_player_frames=[]
        for s in args.seasons:
            pframes.append(source_manager.load("player_week",s))
            tframes.append(source_manager.load("team_week",s))
            sf=source_manager.load("snaps",s,required=False)
            if not sf.empty: sframes.append(sf)
            if not args.skip_pbp_opportunity:
                pf=source_manager.load("pbp",s,required=False)
                if not pf.empty:
                    to,po=prep_pbp_opportunity(pf)
                    if not to.empty: pbp_team_frames.append(to)
                    if not po.empty: pbp_player_frames.append(po)
                del pf
        if args.full_raw_cache:
            # Step 1 reproducibility archive. Optional failures are recorded in source health,
            # never substituted with invented values. Injury history intentionally stops at 2024.
            for s in args.extended_seasons:
                source_manager.ensure("pbp", s, required=False)
                if s >= 2016:
                    source_manager.ensure("participation", s, required=False)
                if s >= 2018:
                    for src in ["pfr_adv_pass", "pfr_adv_rush", "pfr_adv_rec", "pfr_adv_def"]:
                        source_manager.ensure(src, s, required=False)
                source_manager.ensure("rosters", s, required=False)
                source_manager.ensure("weekly_rosters", s, required=False)
                source_manager.ensure("depth_charts", s, required=False)
                if s <= 2024:
                    source_manager.ensure("injuries", s, required=False)
                if s >= 2022:
                    source_manager.ensure("ftn_charting", s, required=False)
            for src in ["ngs_passing", "ngs_receiving", "ngs_rushing", "contracts", "draft_picks", "combine"]:
                source_manager.ensure(src, required=False)

    identity, identity_stats=build_identity(players, ffids)
    player_week, player_match, scoring_support=prep_player_week(pframes,identity,scoring)
    team_week=prep_team_week(tframes)
    team_week=merge_pbp_team_opportunity(team_week, pbp_team_frames)
    snaps,snap_match=prep_snaps(sframes,identity)
    pbp_player=pd.concat(pbp_player_frames,ignore_index=True,sort=False) if pbp_player_frames else pd.DataFrame()
    derived=derive_opportunity(player_week,team_week,snaps,pbp_player)
    metrics=sorted(set(m for vals in POSITION_METRICS.values() for m in vals))
    derived=add_pregame_features(derived,metrics)
    primary=derived[derived.season.isin(args.seasons)].copy()
    derived_manifest=write_derived_tables(primary, team_week, identity, args.derived_dir)

    stability=stability_table(primary,metrics)
    predictiveness=predictiveness_table(primary)
    validation=summarize_validation(validation_table(primary))

    tested_positions={}
    for pos in POSITIONS:
        for m in POSITION_METRICS.get(pos,[]): tested_positions.setdefault(m,[]).append(pos)
    metric_catalog=[{"metric":m,"classification":cls,"positions":tested_positions.get(m,[]),"true_route":m=="true_route_participation","proxy":m.endswith("_proxy")} for m,cls in sorted(METRIC_CLASS.items())]
    team_validation=team_opportunity_validation(team_week[team_week.season.isin(args.seasons)].copy())

    bundle={
        "schema_version":1,"milestone":"M1","control_build":CONTROL_BUILD,"research_build":RESEARCH_BUILD,
        "generated_at":utc_now(),"status":"complete","diagnostic_only":True,
        "primary_window":[min(args.seasons),max(args.seasons)],"extended_window":[min(args.extended_seasons),max(args.extended_seasons)],
        "scoring":{"signature":scoring_signature(scoring),"provenance":scoring_prov,"settings":scoring,"support":scoring_support},
        "methodology":{
            "no_random_split":True,"pregame_lagging":True,
            "folds":["2019-2021 -> 2022","2019-2022 -> 2023","2019-2023 -> 2024","2019-2024 -> 2025"],
            "route_guardrail":"pass_play_participation_proxy is never labeled as true_route_participation",
            "team_opportunity":"separate pregame team-volume forecasts are validated before player allocation; PBP-derived red-zone and goal-line volume joins when available",
            "activation":"none in Milestone 1; all findings remain diagnostic"
        },
        "coverage":coverage_summary(primary,source_manager.status),
        "derived_tables":derived_manifest,
        "identity":{**identity_stats,"player_week":player_match,"snap_counts":snap_match},
        "metrics":metric_catalog,"team_opportunity_validation":team_validation,"stability":stability,"predictiveness":predictiveness,"validation":validation,
        "limitations":[
            "True all-route participation is not inferred from nflverse participation's primary-receiver route field.",
            "Defensive pass-rush, coverage and tackle opportunity counts are proxies from defensive snap share × opponent volume until true role-specific participation is integrated.",
            "PBP is used in the standard M1 build for team red-zone/goal-line volume and player red-zone shares; the broader participation/NGS/PFR/roster/depth/injury/FTN/contracts/draft/combine archive remains optional and diagnostic.",
            "Current injuries after 2024 are not part of this historical Milestone 1 pipeline.",
            "A scoring replay is labelled exact only when every non-zero Sleeper scoring key has a supported raw-stat mapping and source field; unsupported keys are surfaced in scoring.support instead of being silently ignored."
        ]
    }
    return bundle


def parse_args(argv=None):
    p=argparse.ArgumentParser(description="Build FIE V8.3-M1 research bundle")
    p.add_argument("--output",default="data/research/milestone1.json")
    p.add_argument("--cache-dir",default=".cache/fie-research")
    p.add_argument("--league-id",default=None,help="Optional Sleeper league ID; uses exact league scoring settings")
    p.add_argument("--scoring-json",default=None,help="Optional scoring-settings JSON file; overrides league ID")
    p.add_argument("--seasons",default=f"2019-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--extended-seasons",default=f"2016-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--full-raw-cache",action="store_true",help="Also cache the broader Step 1 archive for later milestones")
    p.add_argument("--skip-pbp-opportunity",action="store_true",help="Skip PBP-derived red-zone/goal-line opportunity features; they will remain missing")
    p.add_argument("--derived-dir",default=None,help="Optional directory for compact derived player/team/identity CSV.gz tables")
    p.add_argument("--fixture",action="store_true",help="Run deterministic synthetic integrity fixture, no network")
    args=p.parse_args(argv)
    def parse_range(x):
        if re.fullmatch(r"\d{4}-\d{4}",x):
            a,b=map(int,x.split("-")); return list(range(a,b+1))
        return [int(v) for v in x.split(",")]
    args.seasons=parse_range(args.seasons); args.extended_seasons=parse_range(args.extended_seasons)
    return args


def main(argv=None):
    args=parse_args(argv)
    bundle=run(args)
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(bundle,indent=2,allow_nan=False))
    print(f"Wrote {out} | status={bundle['status']} | player_weeks={bundle['coverage'].get('player_weeks',0)} | validation_rows={len(bundle['validation'])}")

if __name__=="__main__":
    main()
