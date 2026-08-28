#!/usr/bin/env python3
"""Optional point-in-time source contracts for FIE M7-M9.

The public research stack must remain fully runnable without premium data.  This
module defines the only names under which true route/coverage/trench data may be
introduced, so a pressure proxy can never silently masquerade as an OL grade and
nearest-defender data can never masquerade as coverage responsibility.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

import pandas as pd
import numpy as np

KEYS = ("season", "week", "team")

TRENCH_COLUMNS = {
    "ol_pass_block_win_rate": "true_or_charted_team_ol_pass_protection",
    "ol_pressure_allowed_rate": "true_or_charted_team_ol_pass_protection",
    "ol_quick_pressure_allowed_rate": "true_or_charted_team_ol_pass_protection",
    "ol_time_to_pressure_allowed": "true_or_charted_team_ol_pass_protection",
    "ol_run_block_win_rate": "true_or_charted_team_ol_run_blocking",
    "ol_yards_before_contact_over_expected": "true_or_charted_team_ol_run_blocking",
    "dl_pass_rush_win_rate": "true_or_charted_team_dl_pass_rush",
    "dl_pressure_rate": "true_or_charted_team_dl_pass_rush",
    "dl_quick_pressure_rate": "true_or_charted_team_dl_pass_rush",
    "dl_time_to_pressure": "true_or_charted_team_dl_pass_rush",
    "dl_run_stop_win_rate": "true_or_charted_team_dl_run_defense",
}

ROUTE_COLUMNS = {
    "route_participation": "all_route_tracking_or_charting",
    "targets_per_route": "all_route_tracking_or_charting",
    "first_read_share": "charted_first_read",
    "yards_per_route_run": "all_route_tracking_or_charting",
    "separation_win_rate": "all_route_tracking_or_charting",
    "pass_block_rate": "charted_te_usage",
    "inline_rate": "charted_alignment",
    "slot_rate": "charted_alignment",
}

COVERAGE_COLUMNS = {
    "def_man_rate": "coverage_classification",
    "def_zone_rate": "coverage_classification",
    "def_two_high_rate": "coverage_classification",
    "def_single_high_rate": "coverage_classification",
    "def_press_rate": "coverage_classification",
    "def_coverage_success_rate": "coverage_responsibility_or_team_charting",
    "def_explosive_pass_suppression": "coverage_responsibility_or_team_charting",
}

QB_COVERAGE_COLUMNS = {
    "qb_epa_vs_man": "charted_qb_coverage_split",
    "qb_epa_vs_zone": "charted_qb_coverage_split",
    "qb_epa_vs_blitz": "charted_qb_pressure_split",
    "qb_epa_vs_two_high": "charted_qb_shell_split",
    "qb_pressure_to_sack": "charted_qb_pressure_response",
}

PLAYER_FEATURE_KEYS = ("season", "week", "team", "canonical_player_id")

def validate_player_feature_source(path: Optional[str], allowed: Mapping[str, str], max_season: Optional[int] = None) -> tuple[pd.DataFrame, SourceHealth]:
    """Strict player-week charting contract. Values are treated as realised week-N data and lagged by consumers."""
    d=_read(path)
    if d.empty:
        return d, SourceHealth(path or "",0,0,(),0,0,"not_supplied","optional player feature source not supplied")
    missing=[k for k in PLAYER_FEATURE_KEYS if k not in d.columns]; present=[c for c in allowed if c in d.columns]
    if missing or not present:
        return pd.DataFrame(), SourceHealth(path or "",len(d),0,tuple(present),0,0,"invalid_schema",f"missing_keys={missing}; metric_columns={present}")
    q=d[list(PLAYER_FEATURE_KEYS)+present].copy(); q["season"]=pd.to_numeric(q.season,errors="coerce");q["week"]=pd.to_numeric(q.week,errors="coerce")
    q["team"]=q.team.astype(str).str.upper().str.strip();q["canonical_player_id"]=q.canonical_player_id.astype(str)
    for c in present:q[c]=pd.to_numeric(q[c],errors="coerce")
    q=q.dropna(subset=["season","week","team","canonical_player_id"]);q["season"]=q.season.astype(int);q["week"]=q.week.astype(int)
    dup=int(q.duplicated(list(PLAYER_FEATURE_KEYS),keep=False).sum());future=int((q.season>int(max_season)).sum()) if max_season is not None else 0;usable=q[present].notna().any(axis=1)
    status="ok" if dup==0 and future==0 and usable.any() else "invalid_point_in_time";reason="" if status=="ok" else f"duplicate_key_rows={dup}; future_rows={future}; usable={int(usable.sum())}"
    if dup:return pd.DataFrame(),SourceHealth(path or "",len(d),int(usable.sum()),tuple(present),dup,future,status,reason)
    return q.loc[usable].copy(),SourceHealth(path or "",len(d),int(usable.sum()),tuple(present),dup,future,status,reason)

def lag_player_features(df: pd.DataFrame, columns: Sequence[str], prefix: str = "premium_", windows: Sequence[int] = (4,8)) -> pd.DataFrame:
    """Convert realised player-week charting into leakage-safe pregame rolling priors."""
    if df.empty:return df
    d=df.sort_values(["canonical_player_id","season","week"]).copy();g=d.groupby(["canonical_player_id","season"],group_keys=False);out=d[list(PLAYER_FEATURE_KEYS)].copy()
    for c in columns:
        if c not in d:continue
        for w in windows:out[f"{prefix}{c}_prior{w}"]=g[c].transform(lambda x:pd.to_numeric(x,errors="coerce").shift(1).rolling(w,min_periods=max(1,min(2,w))).mean())
    return out

def lag_team_features(df: pd.DataFrame, columns: Sequence[str], prefix: str = "", window: int = 4) -> pd.DataFrame:
    """Convert realised team-week unit/charting values into leakage-safe pregame priors."""
    if df.empty:return df
    d=df.sort_values(["team","season","week"]).copy();g=d.groupby(["team","season"],group_keys=False);out=d[list(KEYS)].copy()
    for c in columns:
        if c in d:out[prefix+c]=g[c].transform(lambda x:pd.to_numeric(x,errors="coerce").shift(1).rolling(window,min_periods=2).mean())
    return out


@dataclass(frozen=True)
class SourceHealth:
    path: str
    rows: int
    usable_rows: int
    columns: tuple[str, ...]
    duplicate_keys: int
    future_key_rows: int
    status: str
    reason: str = ""


def _read(path: Optional[str]) -> pd.DataFrame:
    if not path:
        return pd.DataFrame()
    p = Path(path)
    if not p.exists():
        return pd.DataFrame()
    if p.suffix.lower() in {".json", ".jsonl"}:
        return pd.read_json(p, lines=p.suffix.lower() == ".jsonl")
    return pd.read_csv(p, low_memory=False)


def validate_team_source(path: Optional[str], allowed: Mapping[str, str], max_season: Optional[int] = None) -> tuple[pd.DataFrame, SourceHealth]:
    d = _read(path)
    if d.empty:
        return d, SourceHealth(path or "", 0, 0, (), 0, 0, "not_supplied", "optional source not supplied")
    missing = [k for k in KEYS if k not in d.columns]
    present = [c for c in allowed if c in d.columns]
    if missing or not present:
        reason = f"missing_keys={missing}; metric_columns={present}"
        return pd.DataFrame(), SourceHealth(path or "", len(d), 0, tuple(present), 0, 0, "invalid_schema", reason)
    q = d[list(KEYS) + present].copy()
    q["season"] = pd.to_numeric(q["season"], errors="coerce")
    q["week"] = pd.to_numeric(q["week"], errors="coerce")
    q["team"] = q["team"].astype(str).str.upper().str.strip()
    for c in present:
        q[c] = pd.to_numeric(q[c], errors="coerce")
    q = q.dropna(subset=["season", "week", "team"])
    q["season"] = q["season"].astype(int); q["week"] = q["week"].astype(int)
    dup = int(q.duplicated(list(KEYS), keep=False).sum())
    future = int((q.season > int(max_season)).sum()) if max_season is not None else 0
    usable = q[present].notna().any(axis=1)
    status = "ok" if dup == 0 and future == 0 and usable.any() else "invalid_point_in_time"
    reason = "" if status == "ok" else f"duplicate_key_rows={dup}; future_rows={future}; usable={int(usable.sum())}"
    if dup:
        # Duplicate team-week unit records require an explicit upstream aggregation.
        # FIE refuses to guess weights because that could mix player and unit grades.
        return pd.DataFrame(), SourceHealth(path or "", len(d), int(usable.sum()), tuple(present), dup, future, status, reason)
    return q.loc[usable].copy(), SourceHealth(path or "", len(d), int(usable.sum()), tuple(present), dup, future, status, reason)


def prefixed_optional(df: pd.DataFrame, prefix: str = "premium_") -> pd.DataFrame:
    if df.empty:
        return df
    return df.rename(columns={c: prefix + c for c in df.columns if c not in KEYS})

PLAYER_KEYS = ("season", "week", "team", "player_id")
PLAYER_TRENCH_COLUMNS = {
    "position_group": "OL_or_DL_role_label",
    "pass_block_snaps": "charted_player_workload",
    "run_block_snaps": "charted_player_workload",
    "pass_rush_snaps": "charted_player_workload",
    "ol_pass_block_win_rate": "charted_player_ol_pass_protection",
    "ol_pressure_allowed_rate": "charted_player_ol_pass_protection",
    "ol_quick_pressure_allowed_rate": "charted_player_ol_pass_protection",
    "ol_run_block_win_rate": "charted_player_ol_run_blocking",
    "ol_yards_before_contact_over_expected": "charted_player_ol_run_blocking",
    "dl_pass_rush_win_rate": "charted_player_dl_pass_rush",
    "dl_pressure_rate": "charted_player_dl_pass_rush",
    "dl_quick_pressure_rate": "charted_player_dl_pass_rush",
    "dl_run_stop_win_rate": "charted_player_dl_run_defense",
}


def validate_player_trench_source(path: Optional[str], max_season: Optional[int] = None) -> tuple[pd.DataFrame, SourceHealth]:
    """Validate player-week OL/DL grades without guessing unit aggregation weights."""
    d = _read(path)
    if d.empty:
        return d, SourceHealth(path or "", 0, 0, (), 0, 0, "not_supplied", "optional player trench source not supplied")
    missing = [k for k in PLAYER_KEYS if k not in d.columns]
    metric_cols = [c for c in PLAYER_TRENCH_COLUMNS if c in d.columns and c != "position_group"]
    if missing or not metric_cols:
        reason = f"missing_keys={missing}; metric_columns={metric_cols}"
        return pd.DataFrame(), SourceHealth(path or "", len(d), 0, tuple(metric_cols), 0, 0, "invalid_schema", reason)
    keep = list(PLAYER_KEYS) + (["position_group"] if "position_group" in d.columns else []) + metric_cols
    q = d[keep].copy()
    q["season"] = pd.to_numeric(q.season, errors="coerce"); q["week"] = pd.to_numeric(q.week, errors="coerce")
    q["team"] = q.team.astype(str).str.upper().str.strip(); q["player_id"] = q.player_id.astype(str)
    if "position_group" in q: q["position_group"] = q.position_group.astype(str).str.upper().str.strip()
    for c in metric_cols: q[c] = pd.to_numeric(q[c], errors="coerce")
    q = q.dropna(subset=["season", "week", "team", "player_id"]); q["season"] = q.season.astype(int); q["week"] = q.week.astype(int)
    dup = int(q.duplicated(list(PLAYER_KEYS), keep=False).sum())
    future = int((q.season > int(max_season)).sum()) if max_season is not None else 0
    usable = q[metric_cols].notna().any(axis=1)
    status = "ok" if dup == 0 and future == 0 and usable.any() else "invalid_point_in_time"
    reason = "" if status == "ok" else f"duplicate_key_rows={dup}; future_rows={future}; usable={int(usable.sum())}"
    if dup:
        return pd.DataFrame(), SourceHealth(path or "", len(d), int(usable.sum()), tuple(metric_cols), dup, future, status, reason)
    return q.loc[usable].copy(), SourceHealth(path or "", len(d), int(usable.sum()), tuple(metric_cols), dup, future, status, reason)


def aggregate_player_trenches_to_team(df: pd.DataFrame) -> pd.DataFrame:
    """Build auditable team OL/DL unit challengers from player grades.

    Workload-weighted means are used when the corresponding charted snap count exists.
    Otherwise the field is left unweighted and the caller exposes that limitation. A
    weakest-link statistic is exported separately rather than silently baked into the
    average, so validation can decide whether it helps.
    """
    if df.empty: return pd.DataFrame()
    rows = []
    ol_metrics = [c for c in ["ol_pass_block_win_rate","ol_pressure_allowed_rate","ol_quick_pressure_allowed_rate","ol_run_block_win_rate","ol_yards_before_contact_over_expected"] if c in df]
    dl_metrics = [c for c in ["dl_pass_rush_win_rate","dl_pressure_rate","dl_quick_pressure_rate","dl_run_stop_win_rate"] if c in df]
    for keys,g in df.groupby(["season","week","team"], sort=False):
        row={"season":int(keys[0]),"week":int(keys[1]),"team":str(keys[2])}
        for c in ol_metrics+dl_metrics:
            if c.startswith("ol_"):
                wcol = "pass_block_snaps" if ("pass" in c or "pressure" in c) else "run_block_snaps"
            else:
                wcol = "pass_rush_snaps" if ("pass" in c or "pressure" in c or "quick" in c) else None
            x=pd.to_numeric(g[c],errors="coerce")
            valid=x.notna()
            if not valid.any(): continue
            if wcol and wcol in g:
                w=pd.to_numeric(g[wcol],errors="coerce").fillna(0).clip(lower=0); ok=valid & w.gt(0)
                row[c]=float(np.average(x[ok],weights=w[ok])) if ok.any() and float(w[ok].sum())>0 else float(x[valid].mean())
            else: row[c]=float(x[valid].mean())
            # Win-rate low tail and allowed-rate high tail are explicit weakest-link challengers.
            if "win_rate" in c: row[c+"_weak_link"]=float(x[valid].quantile(.20))
            elif "allowed_rate" in c: row[c+"_weak_link"]=float(x[valid].quantile(.80))
        row["player_trench_rows"]=int(len(g)); rows.append(row)
    return pd.DataFrame(rows)
