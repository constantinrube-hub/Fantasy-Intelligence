#!/usr/bin/env python3
"""Build the Tranche 6D offline M10 offensive research challenger.

M10 predicts raw football outcomes from lagged public-core evidence, reconciles
incompatible player opportunity against team budgets, and only then applies the
existing exact league scorer. It has no runtime writer or promotion path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_pinball_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from fie_m4 import canonical_scoring, feature_frame, final_model_validation, parse_args as m4_parse_args
from fie_research import score_rows
from fie_research_pipeline_contract import ROOT, canonical_bytes, load_json, sha256_bytes, write_json


CONTRACT_PATH = ROOT / "config/m10-offline-experiment.json"
COUNT_TARGETS = {"attempts", "completions", "passing_tds", "interceptions", "carries", "rushing_tds", "targets", "receptions", "receiving_tds"}
BASE_FEATURES = [
    "team_plays", "team_dropbacks", "team_pass_attempts", "team_rush_attempts",
    "team_red_zone_plays", "team_goal_line_plays", "snap_share", "offense_snap_share",
    "target_share", "carry_share", "qb_rush_share", "red_zone_target_share",
    "red_zone_carry_share", "inside_10_carry_share", "inside_5_carry_share",
    "targets", "receptions", "receiving_yards", "receiving_tds", "carries",
    "rushing_yards", "rushing_tds", "attempts", "completions", "passing_yards",
    "passing_tds", "interceptions", "fantasy_points",
]


def lagged_panel(df: pd.DataFrame) -> pd.DataFrame:
    keys = ["canonical_player_id", "season"]
    d = df.sort_values(["canonical_player_id", "season", "week"]).copy()
    for col in BASE_FEATURES:
        if col in d and pd.to_numeric(d[col], errors="coerce").notna().any():
            values = pd.to_numeric(d[col], errors="coerce")
            d[f"{col}_prior4"] = values.groupby([d[k] for k in keys]).transform(
                lambda x: x.shift(1).rolling(4, min_periods=2).mean()
            )
    if "opponent_team" in d:
        d["opponent_team_code"] = pd.factorize(d["opponent_team"].fillna("UNK"), sort=True)[0]
    return d


def features_for(d: pd.DataFrame) -> list[str]:
    return sorted(c for c in d.columns if c.endswith("_prior4") and pd.to_numeric(d[c], errors="coerce").notna().any())


def linear_model(alpha: float) -> Pipeline:
    return Pipeline([("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])


def hgb_loss(target: str, training_target: pd.Series) -> str:
    """Choose a valid deterministic loss from the outer training window only."""
    observed = pd.to_numeric(training_target, errors="coerce").dropna().clip(lower=0)
    return "poisson" if target in COUNT_TARGETS and float(observed.sum()) > 0 else "squared_error"


def hgb_model(spec: dict[str, Any], target: str, training_target: pd.Series) -> Pipeline:
    loss = hgb_loss(target, training_target)
    return Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", HistGradientBoostingRegressor(loss=loss, random_state=106, **spec)),
    ])


def fit_predict(model: Any, train: pd.DataFrame, test: pd.DataFrame, features: list[str], target: str) -> np.ndarray:
    y = pd.to_numeric(train[target], errors="coerce")
    ok = y.notna()
    model.fit(train.loc[ok, features], y[ok].clip(lower=0))
    return np.maximum(0.0, np.asarray(model.predict(test[features]), dtype=float))


def choose_hgb_spec(train: pd.DataFrame, features: list[str], target: str, specs: list[dict[str, Any]]) -> dict[str, Any]:
    years = sorted(int(x) for x in train.season.dropna().unique())
    if len(years) < 2:
        return dict(specs[0])
    inner_test = years[-1]
    tr, va = train[train.season.lt(inner_test)], train[train.season.eq(inner_test)]
    y = pd.to_numeric(va[target], errors="coerce")
    ok = y.notna()
    if len(tr) < 80 or ok.sum() < 12:
        return dict(specs[0])
    scored = []
    for i, spec in enumerate(specs):
        pred = fit_predict(hgb_model(spec, target, tr[target]), tr, va.loc[ok], features, target)
        scored.append((float(mean_absolute_error(y[ok], pred)), i, spec))
    return dict(min(scored, key=lambda row: (row[0], row[1]))[2])


def reconcile(raw: pd.DataFrame) -> pd.DataFrame:
    out = raw.copy()
    for volume, budget in (("targets", "team_pass_attempts_prior4"), ("carries", "team_rush_attempts_prior4")):
        if volume not in out or budget not in out:
            continue
        for _, idx in out.groupby(["season", "week", "team"]).groups.items():
            ids = list(idx); total = float(pd.to_numeric(out.loc[ids, volume], errors="coerce").fillna(0).sum())
            available = float(pd.to_numeric(out.loc[ids, budget], errors="coerce").dropna().median()) if pd.to_numeric(out.loc[ids, budget], errors="coerce").notna().any() else 0.0
            if total > available > 0:
                out.loc[ids, volume] = out.loc[ids, volume] * available / total
    if {"completions", "attempts"}.issubset(out): out["completions"] = np.minimum(out.completions, out.attempts)
    if {"receptions", "targets"}.issubset(out): out["receptions"] = np.minimum(out.receptions, out.targets)
    return out


def metric_row(y: pd.Series, pred: pd.Series, residuals: np.ndarray, quantiles: list[float]) -> dict[str, Any]:
    yv, pv = np.asarray(y, float), np.asarray(pred, float)
    rq = {str(q): float(np.quantile(residuals, q)) if len(residuals) else 0.0 for q in quantiles}
    qp = {str(q): np.maximum(0.0, pv + rq[str(q)]) for q in quantiles}
    return {
        "n": int(len(yv)), "mae": float(mean_absolute_error(yv, pv)), "bias": float(np.mean(pv - yv)),
        "spearman": None if len(yv) < 3 else float(pd.Series(yv).corr(pd.Series(pv), method="spearman")),
        "pinball": {str(q): float(mean_pinball_loss(yv, qp[str(q)], alpha=q)) for q in quantiles},
        "p10_p90_coverage": float(np.mean((yv >= qp[str(quantiles[0])]) & (yv <= qp[str(quantiles[-1])]))),
        "p10_p90_width": float(np.mean(qp[str(quantiles[-1])] - qp[str(quantiles[0])])),
    }


def build(args: argparse.Namespace) -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH, {})
    m4_args = m4_parse_args(["--fixture"] if args.fixture else [
        "--derived-dir", args.derived_dir, "--cache-dir", args.cache_dir,
        "--m1-bundle", args.m1_bundle, "--m2-bundle", args.m2_bundle,
        "--m3-bundle", args.m3_bundle, "--seasons", "2019-2025",
    ])
    df, _, _, m1, _, _ = feature_frame(m4_args)
    scoring = canonical_scoring(m1)
    panel = lagged_panel(df[df.position_model.isin(contract["positions"])].copy())
    _, _, _, m9_oos, _ = final_model_validation(df, scoring)
    m9 = m9_oos.rename(columns={"fie_projection": "M9"})[["season", "week", "canonical_player_id", "position_model", "M9"]]
    panel = panel.merge(m9, on=["season", "week", "canonical_player_id", "position_model"], how="inner")
    folds = []
    for fold in contract["outer_folds"]:
        for pos in contract["positions"]:
            z = panel[panel.position_model.eq(pos)].copy(); features = features_for(z)
            train = z[z.season.isin(fold["train_seasons"])]; test = z[z.season.eq(fold["test_season"])].copy()
            targets = [t for t in contract["targets"][pos] if t in z]
            if len(train) < 80 or len(test) < 12 or not features or not targets: continue
            predictions: dict[str, pd.DataFrame] = {}
            for candidate in ("M10_LINEAR", "M10_HGB"):
                raw = test[["season", "week", "team"] + [c for c in ("team_pass_attempts_prior4", "team_rush_attempts_prior4") if c in test]].copy()
                for target in targets:
                    if candidate == "M10_LINEAR": model = linear_model(6.0)
                    else: model = hgb_model(choose_hgb_spec(train, features, target, contract["candidate_ladder"][2]["search_space"]), target, train[target])
                    raw[target] = fit_predict(model, train, test, features, target)
                predictions[candidate] = reconcile(raw)
            actual = pd.to_numeric(test.fantasy_points, errors="coerce")
            valid = actual.notna() & pd.to_numeric(test.M9, errors="coerce").notna()
            if valid.sum() < 10: continue
            rows = {"M9": pd.to_numeric(test.M9, errors="coerce")}
            for candidate, raw in predictions.items():
                raw["position_model"] = pos
                rows[candidate] = score_rows(raw, scoring)
            metrics = {}
            for candidate, pred in rows.items():
                residual_train = pd.to_numeric(train.fantasy_points, errors="coerce").dropna().to_numpy() - float(pd.to_numeric(train.fantasy_points, errors="coerce").dropna().median())
                metrics[candidate] = metric_row(actual[valid], pred[valid], residual_train, contract["quantiles"])
            folds.append({"position": pos, "train_seasons": fold["train_seasons"], "test_season": fold["test_season"], "paired_rows": int(valid.sum()), "feature_count": len(features), "raw_targets": targets, "metrics": metrics})
    return {
        "schema": "fie-m10-offline-challenger-v1", "experiment_contract_sha256": sha256_bytes(canonical_bytes(contract)),
        "league_id": args.league_id, "scoring_signature": (m1.get("scoring") or {}).get("signature"),
        "source_lineage": {"m1_bundle": args.m1_bundle, "m2_bundle": args.m2_bundle, "m3_bundle": args.m3_bundle, "derived_dir": args.derived_dir, "seasons": [2019, 2020, 2021, 2022, 2023, 2024, 2025]},
        "fixture": bool(args.fixture), "governance": {"research_only": True, "production_model": "M9", "production_activation": False, "app_integration": False, "ensemble": False},
        "component_graph": contract["component_graph"], "candidate_ladder": contract["candidate_ladder"], "outer_folds": contract["outer_folds"],
        "fold_results": folds, "status": "RESEARCH_ONLY_EVALUATED" if folds else "BLOCKED_INSUFFICIENT_OFFLINE_ROWS",
        "promotion_status": "NOT_REVIEWED_TRANCHE_6E_REQUIRED", "distribution_method": "training-window empirical position residual envelope; diagnostic only",
        "notes": ["M9 remains champion.", "2026 is excluded from all selection and evaluation.", "Availability is an external governed input; no historical state is reconstructed."],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(); p.add_argument("--fixture", action="store_true"); p.add_argument("--league-id", default="fixture" ); p.add_argument("--derived-dir", default="data/research/derived"); p.add_argument("--cache-dir", default=".cache/fie-research"); p.add_argument("--m1-bundle", default="data/research/milestone1.json"); p.add_argument("--m2-bundle", default="data/research/milestone2.json"); p.add_argument("--m3-bundle", default="data/research/milestone3.json"); p.add_argument("--output", default="artifacts/tranche6d/m10-offline-challenger.json"); a = p.parse_args(argv)
    out = Path(a.output); out = out if out.is_absolute() else ROOT / out; write_json(out, build(a)); print(f"PASS wrote {out} research-only M10 challenger"); return 0


if __name__ == "__main__": raise SystemExit(main())
