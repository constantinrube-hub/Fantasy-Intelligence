#!/usr/bin/env python3
"""Year-to-year raw-stat preseason projection research for FIE M9.

This module exists because the canonical weekly model correctly requires completed
same-season games.  A preseason/season ranking must not multiply a Week-N residual
correction across 17 games.  Instead, prior-season end profiles predict next-season
per-game raw football outcomes, which are then replayed through the exact league
scoring function.

The model is fail-closed and chronologically validated by target season.  It is a
separate gate from weekly M4/M7/M8 and therefore cannot contaminate weekly runtime.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_research import score_rows
from fie_m4 import RAW_TARGETS
from fie_m7 import OFFENSE_POSITIONS, DRIVER_CATALOG, add_derived_driver_features
from statistical_guardrails import promotion_gate


# M9 season projection must cover every material offensive scoring outcome for
# the position before the board may claim exact league-scoring replay.  Keep
# these additions local to M9 so the validated M1-M8 weekly stack and checkpoint
# remain unchanged.
SEASON_EXTRA_TARGETS: Dict[str, Dict[str, Sequence[str]]] = {
    "QB": {
        "passing_2pt_conversions": ["passing_2pt_conversions"],
        "rushing_2pt_conversions": ["rushing_2pt_conversions"],
        "fumbles_lost": ["fumbles_lost"],
    },
    "RB": {
        "rushing_2pt_conversions": ["rushing_2pt_conversions"],
        "receiving_2pt_conversions": ["receiving_2pt_conversions"],
        "fumbles_lost": ["fumbles_lost"],
    },
    "WR": {
        "rushing_yards": ["rushing_yards"],
        "rushing_tds": ["rushing_tds"],
        "rushing_2pt_conversions": ["rushing_2pt_conversions"],
        "receiving_2pt_conversions": ["receiving_2pt_conversions"],
        "fumbles_lost": ["fumbles_lost"],
    },
    "TE": {
        "rushing_yards": ["rushing_yards"],
        "rushing_tds": ["rushing_tds"],
        "rushing_2pt_conversions": ["rushing_2pt_conversions"],
        "receiving_2pt_conversions": ["receiving_2pt_conversions"],
        "fumbles_lost": ["fumbles_lost"],
    },
}


def _season_target_catalog(pos: str) -> Dict[str, Sequence[str]]:
    out = {str(k): list(v) for k, v in (RAW_TARGETS.get(pos, {}) or {}).items()}
    for k, v in (SEASON_EXTRA_TARGETS.get(pos, {}) or {}).items():
        out[str(k)] = list(v)
    return out


def add_scoring_completion_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Canonicalize sparse scoring outcomes already present in nflverse history.

    nflverse can split fumbles lost by play type.  FIE's score_rows already knows
    how to sum those fields; the season model needs the same total as one target.
    No value is fabricated: absent source columns remain absent/NaN.
    """
    d = df.copy()
    if "fumbles_lost" not in d.columns or pd.to_numeric(d.get("fumbles_lost"), errors="coerce").notna().sum() == 0:
        split = [c for c in ["rushing_fumbles_lost", "receiving_fumbles_lost", "sack_fumbles_lost"] if c in d.columns]
        if split:
            vals = [pd.to_numeric(d[c], errors="coerce") for c in split]
            present = pd.concat([v.notna() for v in vals], axis=1).any(axis=1)
            total = sum((v.fillna(0.0) for v in vals), start=pd.Series(0.0, index=d.index))
            d["fumbles_lost"] = total.where(present, np.nan)
    return d

def _first(df: pd.DataFrame, names: Sequence[str]) -> Optional[str]:
    for x in names:
        if x in df.columns and pd.to_numeric(df[x], errors="coerce").notna().any():
            return x
    return None


def _model(alpha: float = 18.0) -> Pipeline:
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])


def _driver_features(df: pd.DataFrame, pos: str) -> List[str]:
    # Premium and explicit current-opponent matchup fields are deliberately excluded
    # from a year-to-year portability model.  The latter are schedule-specific M8 work.
    fs = []
    for family, members in DRIVER_CATALOG.get(pos, {}).items():
        if family.startswith("premium_"):
            continue
        for f in members:
            if f in df.columns and pd.to_numeric(df[f], errors="coerce").notna().sum() >= 25:
                fs.append(f)
    # Keep the profile compact and avoid duplicate interaction/main-effect explosion.
    preferred = [f for f in fs if not f.startswith("m7_")] + [f for f in fs if f.startswith("m7_")]
    return list(dict.fromkeys(preferred))[:24]


def _targets(df: pd.DataFrame, pos: str) -> Dict[str, str]:
    out = {}
    for canonical, aliases in _season_target_catalog(pos).items():
        c = _first(df, aliases)
        if c:
            out[canonical] = c
    return out


def build_transition_table(df: pd.DataFrame, pos: str) -> Tuple[pd.DataFrame, List[str], Dict[str, str]]:
    d = add_scoring_completion_columns(df[df.position_model.eq(pos)].copy())
    d = add_derived_driver_features(d)
    if d.empty:
        return pd.DataFrame(), [], {}
    features = _driver_features(d, pos)
    targets = _targets(d, pos)
    if not targets:
        return pd.DataFrame(), features, targets
    rows = []
    for (pid, season), g in d.sort_values("week").groupby(["canonical_player_id", "season"], sort=False):
        g = g.sort_values("week")
        last = g.iloc[-1]
        row = {
            "canonical_player_id": str(pid), "profile_season": int(season),
            "full_name": last.get("full_name"), "profile_team": last.get("team"), "position_model": pos,
            "prev_fantasy_ppg": float(pd.to_numeric(g.fantasy_points, errors="coerce").mean()),
            "prev_games": int(pd.to_numeric(g.fantasy_points, errors="coerce").notna().sum()),
        }
        for f in features:
            x = last.get(f)
            try: row[f] = float(x) if x is not None and math.isfinite(float(x)) else np.nan
            except Exception: row[f] = np.nan
        for canonical, source in targets.items():
            row[f"prev__{canonical}"] = float(pd.to_numeric(g[source], errors="coerce").mean())
        rows.append(row)
    prof = pd.DataFrame(rows)
    if prof.empty:
        return prof, features, targets

    # Next-season actuals come from the next consecutive player-season only.
    nxt = prof[["canonical_player_id", "profile_season", "prev_fantasy_ppg"] + [f"prev__{x}" for x in targets]].copy()
    nxt["target_season"] = nxt.profile_season.astype(int)
    nxt = nxt.rename(columns={"prev_fantasy_ppg": "target_fantasy_ppg", **{f"prev__{x}": f"target__{x}" for x in targets}})
    prev = prof.copy(); prev["target_season"] = prev.profile_season.astype(int) + 1
    transitions = prev.merge(nxt.drop(columns=["profile_season"]), on=["canonical_player_id", "target_season"], how="inner")
    transitions = transitions[transitions.target_season.eq(transitions.profile_season + 1)].copy()
    return transitions, features, targets


def _score_stat_frame(values: Dict[str, np.ndarray], pos: str, scoring: dict, n: int) -> np.ndarray:
    frame = pd.DataFrame({k: np.maximum(0.0, np.asarray(v, dtype=float)) for k, v in values.items()})
    frame["position_model"] = pos
    return score_rows(frame, scoring).to_numpy(float)


def validate_preseason(df: pd.DataFrame, scoring: dict) -> dict:
    folds = []; specs = {}; diagnostic_specs = {}; latest_profiles = []; residuals_by_pos: Dict[str, List[float]] = {}
    per_position = {}
    for pos in OFFENSE_POSITIONS:
        trans, features, targets = build_transition_table(df, pos)
        # Also save the most recent profile whether or not the model clears.
        dpos = add_scoring_completion_columns(df[df.position_model.eq(pos)].copy())
        dpos = add_derived_driver_features(dpos)
        if not dpos.empty:
            max_season = int(pd.to_numeric(dpos.season, errors="coerce").max())
            for pid, g in dpos[dpos.season.eq(max_season)].sort_values("week").groupby("canonical_player_id"):
                last = g.iloc[-1]
                r = {"canonical_player_id": str(pid), "profile_season": max_season, "full_name": last.get("full_name"),
                     "profile_team": last.get("team"), "position_model": pos,
                     "prev_fantasy_ppg": float(pd.to_numeric(g.fantasy_points, errors="coerce").mean()),
                     "prev_games": int(len(g))}
                for f in features:
                    try: r[f] = float(last.get(f)) if math.isfinite(float(last.get(f))) else np.nan
                    except Exception: r[f] = np.nan
                for canonical, source in targets.items():
                    r[f"prev__{canonical}"] = float(pd.to_numeric(g[source], errors="coerce").mean())
                latest_profiles.append(r)
        if trans.empty or len(trans) < 80:
            per_position[pos] = {"status": "diagnostic_only", "reason": "insufficient_year_to_year_transitions", "n": int(len(trans))}
            continue
        # Require at least three prior games to avoid tiny one-game season fragments.
        trans = trans[(trans.prev_games >= 3) & trans.target_fantasy_ppg.notna()].copy()
        test_seasons = sorted(int(x) for x in trans.target_season.unique())[-4:]
        for test_season in test_seasons:
            tr = trans[trans.target_season < test_season].copy(); te = trans[trans.target_season.eq(test_season)].copy()
            if len(tr) < 60 or len(te) < 12:
                continue
            pred_stats = {}; base_stats = {}; usable_targets = []
            for canonical in targets:
                target_col = f"target__{canonical}"; prev_col = f"prev__{canonical}"
                if target_col not in tr or pd.to_numeric(tr[target_col], errors="coerce").notna().sum() < 40:
                    continue
                fs = ["prev_fantasy_ppg", prev_col] + [f for f in features if f in tr]
                fs = list(dict.fromkeys(fs))
                m = _model(); m.fit(tr[fs], pd.to_numeric(tr[target_col], errors="coerce"))
                pred_stats[canonical] = np.maximum(0.0, m.predict(te[fs]))
                base_stats[canonical] = np.maximum(0.0, pd.to_numeric(te[prev_col], errors="coerce").fillna(0).to_numpy(float))
                usable_targets.append(canonical)
            if not usable_targets:
                continue
            pred = _score_stat_frame(pred_stats, pos, scoring, len(te))
            base = _score_stat_frame(base_stats, pos, scoring, len(te))
            y = pd.to_numeric(te.target_fantasy_ppg, errors="coerce").to_numpy(float)
            ok = np.isfinite(y) & np.isfinite(pred) & np.isfinite(base)
            if ok.sum() < 12:
                continue
            y, pred, base = y[ok], pred[ok], base[ok]
            pmae = float(np.mean(np.abs(y - pred))); bmae = float(np.mean(np.abs(y - base)))
            imp = (bmae - pmae) / bmae if bmae > 0 else None
            folds.append({"position": pos, "test_season": test_season, "n_test": int(ok.sum()),
                          "targets": usable_targets, "preseason_mae": pmae, "prior_season_raw_stat_mae": bmae,
                          "incremental_mae_improvement": imp})
            residuals_by_pos.setdefault(pos, []).extend((y - pred).tolist())

        pf = [r for r in folds if r["position"] == pos and r.get("incremental_mae_improvement") is not None]
        vals = [r["incremental_mae_improvement"] for r in pf]; weights = [r["n_test"] for r in pf]
        gate = promotion_gate(vals, weights=weights, min_mean=.01, min_folds=4, require_positive_ci=True) if vals else {"robust": False, "ci95_low": None, "ci95_high": None}
        agg = {"status": "validated_candidate" if gate.get("robust") else "diagnostic_only", "folds": len(pf),
               "n_test": int(sum(weights)), "mean_incremental_mae_improvement": float(np.mean(vals)) if vals else None,
               "bootstrap_ci95_low": gate.get("ci95_low"), "bootstrap_ci95_high": gate.get("ci95_high")}
        per_position[pos] = agg

        # Always serialize an auditable shadow/diagnostic specification when the
        # year-to-year sample is large enough to estimate it.  The production
        # `model_specs` dictionary remains strictly gated; diagnostic specs never
        # gain activation rights merely by existing.
        target_specs = []
        for canonical in targets:
            target_col = f"target__{canonical}"; prev_col = f"prev__{canonical}"
            if target_col not in trans or pd.to_numeric(trans[target_col], errors="coerce").notna().sum() < 50:
                continue
            fs = list(dict.fromkeys(["prev_fantasy_ppg", prev_col] + [f for f in features if f in trans]))
            z = trans.dropna(subset=[target_col]).copy()
            if len(z) < 50:
                continue
            m = _model(); m.fit(z[fs], pd.to_numeric(z[target_col], errors="coerce"))
            imp, sc, reg = m.named_steps["impute"], m.named_steps["scale"], m.named_steps["ridge"]
            target_specs.append({"target": canonical, "features": fs, "imputer_medians": [float(x) for x in imp.statistics_],
                                 "scaler_mean": [float(x) for x in sc.mean_], "scaler_scale": [float(x) if x else 1.0 for x in sc.scale_],
                                 "coefficients": [float(x) for x in reg.coef_], "intercept": float(reg.intercept_),
                                 "prediction_floor": 0.0, "n_train": int(len(z))})
        if target_specs:
            shadow = {"targets": target_specs, "gate": agg, "profile_features": features,
                      "semantics": "market-comparison shadow model: prior-season profile -> next-season per-game raw football outcomes",
                      "activation_eligible": agg["status"] == "validated_candidate"}
            diagnostic_specs[pos] = shadow
            if agg["status"] == "validated_candidate":
                specs[pos] = shadow

    residual_cal = {}
    for pos, vals in residuals_by_pos.items():
        a = np.asarray(vals, dtype=float); a = a[np.isfinite(a)]
        if len(a):
            residual_cal[pos] = {"n": int(len(a)), "mean": float(a.mean()), "std": float(a.std(ddof=1)) if len(a)>1 else 0.0,
                                 "q10": float(np.quantile(a,.10)), "q25": float(np.quantile(a,.25)), "q50": float(np.quantile(a,.50)),
                                 "q75": float(np.quantile(a,.75)), "q90": float(np.quantile(a,.90))}
    return {"folds": folds, "aggregate": per_position, "model_specs": specs,
            "diagnostic_model_specs": diagnostic_specs,
            "latest_profiles": latest_profiles, "oos_residual_calibration": residual_cal,
            "activation_status": "POSITION_SPEC_AVAILABLE" if specs else "DIAGNOSTIC_ONLY",
            "diagnostic_semantics": "Shadow specs are serialized for market-relative explanation even when a position fails the production gate. They never activate runtime projections unless the corresponding production model_specs gate also clears."}


def write_latest_profiles(rows: List[dict], derived_dir: str) -> Optional[str]:
    if not rows or not derived_dir:
        return None
    p = Path(derived_dir) / "m9_preseason_latest_profiles.csv.gz"; p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(p, index=False, compression="gzip"); return str(p)
