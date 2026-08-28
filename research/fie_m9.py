#!/usr/bin/env python3
"""FIE V9.4-M9 returner intelligence and projection-distribution calibration.

M9 keeps two contracts separate:
1. Return work produces raw football outcomes (KR/PR opportunities, yards, TDs).
   Fantasy scoring is applied only after those outcomes exist and only for scoring
   keys present in the league profile.
2. Projection uncertainty is calibrated from historical out-of-sample FIE errors.
   P10/P25/P50/P75/P90 are therefore empirical simulation outputs, never a fixed
   percentage around a point estimate.

Returner history is reconstructed from nflverse play-by-play when available.  No
returner is inferred from depth-chart labels alone.  A deterministic synthetic
return history exists only for --fixture integrity testing.
"""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import brier_score_loss, mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from fie_research import CONTROL_BUILD, LATEST_COMPLETED_SEASON, SourceManager
from fie_m2 import FOLDS
from fie_m4 import feature_frame
from fie_m7 import OFFENSE_POSITIONS, load_oos, load_json
from statistical_guardrails import promotion_gate
from preseason_projection import validate_preseason, write_latest_profiles

RESEARCH_BUILD = "V9.4-M9"
MILESTONE = "M9"
RETURN_POSITIONS = {"RB", "WR", "TE"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_safe(value):
    """Recursively convert non-finite research diagnostics to strict JSON null.

    This is an artifact-boundary conversion only. It does not impute model inputs,
    change validation gates, or turn missing football information into zero.
    """
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    return value


def _num(s, default=np.nan):
    if isinstance(s, pd.Series):
        return pd.to_numeric(s, errors="coerce")
    return pd.Series(default, dtype=float)


def _first(df: pd.DataFrame, names: Sequence[str]) -> Optional[str]:
    for n in names:
        if n in df.columns:
            return n
    return None


def _safe_quantile(x: pd.Series, q: float) -> Optional[float]:
    y = pd.to_numeric(x, errors="coerce").dropna()
    return None if y.empty else float(y.quantile(q))


def _pbp_return_rows(pbp: pd.DataFrame) -> pd.DataFrame:
    """Reduce PBP to one player/team/week row of raw return outcomes."""
    if pbp is None or pbp.empty or "season" not in pbp or "week" not in pbp:
        return pd.DataFrame()
    p = pbp.copy()
    if "season_type" in p:
        p = p[p.season_type.astype(str).str.upper().str.startswith("REG")]
    play_type = p.get("play_type", pd.Series("", index=p.index)).fillna("").astype(str).str.lower()
    ret_yards = pd.to_numeric(p.get("return_yards", 0), errors="coerce").fillna(0.0)
    return_team = p.get("return_team", pd.Series(None, index=p.index))

    frames: List[pd.DataFrame] = []
    for kind, mask, ids in [
        ("KR", play_type.eq("kickoff"), ["kickoff_returner_player_id", "return_player_id", "returner_player_id"]),
        ("PR", play_type.eq("punt"), ["punt_returner_player_id", "return_player_id", "returner_player_id"]),
    ]:
        idc = _first(p, ids)
        if idc is None:
            continue
        q = p[mask & p[idc].notna()].copy()
        if q.empty:
            continue
        q["canonical_player_id"] = q[idc].astype(str)
        q["team"] = return_team.loc[q.index].astype(str) if return_team is not None else ""
        q["return_yards"] = ret_yards.loc[q.index]
        td = pd.to_numeric(q.get("touchdown", 0), errors="coerce").fillna(0).gt(0)
        td_team = q.get("td_team", pd.Series("", index=q.index)).fillna("").astype(str)
        q["return_td"] = (td & (td_team.eq(q["team"]) | td_team.eq(""))).astype(int)
        q["return_attempt"] = 1
        q["return_type"] = kind
        frames.append(q[["season", "week", "team", "canonical_player_id", "return_type", "return_attempt", "return_yards", "return_td"]])
    if not frames:
        return pd.DataFrame()
    z = pd.concat(frames, ignore_index=True)
    z["season"] = pd.to_numeric(z.season, errors="coerce")
    z["week"] = pd.to_numeric(z.week, errors="coerce")
    return z.groupby(["season", "week", "team", "canonical_player_id", "return_type"], as_index=False).agg(
        return_attempts=("return_attempt", "sum"), return_yards=("return_yards", "sum"), return_tds=("return_td", "sum")
    )


def load_return_history(args, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
    """Load point-in-time individual return history; fixture synthesis is explicit."""
    if args.fixture:
        rows: List[dict] = []
        p = df[df.position_model.isin(RETURN_POSITIONS)][["season", "week", "team", "canonical_player_id", "position_model"]].copy()
        for (season, week, team), g in p.groupby(["season", "week", "team"], sort=False):
            # deterministic candidate ordering; only the first two skill players can return
            g = g.sort_values("canonical_player_id")
            for j, r in enumerate(g.head(2).itertuples(index=False)):
                if (int(week) + j + len(str(r.canonical_player_id))) % 3 == 0:
                    continue
                attempts = 2 if j == 0 else 1
                rows.append({"season": int(season), "week": int(week), "team": team,
                             "canonical_player_id": str(r.canonical_player_id), "return_type": "KR",
                             "return_attempts": attempts, "return_yards": float(attempts * (21 + (int(week) % 7))),
                             "return_tds": int((int(week) + j) % 31 == 0)})
                if j == 0 and int(week) % 2 == 0:
                    rows.append({"season": int(season), "week": int(week), "team": team,
                                 "canonical_player_id": str(r.canonical_player_id), "return_type": "PR",
                                 "return_attempts": 1, "return_yards": float(6 + int(week) % 9), "return_tds": 0})
        return pd.DataFrame(rows), {"status": "fixture_only", "rows": len(rows), "source": "deterministic_synthetic_pbp_returns"}

    sm = SourceManager(Path(args.cache_dir))
    frames = []
    for season in args.seasons:
        pbp = sm.load("pbp", int(season), required=False)
        if not pbp.empty:
            q = _pbp_return_rows(pbp)
            if not q.empty:
                frames.append(q)
    out = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return out, {
        "status": "ok" if not out.empty else "blocked_missing_pbp_return_history",
        "rows": int(len(out)), "source": "nflverse_pbp", "source_status": [x.__dict__ for x in sm.status],
    }


def build_return_panel(df: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Create a candidate panel with strictly lagged return-role features."""
    base = df[df.position_model.isin(RETURN_POSITIONS)][[
        "season", "week", "team", "canonical_player_id", "full_name", "position_model"
    ] + (["offense_snap_share"] if "offense_snap_share" in df else [])].drop_duplicates(
        ["season", "week", "team", "canonical_player_id"]
    ).copy()
    if base.empty:
        return base
    if returns.empty:
        for c in ["kr_att", "kr_yd", "kr_td", "pr_att", "pr_yd", "pr_td"]:
            base[c] = 0.0
    else:
        r = returns.copy()
        piv = r.pivot_table(index=["season", "week", "team", "canonical_player_id"], columns="return_type",
                            values=["return_attempts", "return_yards", "return_tds"], aggfunc="sum", fill_value=0)
        piv.columns = [f"{b}_{a}" for a, b in piv.columns]
        piv = piv.reset_index().rename(columns={
            "KR_return_attempts": "kr_att", "KR_return_yards": "kr_yd", "KR_return_tds": "kr_td",
            "PR_return_attempts": "pr_att", "PR_return_yards": "pr_yd", "PR_return_tds": "pr_td",
        })
        base = base.merge(piv, on=["season", "week", "team", "canonical_player_id"], how="left")
        for c in ["kr_att", "kr_yd", "kr_td", "pr_att", "pr_yd", "pr_td"]:
            if c not in base: base[c] = 0.0
            base[c] = pd.to_numeric(base[c], errors="coerce").fillna(0.0)

    base["return_att"] = base.kr_att + base.pr_att
    base["return_yd"] = base.kr_yd + base.pr_yd
    base["return_td"] = base.kr_td + base.pr_td
    team = base.groupby(["season", "week", "team"], as_index=False).return_att.sum().rename(columns={"return_att": "team_return_att"})
    base = base.merge(team, on=["season", "week", "team"], how="left")
    base["return_share"] = np.where(base.team_return_att > 0, base.return_att / base.team_return_att, 0.0)
    base["primary_returner"] = ((base.return_share >= .50) & (base.return_att >= 1)).astype(int)
    base["return_ypr"] = np.where(base.return_att > 0, base.return_yd / base.return_att, np.nan)
    base = base.sort_values(["canonical_player_id", "season", "week"]).copy()
    g = base.groupby(["canonical_player_id", "season"], group_keys=False)
    for c in ["return_share", "return_att", "return_ypr", "return_td"]:
        base[f"{c}_prior4"] = g[c].transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())
        base[f"{c}_prior8"] = g[c].transform(lambda s: s.shift(1).rolling(8, min_periods=1).mean())
    if "offense_snap_share" in base:
        base["offense_snap_share_prior4_return"] = g["offense_snap_share"].transform(lambda s: pd.to_numeric(s, errors="coerce").shift(1).rolling(4, min_periods=1).mean())
    else:
        base["offense_snap_share_prior4_return"] = np.nan
    tg = base.groupby(["team", "season"], group_keys=False)
    base["team_return_att_prior4"] = tg.team_return_att.transform(lambda s: s.shift(1).rolling(4, min_periods=1).mean())
    return base


def validate_return_role(panel: pd.DataFrame) -> Tuple[List[dict], dict]:
    features = ["return_share_prior4", "return_share_prior8", "return_att_prior4", "return_ypr_prior4",
                "return_td_prior8", "offense_snap_share_prior4_return", "team_return_att_prior4"]
    rows = []
    if panel.empty or panel.primary_returner.nunique() < 2:
        return rows, {"status": "diagnostic_only", "reason": "insufficient_return_history", "folds": 0}
    for train_seasons, test_season in FOLDS:
        tr = panel[panel.season.isin(train_seasons)].copy()
        te = panel[panel.season.eq(test_season)].copy()
        if len(tr) < 150 or len(te) < 40 or tr.primary_returner.nunique() < 2:
            continue
        m = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()),
                      ("model", LogisticRegression(C=.25, max_iter=500, class_weight="balanced"))])
        m.fit(tr[features], tr.primary_returner)
        prob = np.clip(m.predict_proba(te[features])[:, 1], .001, .999)
        baseline = np.clip(pd.to_numeric(te.return_share_prior4, errors="coerce").fillna(0).to_numpy(float), .001, .999)
        y = te.primary_returner.to_numpy(int)
        mb, bb = float(brier_score_loss(y, prob)), float(brier_score_loss(y, baseline))
        imp = (bb - mb) / bb if bb > 0 else None
        rows.append({"test_season": int(test_season), "n_test": int(len(te)), "model_brier": mb,
                     "persistence_brier": bb, "incremental_brier_improvement": imp})
    if not rows:
        return rows, {"status": "diagnostic_only", "reason": "insufficient_chronological_folds", "folds": 0}
    vals = [r["incremental_brier_improvement"] for r in rows if r["incremental_brier_improvement"] is not None]
    weights = [r["n_test"] for r in rows if r["incremental_brier_improvement"] is not None]
    gate = promotion_gate(vals, weights=weights, min_mean=.01, min_folds=4, require_positive_ci=True)
    return rows, {"status": "validated_candidate" if gate["robust"] else "diagnostic_only", "folds": len(rows),
                  "mean_incremental_brier_improvement": float(np.mean(vals)) if vals else None,
                  "bootstrap_ci95_low": gate["ci95_low"], "bootstrap_ci95_high": gate["ci95_high"]}


def validate_return_yards(panel: pd.DataFrame) -> Tuple[List[dict], dict]:
    """Validate raw return-yards expectation against a lagged persistence baseline."""
    rows = []
    if panel.empty:
        return rows, {"status": "diagnostic_only", "reason": "insufficient_return_history", "folds": 0}
    features = ["return_share_prior4", "return_att_prior4", "return_ypr_prior4", "return_share_prior8",
                "return_ypr_prior8", "team_return_att_prior4", "offense_snap_share_prior4_return"]
    for train_seasons, test_season in FOLDS:
        tr = panel[panel.season.isin(train_seasons)].copy()
        te = panel[panel.season.eq(test_season)].copy()
        if len(tr) < 150 or len(te) < 40:
            continue
        model = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=12.0))])
        model.fit(tr[features], tr.return_yd)
        pred = np.maximum(0.0, model.predict(te[features]))
        baseline = np.maximum(0.0, pd.to_numeric(te.return_att_prior4, errors="coerce").fillna(0).to_numpy(float) *
                              pd.to_numeric(te.return_ypr_prior4, errors="coerce").fillna(0).to_numpy(float))
        y = te.return_yd.to_numpy(float)
        ma, ba = float(mean_absolute_error(y, pred)), float(mean_absolute_error(y, baseline))
        rows.append({"test_season": int(test_season), "n_test": int(len(te)), "model_mae": ma,
                     "persistence_mae": ba, "incremental_mae_improvement": (ba - ma) / ba if ba > 0 else None})
    vals = [r["incremental_mae_improvement"] for r in rows if r.get("incremental_mae_improvement") is not None]
    weights = [r["n_test"] for r in rows if r.get("incremental_mae_improvement") is not None]
    if not vals:
        return rows, {"status": "diagnostic_only", "reason": "insufficient_chronological_folds", "folds": len(rows)}
    gate = promotion_gate(vals, weights=weights, min_mean=.01, min_folds=4, require_positive_ci=True)
    return rows, {"status": "validated_candidate" if gate["robust"] else "diagnostic_only", "folds": len(rows),
                  "mean_incremental_mae_improvement": float(np.mean(vals)),
                  "bootstrap_ci95_low": gate["ci95_low"], "bootstrap_ci95_high": gate["ci95_high"]}



def _serialize_return_models(panel: pd.DataFrame, role_agg: dict, yard_agg: dict) -> dict:
    features = ["return_share_prior4", "return_share_prior8", "return_att_prior4", "return_ypr_prior4",
                "return_td_prior8", "offense_snap_share_prior4_return", "team_return_att_prior4"]
    specs = {}
    z = panel.copy()
    if role_agg.get("status") == "validated_candidate" and len(z) >= 150 and z.primary_returner.nunique() >= 2:
        pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()),
                         ("model", LogisticRegression(C=.25, max_iter=500, class_weight="balanced"))])
        pipe.fit(z[features], z.primary_returner)
        imp, sc, mod = pipe.named_steps["impute"], pipe.named_steps["scale"], pipe.named_steps["model"]
        specs["returner_role"] = {
            "features": features, "imputer_medians": [float(x) for x in imp.statistics_],
            "scaler_mean": [float(x) for x in sc.mean_], "scaler_scale": [float(x) for x in sc.scale_],
            "coefficients": [float(x) for x in mod.coef_[0]], "intercept": float(mod.intercept_[0]),
            "link": "logit", "n_train": int(len(z)), "gate": role_agg,
        }
    yfeatures = ["return_share_prior4", "return_att_prior4", "return_ypr_prior4", "return_share_prior8",
                 "return_ypr_prior8", "team_return_att_prior4", "offense_snap_share_prior4_return"]
    if yard_agg.get("status") == "validated_candidate" and len(z) >= 150:
        pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=12.0))])
        pipe.fit(z[yfeatures], z.return_yd)
        imp, sc, mod = pipe.named_steps["impute"], pipe.named_steps["scale"], pipe.named_steps["ridge"]
        specs["return_yards"] = {
            "features": yfeatures, "imputer_medians": [float(x) for x in imp.statistics_],
            "scaler_mean": [float(x) for x in sc.mean_], "scaler_scale": [float(x) for x in sc.scale_],
            "coefficients": [float(x) for x in mod.coef_], "intercept": float(mod.intercept_),
            "prediction_floor": 0.0, "n_train": int(len(z)), "gate": yard_agg,
        }
    return specs



def return_season_frame(panel: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Build prior-season -> next-season return projection rows.

    The model intentionally needs an NFL return history for the player.  New/rookie
    returners therefore remain unmodelled until a separate preseason/depth-chart
    source is supplied rather than being guessed from nominal roster position.
    """
    if panel.empty:
        return pd.DataFrame(), pd.DataFrame()
    d = panel.copy()
    rows = []
    for (pid, season), g in d.groupby(["canonical_player_id", "season"], sort=False):
        games = max(1, int(pd.to_numeric(g.week, errors="coerce").nunique()))
        team_mode = g.team.dropna().astype(str).mode()
        pos_mode = g.position_model.dropna().astype(str).mode()
        rec = {
            "canonical_player_id": str(pid), "season": int(season),
            "profile_team": str(team_mode.iloc[0]) if len(team_mode) else None,
            "position_model": str(pos_mode.iloc[0]) if len(pos_mode) else None,
            "prev_games": games,
            "prev_return_att_pg": float(pd.to_numeric(g.return_att, errors="coerce").fillna(0).sum() / games),
            "prev_return_share": float(pd.to_numeric(g.return_share, errors="coerce").fillna(0).mean()),
            "prev_primary_rate": float(pd.to_numeric(g.primary_returner, errors="coerce").fillna(0).mean()),
            "prev_return_td_pg": float(pd.to_numeric(g.return_td, errors="coerce").fillna(0).sum() / games),
            "prev_offense_snap_share": float(pd.to_numeric(g.get("offense_snap_share", pd.Series(index=g.index, dtype=float)), errors="coerce").mean()) if len(g) else np.nan,
        }
        for c in ["kr_yd", "pr_yd", "kr_td", "pr_td"]:
            rec[f"prev_{c}_pg"] = float(pd.to_numeric(g[c], errors="coerce").fillna(0).sum() / games)
        rows.append(rec)
    season = pd.DataFrame(rows)
    if season.empty:
        return pd.DataFrame(), pd.DataFrame()
    current = season.copy().rename(columns={"season": "target_season"})
    prev = season.copy(); prev["target_season"] = prev.season + 1
    keep = [c for c in prev.columns if c != "season"]
    supervised = current[["canonical_player_id", "target_season", "profile_team", "position_model"]].merge(
        prev[keep], on=["canonical_player_id", "target_season"], how="inner", suffixes=("_target", "")
    )
    # Actual next-season targets come from the target-season aggregate.
    actual = season.rename(columns={
        "season": "target_season", "profile_team": "target_team", "position_model": "target_position",
        **{f"prev_{c}_pg": f"target_{c}_pg" for c in ["kr_yd", "pr_yd", "kr_td", "pr_td"]},
    })
    supervised = supervised.merge(
        actual[["canonical_player_id", "target_season", "target_team", "target_position"] + [f"target_{c}_pg" for c in ["kr_yd", "pr_yd", "kr_td", "pr_td"]]],
        on=["canonical_player_id", "target_season"], how="left"
    )
    latest_season = int(season.season.max())
    latest = season[season.season.eq(latest_season)].drop(columns=["season"]).copy()
    latest["profile_season"] = latest_season
    return supervised, latest


def _serialize_return_season_target(z: pd.DataFrame, features: List[str], target: str) -> Optional[dict]:
    q = z.dropna(subset=[target]).copy()
    if len(q) < 100:
        return None
    pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=15.0))])
    pipe.fit(q[features], q[target])
    imp, sc, mod = pipe.named_steps["impute"], pipe.named_steps["scale"], pipe.named_steps["ridge"]
    return {
        "features": features, "imputer_medians": [float(x) for x in imp.statistics_],
        "scaler_mean": [float(x) for x in sc.mean_], "scaler_scale": [float(x) for x in sc.scale_],
        "coefficients": [float(x) for x in mod.coef_], "intercept": float(mod.intercept_),
        "prediction_floor": 0.0, "n_train": int(len(q)), "target": target.replace("target_", "").replace("_pg", ""),
        "unit": "per_game_raw_return_outcome",
    }


def validate_return_season(panel: pd.DataFrame) -> dict:
    """Validate return yards/TDs as next-season raw outcomes independently by target."""
    z, latest = return_season_frame(panel)
    targets = ["kr_yd", "pr_yd", "kr_td", "pr_td"]
    folds, aggregate, specs = [], {}, {}
    if z.empty:
        return {"folds": [], "aggregate": {}, "model_specs": {}, "latest_profiles": [], "status": "diagnostic_only"}
    base_features = ["prev_return_att_pg", "prev_return_share", "prev_primary_rate", "prev_return_td_pg", "prev_games", "prev_offense_snap_share"]
    for raw in targets:
        target = f"target_{raw}_pg"; own = f"prev_{raw}_pg"; features = [own] + base_features
        target_rows = []
        for train_seasons, test_season in FOLDS:
            tr = z[z.target_season.isin(train_seasons)].copy(); te = z[z.target_season.eq(test_season)].copy()
            if len(tr) < 100 or len(te) < 25:
                continue
            pipe = Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=15.0))])
            pipe.fit(tr[features], tr[target])
            pred = np.maximum(0.0, pipe.predict(te[features]))
            baseline = np.maximum(0.0, pd.to_numeric(te[own], errors="coerce").fillna(0).to_numpy(float))
            y = pd.to_numeric(te[target], errors="coerce").fillna(0).to_numpy(float)
            ma, ba = float(mean_absolute_error(y, pred)), float(mean_absolute_error(y, baseline))
            target_rows.append({"target": raw, "test_season": int(test_season), "n_test": int(len(te)),
                                "model_mae": ma, "persistence_mae": ba,
                                "incremental_mae_improvement": (ba-ma)/ba if ba > 0 else None})
        folds.extend(target_rows)
        vals = [r["incremental_mae_improvement"] for r in target_rows if r.get("incremental_mae_improvement") is not None]
        weights = [r["n_test"] for r in target_rows if r.get("incremental_mae_improvement") is not None]
        gate = promotion_gate(vals, weights=weights, min_mean=.01, min_folds=4, require_positive_ci=True) if vals else {"robust": False, "ci95_low": None, "ci95_high": None}
        agg = {"target": raw, "status": "validated_candidate" if gate.get("robust") else "diagnostic_only",
               "folds": len(target_rows), "mean_incremental_mae_improvement": float(np.mean(vals)) if vals else None,
               "bootstrap_ci95_low": gate.get("ci95_low"), "bootstrap_ci95_high": gate.get("ci95_high")}
        aggregate[raw] = agg
        if agg["status"] == "validated_candidate":
            spec = _serialize_return_season_target(z, features, target)
            if spec:
                spec["gate"] = agg; specs[raw] = spec
    return {"folds": folds, "aggregate": aggregate, "model_specs": specs,
            "latest_profiles": latest.replace({np.nan: None}).to_dict("records") if not latest.empty else [],
            "status": "validated_candidate" if specs else "diagnostic_only",
            "rule": "Each KR/PR yards/TD raw outcome has an independent prior-season -> next-season gate; unsupported targets remain zero-impact."}

def projection_calibration(oos: pd.DataFrame) -> Dict[str, dict]:
    """Calibrate empirical weekly FIE errors by position using OOS rows only."""
    out: Dict[str, dict] = {}
    z = oos.copy()
    z["residual"] = pd.to_numeric(z.fantasy_points, errors="coerce") - pd.to_numeric(z.fie_projection, errors="coerce")
    z["abs_residual"] = z.residual.abs()
    for pos in OFFENSE_POSITIONS:
        q = z[z.position_model.eq(pos)].dropna(subset=["residual"]).copy()
        if len(q) < 30:
            continue
        out[pos] = {
            "n_oos": int(len(q)), "residual_mean": float(q.residual.mean()), "residual_std": float(q.residual.std(ddof=1)),
            "residual_mad": float(q.abs_residual.median()),
            "q10": _safe_quantile(q.residual, .10), "q25": _safe_quantile(q.residual, .25),
            "q50": _safe_quantile(q.residual, .50), "q75": _safe_quantile(q.residual, .75), "q90": _safe_quantile(q.residual, .90),
            "method": "empirical_out_of_sample_weekly_residuals",
        }
    return out


def simulate_player_season(weekly_mean: float, games: int, calibration: dict, n: int = 10000,
                           seed: int = 94, active_probability: float = 1.0,
                           weekly_means: Optional[Sequence[float]] = None) -> dict:
    """Deterministic-seed empirical season simulation for report/runtime consumers."""
    rng = np.random.default_rng(seed)
    means = np.array(list(weekly_means), dtype=float) if weekly_means is not None else np.repeat(float(weekly_mean), int(games))
    if means.size == 0:
        return {"mean": 0.0, "p10": 0.0, "p25": 0.0, "p50": 0.0, "p75": 0.0, "p90": 0.0, "n": int(n)}
    std = max(float(calibration.get("residual_std") or 0.0), .01)
    center = float(calibration.get("residual_mean") or 0.0)
    # Use Student-t tails to avoid pretending weekly NFL outcomes are Gaussian.
    noise = center + rng.standard_t(df=6, size=(int(n), means.size)) * std * math.sqrt((6 - 2) / 6)
    active = rng.random((int(n), means.size)) < float(np.clip(active_probability, 0, 1))
    draws = np.maximum(0.0, means.reshape(1, -1) + noise) * active
    season = draws.sum(axis=1)
    qs = np.quantile(season, [.10, .25, .50, .75, .90])
    return {"mean": float(season.mean()), "p10": float(qs[0]), "p25": float(qs[1]), "p50": float(qs[2]),
            "p75": float(qs[3]), "p90": float(qs[4]), "n": int(n), "games": int(means.size),
            "active_probability": float(active_probability)}


RETURN_SCORING_ALIASES = {
    "kr_yd": "kr_yd", "pr_yd": "pr_yd", "kr_td": "kr_td", "pr_td": "pr_td",
    "ret_yd": "return_yd", "ret_td": "return_td",
}


def score_return_stats(raw: dict, scoring: dict) -> dict:
    """Apply only explicit Sleeper-style return scoring keys; never guess unsupported keys."""
    points = 0.0; supported = []; unsupported = []
    for key, weight in (scoring or {}).items():
        if key not in RETURN_SCORING_ALIASES:
            continue
        try: w = float(weight)
        except Exception: continue
        field = RETURN_SCORING_ALIASES[key]
        if field in raw:
            points += float(raw.get(field, 0) or 0) * w; supported.append(key)
        else:
            unsupported.append(key)
    return {"points": float(points), "supported_keys": sorted(supported), "unsupported_keys": sorted(unsupported),
            "exact_for_active_return_keys": not unsupported}


def write_return_panel(panel: pd.DataFrame, derived_dir: str) -> Optional[str]:
    if panel.empty or not derived_dir:
        return None
    p = Path(derived_dir) / "m9_returner_history.csv.gz"; p.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(p, index=False, compression="gzip"); return str(p)


def run(args) -> dict:
    df, team, identity, m1_core, m2_core, enrichment = feature_frame(args)
    m1 = load_json(args.m1_bundle) or m1_core
    m8 = load_json(args.m8_bundle)
    oos = load_oos(args.derived_dir, args.fixture, df)
    returns, source = load_return_history(args, df)
    panel = build_return_panel(df, returns)
    role_folds, role_agg = validate_return_role(panel)
    yard_folds, yard_agg = validate_return_yards(panel)
    return_season = validate_return_season(panel)
    calibration = projection_calibration(oos)
    preseason = validate_preseason(df, m1.get("scoring", {}).get("settings", {}))
    preseason_profile_path = write_latest_profiles(preseason.get("latest_profiles", []), args.derived_dir)
    return_specs = _serialize_return_models(panel, role_agg, yard_agg)
    derived_path = write_return_panel(panel, args.derived_dir)
    validated = [name for name, agg in [("returner_role", role_agg), ("return_yards", yard_agg)] if agg.get("status") == "validated_candidate"]
    return {
        "schema_version": 9, "milestone": MILESTONE, "control_build": CONTROL_BUILD, "research_build": RESEARCH_BUILD,
        "generated_at": utc_now(), "status": "complete", "steps_completed": [38, 39, 40, 41],
        "scoring_signature": m8.get("scoring_signature") or m1.get("scoring", {}).get("signature"),
        "methodology": {
            "step38": "Reconstruct individual KR/PR opportunities, yards and TDs from point-in-time PBP. Returner status is a probabilistic role, not a depth-chart label.",
            "step39": "Validate primary-returner probability and weekly return-yard expectation chronologically, plus independent prior-season -> next-season KR/PR yard and TD targets. Raw football outcomes remain separate from fantasy scoring.",
            "step40": "Calibrate position-specific uncertainty from historical M4 out-of-sample FIE residuals; no fixed floor/ceiling percentage is used.",
            "step41": "Validate a separate prior-season -> next-season raw-stat projection by target season, then expose seeded P10/P25/P50/P75/P90 simulation. The weekly model is never multiplied across 17 games.",
        },
        "returner_intelligence": {
            "source": source, "panel_rows": int(len(panel)), "derived_table": derived_path,
            "role_validation": {"folds": role_folds, "aggregate": role_agg},
            "yard_validation": {"folds": yard_folds, "aggregate": yard_agg},
            "validated_candidates": validated,
            "model_specs": return_specs,
            "activation_status": "MODEL_SPEC_AVAILABLE" if return_specs else "DIAGNOSTIC_ONLY_UNTIL_CONSUMER_GATE",
            "raw_outcomes": ["kr_att", "kr_yd", "kr_td", "pr_att", "pr_yd", "pr_td"],
            "scoring_bridge": {"supported_explicit_keys": sorted(RETURN_SCORING_ALIASES),
                               "rule": "Return production changes fantasy rank only when the league scoring profile contains a supported nonzero return key."},
            "season_projection": return_season,
        },
        "preseason_season_projection": {
            **preseason,
            "latest_profiles_derived_table": preseason_profile_path,
            "scoring_rule": "Models predict per-game raw football outcomes first; the league scoring settings are applied afterwards.",
            "rollover_rule": "The weekly same-season model is never multiplied across a preseason schedule. Year-to-year portability has its own chronological gate.",
        },
        "projection_distribution": {
            "status": "calibrated_from_oos" if calibration else "blocked_missing_oos",
            "position_calibration": calibration,
            "quantiles": ["p10", "p25", "p50", "p75", "p90"],
            "simulation": "research/fie_m9.py::simulate_player_season",
            "availability_semantics": "conditional projections and availability-adjusted season totals remain separate",
        },
        "market_report_contract": {
            "status": "ready_for_current_market_snapshot",
            "universe": {"QB": 24, "RB": 36, "WR": 36, "TE": 24},
            "sleepers": {"QB": 5, "RB": 10, "WR": 10, "TE": 5},
            "rule": "Market universe is frozen first; raw football projections are computed once; league scoring and scarcity are applied afterward.",
        },
        "upstream": {"m1_status": m1.get("status"), "m8_status": m8.get("status")},
        "limitations": [
            "PBP returner IDs are authoritative only when present; missing historical IDs are not filled from nominal depth charts.",
            "A returner model does not activate fantasy value in leagues that do not score individual return production.",
            "Position residual calibration describes projection uncertainty, not injury probability. Availability is an explicit separate input.",
            "M9 calibrates marginal player uncertainty. Fully correlated game simulation is intentionally downstream so teammate/opponent dependence is modelled once rather than double counted.",
        ],
    }


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build FIE M9 returner and season-distribution research")
    p.add_argument("--derived-dir", default="data/research/derived")
    for n in range(1, 9): p.add_argument(f"--m{n}-bundle", default=f"data/research/milestone{n}.json")
    p.add_argument("--cache-dir", default=".cache/fie-research")
    p.add_argument("--seasons", default=f"2019-{LATEST_COMPLETED_SEASON}")
    p.add_argument("--output", default="data/research/milestone9.json")
    p.add_argument("--fixture", action="store_true")
    a = p.parse_args(argv)
    if isinstance(a.seasons, str):
        lo, hi = map(int, a.seasons.split("-")); a.seasons = list(range(lo, hi + 1))
    return a


def main(argv=None):
    args = parse_args(argv); bundle = run(args)
    out = Path(args.output); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(json_safe(bundle), indent=2, allow_nan=False))
    print(f"Wrote {out} status={bundle['status']} validated={len(bundle['returner_intelligence']['validated_candidates'])}")


if __name__ == "__main__":
    main()
