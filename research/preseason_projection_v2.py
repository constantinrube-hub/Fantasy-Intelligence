#!/usr/bin/env python3
"""FIE V9.7 component-first preseason / next-season research challenger.

This module is intentionally additive to M9's preseason_projection.py.  It reuses the
same historical player-week backbone and exact league scoring function, but asks the
question in the order supported by M7/V9.6 evidence:

    prior role -> next-season football volume -> conversion/efficiency -> fantasy PPG

The module never consumes ADP or Sleeper season projections.  Market information stays
outside the football model so later FIE-vs-market disagreement remains independent.
Production activation is fail-closed and requires four chronological folds plus the
standard FIE promotion gate.  A diagnostic model spec may be serialized even when the
gate does not clear; diagnostic existence never grants runtime rights.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_research import BONUS_RULES, score_rows, scoring_audit
from statistical_guardrails import promotion_gate

BUILD = "V9.7.1-PRESEASON-COMPONENTS-FUMBLE-REPLAY-1"
POSITIONS = ("QB", "RB", "WR", "TE")

RAW_TARGETS: Dict[str, Dict[str, Sequence[str]]] = {
    "QB": {
        "passing_attempts": ("passing_attempts", "attempts"),
        "completions": ("completions",),
        "passing_yards": ("passing_yards",),
        "passing_tds": ("passing_tds",),
        "interceptions": ("interceptions", "passing_interceptions"),
        "passing_2pt_conversions": ("passing_2pt_conversions",),
        "passing_first_downs": ("passing_first_downs",),
        "rushing_attempts": ("carries", "rushing_attempts"),
        "rushing_yards": ("rushing_yards",),
        "rushing_tds": ("rushing_tds",),
        "rushing_2pt_conversions": ("rushing_2pt_conversions",),
        "rushing_first_downs": ("rushing_first_downs",),
        "fumbles": ("fumbles",),
        "fumbles_lost": ("fumbles_lost",),
    },
    "RB": {
        "rushing_attempts": ("carries", "rushing_attempts"),
        "rushing_yards": ("rushing_yards",),
        "rushing_tds": ("rushing_tds",),
        "rushing_2pt_conversions": ("rushing_2pt_conversions",),
        "rushing_first_downs": ("rushing_first_downs",),
        "targets": ("targets",),
        "receptions": ("receptions",),
        "receiving_yards": ("receiving_yards",),
        "receiving_tds": ("receiving_tds",),
        "receiving_2pt_conversions": ("receiving_2pt_conversions",),
        "receiving_first_downs": ("receiving_first_downs",),
        "fumbles": ("fumbles",),
        "fumbles_lost": ("fumbles_lost",),
    },
    "WR": {
        "rushing_attempts": ("carries", "rushing_attempts"),
        "rushing_yards": ("rushing_yards",),
        "rushing_tds": ("rushing_tds",),
        "rushing_2pt_conversions": ("rushing_2pt_conversions",),
        "rushing_first_downs": ("rushing_first_downs",),
        "targets": ("targets",),
        "receptions": ("receptions",),
        "receiving_yards": ("receiving_yards",),
        "receiving_tds": ("receiving_tds",),
        "receiving_2pt_conversions": ("receiving_2pt_conversions",),
        "receiving_first_downs": ("receiving_first_downs",),
        "fumbles": ("fumbles",),
        "fumbles_lost": ("fumbles_lost",),
    },
    "TE": {
        "rushing_attempts": ("carries", "rushing_attempts"),
        "rushing_yards": ("rushing_yards",),
        "rushing_tds": ("rushing_tds",),
        "rushing_2pt_conversions": ("rushing_2pt_conversions",),
        "rushing_first_downs": ("rushing_first_downs",),
        "targets": ("targets",),
        "receptions": ("receptions",),
        "receiving_yards": ("receiving_yards",),
        "receiving_tds": ("receiving_tds",),
        "receiving_2pt_conversions": ("receiving_2pt_conversions",),
        "receiving_first_downs": ("receiving_first_downs",),
        "fumbles": ("fumbles",),
        "fumbles_lost": ("fumbles_lost",),
    },
}

# Feature semantics are deliberately compact and mechanism-based.  Every item is an
# end-of-season profile known before the following season.  Missing features stay
# missing and are handled by the train-fold imputer rather than filled with zero.
POSITION_SCORING_KEYS = {
    "QB": {"pass_yd","pass_td","pass_int","pass_cmp","pass_att","pass_2pt","pass_fd","rush_yd","rush_td","rush_att","rush_2pt","rush_fd","fum","fum_lost","bonus_pass_yd_300","bonus_pass_yd_400","bonus_rush_yd_100","bonus_rush_yd_200"},
    "RB": {"rush_yd","rush_td","rush_att","rush_2pt","rush_fd","rec","rec_yd","rec_td","rec_tgt","rec_2pt","rec_fd","fum_lost","bonus_rush_yd_100","bonus_rush_yd_200","bonus_rec_yd_100","bonus_rec_yd_200","bonus_rec_rb","rec_rb","fum"},
    "WR": {"rush_yd","rush_td","rush_att","rush_2pt","rush_fd","rec","rec_yd","rec_td","rec_tgt","rec_2pt","rec_fd","fum_lost","bonus_rush_yd_100","bonus_rush_yd_200","bonus_rec_yd_100","bonus_rec_yd_200","bonus_rec_wr","rec_wr","fum"},
    "TE": {"rush_yd","rush_td","rush_att","rush_2pt","rush_fd","rec","rec_yd","rec_td","rec_tgt","rec_2pt","rec_fd","fum_lost","bonus_rush_yd_100","bonus_rush_yd_200","bonus_rec_yd_100","bonus_rec_yd_200","bonus_rec_te","rec_te","fum"},
}

BASE_FEATURES = [
    "prev_games", "prev_fantasy_ppg",
    "prev_snap_share", "prev_carry_share", "prev_target_share", "prev_qb_pass_share",
    "prev_qb_rush_share", "prev_red_zone_carry_share", "prev_inside5_carry_share",
    "prev_red_zone_target_share", "prev_backfield_competition", "prev_receiving_competition",
    "prev_pass_ypa", "prev_completion_rate", "prev_rush_ypc", "prev_catch_rate",
    "prev_rec_ypt", "prev_pass_td_rate", "prev_rush_td_rate", "prev_rec_td_rate",
    "age", "years_exp",
]


def _num(x) -> pd.Series:
    return pd.to_numeric(x, errors="coerce")


def _first(df: pd.DataFrame, names: Iterable[str]) -> Optional[str]:
    for name in names:
        if name in df.columns and _num(df[name]).notna().any():
            return name
    return None


def _safe_div(a: pd.Series, b: pd.Series) -> pd.Series:
    aa, bb = _num(a), _num(b)
    return aa / bb.where(bb.abs() > 1e-12)


def _pipeline(alpha: float = 18.0) -> Pipeline:
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("ridge", Ridge(alpha=alpha)),
    ])


def _series(df: pd.DataFrame, aliases: Sequence[str]) -> pd.Series:
    c = _first(df, aliases)
    return _num(df[c]) if c else pd.Series(np.nan, index=df.index, dtype=float)


def _fumbles_series(df: pd.DataFrame) -> pd.Series:
    """Canonical total fumbles from aggregate or split nflverse weekly fields."""
    aggregate = _num(df["fumbles"]) if "fumbles" in df.columns else pd.Series(np.nan, index=df.index, dtype=float)
    split_cols = [c for c in ["rushing_fumbles", "receiving_fumbles", "sack_fumbles"] if c in df.columns]
    if not split_cols:
        return aggregate
    split = pd.concat([_num(df[c]) for c in split_cols], axis=1).sum(axis=1, min_count=1)
    return aggregate.where(aggregate.notna(), split)


def _fumbles_lost_series(df: pd.DataFrame) -> pd.Series:
    """Canonical fumbles-lost outcome from nflverse weekly schemas.

    nflverse seasons/caches may expose either one aggregate ``fumbles_lost``
    column or split rushing/receiving/sack fumble-loss columns.  Scoring already
    supports both representations; V9.7.1 mirrors that contract in the season
    profile builder so exact replay is audited against data that actually exists.
    If no fumble-loss source exists at all, the result stays missing rather than
    fabricating zero.
    """
    aggregate = _num(df["fumbles_lost"]) if "fumbles_lost" in df.columns else pd.Series(np.nan, index=df.index, dtype=float)
    split_cols = [c for c in ["rushing_fumbles_lost", "receiving_fumbles_lost", "sack_fumbles_lost"] if c in df.columns]
    if not split_cols:
        return aggregate
    split = pd.concat([_num(df[c]) for c in split_cols], axis=1).sum(axis=1, min_count=1)
    return aggregate.where(aggregate.notna(), split)


def _season_identity(identity_path: Optional[str]) -> pd.DataFrame:
    if not identity_path or not Path(identity_path).is_file():
        return pd.DataFrame()
    q = pd.read_csv(identity_path, low_memory=False)
    keep = [c for c in ["canonical_player_id", "age", "years_exp"] if c in q.columns]
    if "canonical_player_id" not in keep:
        return pd.DataFrame()
    return q[keep].drop_duplicates("canonical_player_id", keep="last")


def build_season_profiles(player_week: pd.DataFrame, identity: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """Build one end-of-season profile per offensive player.

    Role shares are derived from the same player-week table when direct M2/M7 share
    columns are unavailable.  This deliberately reuses the canonical historical
    backbone instead of introducing a second data ingestion layer.
    """
    d = player_week.copy()
    if "position_model" not in d.columns and "position" in d.columns:
        d["position_model"] = d["position"]
    required = {"season", "canonical_player_id", "position_model"}
    if not required.issubset(d.columns):
        raise RuntimeError(f"player_week missing required columns: {sorted(required-set(d.columns))}")
    d = d[d.position_model.astype(str).isin(POSITIONS)].copy()
    d["season"] = _num(d.season)
    if "week" not in d.columns:
        d["week"] = 1
    d["week"] = _num(d.week)
    d = d[d.season.notna() & d.week.notna()].copy()

    # Canonical raw per-game columns.
    all_targets = sorted({x for pos in POSITIONS for x in RAW_TARGETS[pos]})
    for canonical in all_targets:
        aliases = []
        for pos in POSITIONS:
            aliases.extend(RAW_TARGETS[pos].get(canonical, ()))
        d[f"raw__{canonical}"] = _series(d, tuple(dict.fromkeys([canonical] + aliases)))
    # Keep the canonical scoring/profile representation aligned with score_rows().
    # This is the only special multi-column raw target because fumble losses may be
    # split by play type in nflverse rather than published as one aggregate field.
    d["raw__fumbles"] = _fumbles_series(d)
    d["raw__fumbles_lost"] = _fumbles_lost_series(d)

    # Team opportunity pools for season-level role shares.  Team can be absent in a
    # tiny fixture; those shares remain missing rather than fabricated.
    if "team" in d.columns:
        team_keys = ["season", "team"]
        team = d.groupby(team_keys, as_index=False).agg(
            team_pass_att=("raw__passing_attempts", "sum"),
            team_rush_att=("raw__rushing_attempts", "sum"),
            team_targets=("raw__targets", "sum"),
        )
    else:
        team = pd.DataFrame()

    # Direct role/context aliases already engineered in M2/M7.
    role_aliases = {
        "snap_share": ("offense_snap_share", "snap_share", "offense_snap_share_prior4", "snap_share_prior4"),
        "carry_share": ("carry_share", "carry_share_prior4"),
        "target_share": ("target_share", "target_share_prior4"),
        "qb_pass_share": ("qb_pass_attempt_share", "qb_pass_attempt_share_prior4"),
        "qb_rush_share": ("qb_rush_share", "qb_rush_share_prior4"),
        "red_zone_carry_share": ("red_zone_carry_share", "red_zone_carry_share_prior4"),
        "inside5_carry_share": ("inside_5_carry_share", "inside_5_carry_share_prior4"),
        "red_zone_target_share": ("red_zone_target_share", "red_zone_target_share_prior4"),
        "backfield_competition": ("backfield_competition_index", "backfield_competition_index_prior4", "backfield_competitor_count"),
        "receiving_competition": ("receiving_competition_index", "receiving_competition_index_prior4", "receiving_competitor_count"),
    }
    for out, aliases in role_aliases.items():
        d[f"role__{out}"] = _series(d, aliases)

    rows: List[dict] = []
    group_cols = ["season", "canonical_player_id", "position_model"]
    for (season, pid, pos), g in d.sort_values("week").groupby(group_cols, sort=False):
        pos = str(pos)
        if pos not in POSITIONS:
            continue
        valid_games = int(g["week"].nunique())
        row = {
            "season": int(season),
            "canonical_player_id": str(pid),
            "position_model": pos,
            "full_name": g["full_name"].dropna().iloc[-1] if "full_name" in g and g["full_name"].notna().any() else None,
            "team": g["team"].dropna().astype(str).iloc[-1] if "team" in g and g["team"].notna().any() else None,
            "prev_games": valid_games,
            "prev_fantasy_ppg": float(_num(g["fantasy_points"]).mean()) if "fantasy_points" in g else np.nan,
        }
        for target in RAW_TARGETS[pos]:
            row[f"prev__{target}"] = float(_num(g[f"raw__{target}"]).mean())
        for name in role_aliases:
            s = _num(g[f"role__{name}"]).dropna()
            row[f"prev_{name}"] = float(s.tail(min(4, len(s))).mean()) if len(s) else np.nan

        # Derive missing role shares from full-season player/team totals.
        if not team.empty and row.get("team"):
            tg = team[(team.season.eq(int(season))) & (team.team.astype(str).eq(str(row["team"])))]
            if not tg.empty:
                tr = tg.iloc[0]
                pass_att = float(_num(g["raw__passing_attempts"]).fillna(0).sum())
                rush_att = float(_num(g["raw__rushing_attempts"]).fillna(0).sum())
                targets = float(_num(g["raw__targets"]).fillna(0).sum())
                if not math.isfinite(row.get("prev_qb_pass_share", np.nan)):
                    row["prev_qb_pass_share"] = pass_att / tr.team_pass_att if tr.team_pass_att else np.nan
                if not math.isfinite(row.get("prev_carry_share", np.nan)):
                    row["prev_carry_share"] = rush_att / tr.team_rush_att if tr.team_rush_att else np.nan
                if not math.isfinite(row.get("prev_target_share", np.nan)):
                    row["prev_target_share"] = targets / tr.team_targets if tr.team_targets else np.nan

        # Conversion features are previous-season summaries.  They are not direct
        # fantasy-point bonuses and allow volume and efficiency to be modelled apart.
        p_att = row.get("prev__passing_attempts", np.nan)
        comp = row.get("prev__completions", np.nan)
        p_yd = row.get("prev__passing_yards", np.nan)
        p_td = row.get("prev__passing_tds", np.nan)
        r_att = row.get("prev__rushing_attempts", np.nan)
        r_yd = row.get("prev__rushing_yards", np.nan)
        r_td = row.get("prev__rushing_tds", np.nan)
        tgt = row.get("prev__targets", np.nan)
        rec = row.get("prev__receptions", np.nan)
        rec_yd = row.get("prev__receiving_yards", np.nan)
        rec_td = row.get("prev__receiving_tds", np.nan)
        row.update({
            "prev_pass_ypa": p_yd / p_att if p_att and math.isfinite(p_att) else np.nan,
            "prev_completion_rate": comp / p_att if p_att and math.isfinite(p_att) else np.nan,
            "prev_rush_ypc": r_yd / r_att if r_att and math.isfinite(r_att) else np.nan,
            "prev_catch_rate": rec / tgt if tgt and math.isfinite(tgt) else np.nan,
            "prev_rec_ypt": rec_yd / tgt if tgt and math.isfinite(tgt) else np.nan,
            "prev_pass_td_rate": p_td / p_att if p_att and math.isfinite(p_att) else np.nan,
            "prev_rush_td_rate": r_td / r_att if r_att and math.isfinite(r_att) else np.nan,
            "prev_rec_td_rate": rec_td / tgt if tgt and math.isfinite(tgt) else np.nan,
        })
        rows.append(row)

    prof = pd.DataFrame(rows)
    if prof.empty:
        return prof
    if identity is not None and not identity.empty:
        q = identity.copy()
        q["canonical_player_id"] = q.canonical_player_id.astype(str)
        prof = prof.merge(q, on="canonical_player_id", how="left", suffixes=("", "_identity"))
    for c in ["age", "years_exp"]:
        if c not in prof:
            prof[c] = np.nan
    return prof


def transition_panel(profiles: pd.DataFrame) -> pd.DataFrame:
    if profiles.empty:
        return profiles.copy()
    prev = profiles.copy()
    prev["target_season"] = prev.season.astype(int) + 1
    target_cols = [c for c in profiles.columns if c.startswith("prev__")]
    nxt = profiles[["canonical_player_id", "season", "position_model", "prev_fantasy_ppg"] + target_cols].copy()
    nxt = nxt.rename(columns={
        "season": "target_season",
        "prev_fantasy_ppg": "target_fantasy_ppg",
        **{c: c.replace("prev__", "target__", 1) for c in target_cols},
    })
    out = prev.merge(nxt, on=["canonical_player_id", "position_model", "target_season"], how="inner")
    return out[out.target_season.eq(out.season + 1)].copy()


def _features(trans: pd.DataFrame, pos: str, target: str) -> List[str]:
    preferred = ["prev_fantasy_ppg", f"prev__{target}"] + BASE_FEATURES
    fs = []
    for f in preferred:
        if f in trans.columns and _num(trans[f]).notna().sum() >= 20:
            fs.append(f)
    return list(dict.fromkeys(fs))


def _serialize(pipe: Pipeline, features: List[str], n: int) -> dict:
    imp, sc, reg = pipe.named_steps["impute"], pipe.named_steps["scale"], pipe.named_steps["ridge"]
    return {
        "algorithm": "median_impute+standardize+ridge",
        "features": features,
        "imputer_medians": [float(x) for x in imp.statistics_],
        "scaler_mean": [float(x) for x in sc.mean_],
        "scaler_scale": [float(x) if float(x) else 1.0 for x in sc.scale_],
        "coefficients": [float(x) for x in np.ravel(reg.coef_)],
        "intercept": float(np.ravel([reg.intercept_])[0]),
        "prediction_floor": 0.0,
        "n_train": int(n),
    }


def _score(pred: Dict[str, np.ndarray], pos: str, scoring: dict, n: int) -> np.ndarray:
    f = pd.DataFrame(index=np.arange(n))
    for k, v in pred.items():
        f[k] = np.maximum(0.0, np.asarray(v, dtype=float))
    f["position_model"] = pos
    # ``fum`` is an active Sleeper offensive scoring key in the pilot league but
    # the older M1 SCORING_MAP does not yet map it. Keep V9.7.1 isolated: score
    # total fumbles locally and delegate all established keys to score_rows().
    local_scoring=dict(scoring or {})
    fum_weight=local_scoring.pop("fum",0)
    out=score_rows(f, local_scoring).to_numpy(float)
    try:
        fw=float(fum_weight or 0)
    except Exception:
        fw=0.0
    if fw and "fumbles" in f.columns:
        out = out + pd.to_numeric(f["fumbles"],errors="coerce").fillna(0).to_numpy(float) * fw
    return out


def _position_scoring_audit(targets: Sequence[str], pos: str, scoring: dict) -> dict:
    """Exact position audit including V9.7.1's local total-fumbles mapping."""
    audit_frame = pd.DataFrame([{**{t: 1.0 for t in targets}, "position_model": pos}])
    position_scoring = {k:v for k,v in scoring.items() if k in POSITION_SCORING_KEYS[pos]}
    fum_weight=position_scoring.pop("fum",0) if "fum" in position_scoring else 0
    audit=scoring_audit(audit_frame, position_scoring)
    try: fum_active=math.isfinite(float(fum_weight)) and float(fum_weight)!=0
    except Exception: fum_active=False
    if fum_active:
        supported=list(audit.get("supported_keys") or [])
        unsupported=list(audit.get("unsupported") or [])
        if "fumbles" in targets:
            supported.append("fum")
        else:
            unsupported.append({"key":"fum","reason":"mapped raw-stat field absent"})
        audit["supported_keys"]=sorted(set(supported))
        audit["unsupported"]=unsupported
        audit["nonzero_keys"]=len(audit["supported_keys"])+len(unsupported)
        audit["exact_replay_eligible"]=len(unsupported)==0
        audit["coverage_rate"]=len(audit["supported_keys"])/audit["nonzero_keys"] if audit["nonzero_keys"] else 1.0
    return audit


def validate_component_preseason(player_week: pd.DataFrame, scoring: dict, identity: Optional[pd.DataFrame] = None) -> dict:
    profiles = build_season_profiles(player_week, identity)
    trans = transition_panel(profiles)
    nonlinear = [k for k, v in (scoring or {}).items() if k in BONUS_RULES and float(v or 0) != 0]
    output = {
        "build": BUILD,
        "status": "complete_research_only",
        "governance": {
            "auto_activation": False,
            "market_inputs_used": False,
            "weekly_runtime_modified": False,
            "requires_four_folds": True,
            "nonlinear_scoring_keys": nonlinear,
            "evaluation_target_source": "reconstructed_raw_components",
            "local_total_fumble_replay": True,
            "canonical_m1_scoring_modified": False,
        },
        "profiles": int(len(profiles)),
        "transitions": int(len(trans)),
        "per_position": {},
        "folds": [],
        "diagnostic_model_specs": {},
        "model_specs": {},
    }
    if trans.empty:
        return output

    for pos in POSITIONS:
        z = trans[(trans.position_model.eq(pos)) & (_num(trans.prev_games) >= 3)].copy()
        targets = [t for t in RAW_TARGETS[pos] if f"target__{t}" in z and _num(z[f"target__{t}"]).notna().sum() >= 40]
        test_seasons = sorted(int(x) for x in _num(z.target_season).dropna().unique())[-4:]
        pfolds = []
        for test in test_seasons:
            tr, te = z[z.target_season < test].copy(), z[z.target_season == test].copy()
            if len(tr) < 60 or len(te) < 12:
                continue
            pred_stats, base_stats = {}, {}
            usable = []
            for target in targets:
                ycol = f"target__{target}"; pcol = f"prev__{target}"
                fs = _features(tr, pos, target)
                train_ok = _num(tr[ycol]).notna()
                if len(fs) < 2 or int(train_ok.sum()) < 45:
                    continue
                m = _pipeline()
                m.fit(tr.loc[train_ok, fs], _num(tr.loc[train_ok, ycol]))
                pred_stats[target] = np.maximum(0.0, m.predict(te[fs]))
                base_stats[target] = np.maximum(0.0, _num(te[pcol]).fillna(0).to_numpy(float))
                usable.append(target)
            if not usable:
                continue
            fold_audit=_position_scoring_audit(usable,pos,scoring)
            pred, base = _score(pred_stats, pos, scoring, len(te)), _score(base_stats, pos, scoring, len(te))
            actual_stats={t:_num(te[f"target__{t}"]).to_numpy(float) for t in usable}
            y = _score(actual_stats, pos, scoring, len(te))
            ok = np.isfinite(y) & np.isfinite(pred) & np.isfinite(base)
            if int(ok.sum()) < 12:
                continue
            pmae = float(np.mean(np.abs(y[ok] - pred[ok])))
            bmae = float(np.mean(np.abs(y[ok] - base[ok])))
            imp = (bmae - pmae) / bmae if bmae > 0 else None
            rec = {"position": pos, "test_season": int(test), "n_test": int(ok.sum()),
                   "component_targets": usable, "model_mae": pmae, "persistence_mae": bmae,
                   "incremental_mae_improvement": imp,
                   "exact_scoring_replay_fold":bool(fold_audit.get("exact_replay_eligible")),
                   "scoring_unsupported_fold":fold_audit.get("unsupported") or []}
            pfolds.append(rec); output["folds"].append(rec)

        vals = [r["incremental_mae_improvement"] for r in pfolds if r["incremental_mae_improvement"] is not None]
        weights = [r["n_test"] for r in pfolds if r["incremental_mae_improvement"] is not None]
        gate = promotion_gate(vals, weights=weights, min_mean=.01, min_folds=4, require_positive_ci=True) if vals else {
            "robust": False, "ci95_low": None, "ci95_high": None, "folds": 0, "positive_folds": 0,
        }
        # Exact league-scoring coverage is a separate production requirement.  A
        # strong component model may remain useful diagnostically even when the
        # current target catalog cannot replay every non-zero scoring key.
        audit = _position_scoring_audit(targets, pos, scoring)
        pos_nonlinear = [k for k in nonlinear if k in POSITION_SCORING_KEYS[pos]]
        fold_exact=bool(pfolds) and all(bool(r.get("exact_scoring_replay_fold")) for r in pfolds)
        exact_scoring = bool(audit.get("exact_replay_eligible")) and fold_exact and not pos_nonlinear
        robust = bool(gate.get("robust")) and exact_scoring
        agg = {
            "status": "validated_candidate" if robust else "diagnostic_only",
            "folds": len(pfolds),
            "n_test": int(sum(weights)),
            "mean_incremental_mae_improvement": float(np.mean(vals)) if vals else None,
            "positive_folds": int(sum(v > 0 for v in vals)),
            "bootstrap_ci95_low": gate.get("ci95_low"),
            "bootstrap_ci95_high": gate.get("ci95_high"),
            "exact_scoring_replay": exact_scoring,
            "scoring_coverage_rate": audit.get("coverage_rate"),
            "scoring_unsupported": audit.get("unsupported"),
            "all_folds_exact_scoring_replay": fold_exact,
            "reason": None if robust else (
                "nonlinear_scoring_requires_separate_simulation_validation" if pos_nonlinear else
                ("incomplete_exact_scoring_replay" if not exact_scoring else "promotion_gate_not_cleared")
            ),
        }
        output["per_position"][pos] = agg

        # Refit auditable target specs on all historical transitions.  Production gets
        # a copy only when the position-level gate clears.
        specs = []
        for target in targets:
            ycol = f"target__{target}"; fs = _features(z, pos, target)
            ok = _num(z[ycol]).notna()
            if len(fs) < 2 or int(ok.sum()) < 50:
                continue
            m = _pipeline(); m.fit(z.loc[ok, fs], _num(z.loc[ok, ycol]))
            specs.append({"target": target, **_serialize(m, fs, int(ok.sum()))})
        if specs:
            pack = {"targets": specs, "gate": agg, "semantics": "prior-season role -> next-season per-game football components"}
            output["diagnostic_model_specs"][pos] = pack
            if robust:
                output["model_specs"][pos] = pack

    output["production_eligible_positions"] = sorted(output["model_specs"])
    output["production_activation_allowed"] = False  # separate runtime integration required even after validation
    return output


def fixture_player_week() -> pd.DataFrame:
    rng = np.random.default_rng(97); rows = []
    for season in range(2017, 2026):
        for pos, nplayers in [("QB", 28), ("RB", 55), ("WR", 75), ("TE", 42)]:
            for j in range(nplayers):
                pid = f"{pos}{j:03d}"
                talent = 0.4 + (j % 13) / 15 + rng.normal(0, .05)
                for week in range(1, 15):
                    if pos == "QB":
                        att = 23 + 12*talent + rng.normal(0,3); comp = att*(.56+.08*talent)
                        py = comp*(9.2+talent); ptd = att*(.035+.018*talent)
                        ra = 2+4*talent; ry=ra*(4.2+talent); rtd=ra*.05
                        raw = dict(passing_attempts=att, completions=comp, passing_yards=py, passing_tds=ptd,
                                   interceptions=att*.02, carries=ra, rushing_yards=ry, rushing_tds=rtd, fumbles_lost=0.0)
                    else:
                        tgt = max(0, (3 if pos=="RB" else 5.5)*talent + rng.normal(0,1))
                        rec=tgt*(.64+.08*talent); ryd=rec*(7 if pos=="RB" else 10+talent); rtd=tgt*.045
                        car=max(0, (10 if pos=="RB" else .5)*talent + rng.normal(0,1)); cyd=car*(4.1+.5*talent); ctd=car*.035
                        raw=dict(targets=tgt,receptions=rec,receiving_yards=ryd,receiving_tds=rtd,carries=car,rushing_yards=cyd,rushing_tds=ctd,fumbles_lost=0.0)
                    fp = raw.get("passing_yards",0)/25 + raw.get("passing_tds",0)*4 - raw.get("interceptions",0)*2 + raw.get("rushing_yards",0)/10 + raw.get("rushing_tds",0)*6 + raw.get("receptions",0) + raw.get("receiving_yards",0)/10 + raw.get("receiving_tds",0)*6
                    rows.append({"season":season,"week":week,"canonical_player_id":pid,"full_name":pid,"team":f"T{j%16:02d}","position_model":pos,"fantasy_points":fp,**raw})
    return pd.DataFrame(rows)


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--player-week", default="")
    p.add_argument("--identity", default="")
    p.add_argument("--scoring-json", default="")
    p.add_argument("--output", required=True)
    p.add_argument("--fixture", action="store_true")
    return p.parse_args(argv)


def main(argv=None):
    a = parse_args(argv)
    if a.fixture:
        pw = fixture_player_week()
        scoring = {"pass_yd":.04,"pass_td":4,"pass_int":-2,"rush_yd":.1,"rush_td":6,"rec":1,"rec_yd":.1,"rec_td":6,"fum_lost":-2}
        identity = pd.DataFrame()
    else:
        if not a.player_week or not Path(a.player_week).is_file():
            raise RuntimeError("--player-week is required outside fixture mode")
        pw = pd.read_csv(a.player_week, low_memory=False)
        identity = _season_identity(a.identity)
        if not a.scoring_json or not Path(a.scoring_json).is_file():
            raise RuntimeError("--scoring-json must contain the exact league scoring settings")
        obj = json.loads(Path(a.scoring_json).read_text())
        scoring = obj.get("settings", obj.get("scoring_settings", obj))
    out = validate_component_preseason(pw, scoring, identity)
    Path(a.output).parent.mkdir(parents=True, exist_ok=True)
    Path(a.output).write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print(f"Wrote {a.output} eligible={out.get('production_eligible_positions',[])} transitions={out.get('transitions')}")


if __name__ == "__main__":
    main()
