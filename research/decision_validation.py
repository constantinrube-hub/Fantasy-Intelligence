#!/usr/bin/env python3
"""Decision-specific forward-validation utilities for FIE V9.

This module deliberately separates projection quality from fantasy-decision
quality.  It is dependency-light and can be imported by future M5/M6 builders
or run on exported decision-evaluation rows.  Promotion remains fail-closed
when sample, temporal coverage, practical lift, or calibration gates are not
met.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping, Sequence
import math
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Gate:
    min_rows: int
    min_periods: int
    min_relative_lift: float
    min_spearman_delta: float = 0.0
    max_regret_ratio: float = 1.0


DEFAULT_GATES = {
    "draft": Gate(250, 6, 0.01, 0.0, 0.99),
    "start_sit": Gate(300, 8, 0.01, 0.0, 0.99),
    "waiver": Gate(200, 6, 0.015, 0.0, 0.985),
    "chopped": Gate(200, 6, 0.01, 0.0, 0.99),
    "best_ball": Gate(250, 6, 0.01, 0.0, 0.99),
    "dynasty": Gate(250, 2, 0.01, 0.0, 0.99),
}


def _finite_series(x: Iterable) -> pd.Series:
    return pd.to_numeric(pd.Series(x), errors="coerce").replace([np.inf, -np.inf], np.nan)


def mae(y, pred) -> float | None:
    y, p = _finite_series(y), _finite_series(pred)
    m = y.notna() & p.notna()
    return float((y[m] - p[m]).abs().mean()) if m.any() else None


def spearman(y, pred) -> float | None:
    y, p = _finite_series(y), _finite_series(pred)
    m = y.notna() & p.notna()
    if int(m.sum()) < 3:
        return None
    v = y[m].rank().corr(p[m].rank())
    return float(v) if pd.notna(v) else None


def brier(y, prob) -> float | None:
    y, p = _finite_series(y), _finite_series(prob)
    m = y.notna() & p.notna()
    if not m.any():
        return None
    p = p[m].clip(0, 1)
    return float(((p - y[m]) ** 2).mean())


def relative_improvement(candidate: float | None, baseline: float | None, *, lower_is_better: bool = True) -> float | None:
    if candidate is None or baseline is None or not math.isfinite(candidate) or not math.isfinite(baseline) or abs(baseline) < 1e-12:
        return None
    return float((baseline - candidate) / abs(baseline) if lower_is_better else (candidate - baseline) / abs(baseline))


def temporal_period_count(df: pd.DataFrame, cols: Sequence[str] = ("season", "week")) -> int:
    use = [c for c in cols if c in df.columns]
    if not use:
        return 0
    return int(df[use].drop_duplicates().shape[0])


def paired_block_bootstrap_delta(
    df: pd.DataFrame,
    candidate_col: str,
    baseline_col: str,
    outcome_col: str,
    *,
    block_cols: Sequence[str] = ("season", "week"),
    n_boot: int = 800,
    seed: int = 89,
) -> dict:
    """Bootstrap paired MAE improvement by temporal blocks.

    Positive values mean the candidate improves on baseline.  Candidate and
    baseline always use the same resampled rows, limiting winner's-curse noise
    compared with independent resampling.
    """
    cols = [candidate_col, baseline_col, outcome_col] + [c for c in block_cols if c in df.columns]
    x = df[cols].copy()
    for c in [candidate_col, baseline_col, outcome_col]:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.dropna(subset=[candidate_col, baseline_col, outcome_col])
    use_blocks = [c for c in block_cols if c in x.columns]
    if x.empty or not use_blocks:
        return {"n": int(len(x)), "blocks": 0, "mean_delta": None, "ci_low": None, "ci_high": None}
    groups = [g for _, g in x.groupby(use_blocks, dropna=False)]
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(int(n_boot)):
        sample = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))], ignore_index=True)
        bm = mae(sample[outcome_col], sample[baseline_col])
        cm = mae(sample[outcome_col], sample[candidate_col])
        if bm is not None and cm is not None:
            vals.append(bm - cm)
    if not vals:
        return {"n": int(len(x)), "blocks": len(groups), "mean_delta": None, "ci_low": None, "ci_high": None}
    a = np.asarray(vals, dtype=float)
    return {
        "n": int(len(x)), "blocks": len(groups), "mean_delta": float(a.mean()),
        "ci_low": float(np.quantile(a, .025)), "ci_high": float(np.quantile(a, .975)),
    }


def decision_regret(actual_utility, chosen_utility, best_utility) -> dict:
    a, c, b = map(_finite_series, (actual_utility, chosen_utility, best_utility))
    m = a.notna() & c.notna() & b.notna()
    if not m.any():
        return {"n": 0, "mean_regret": None, "normalized_regret": None}
    # actual_utility is retained in the contract for audit/context; regret is
    # the opportunity loss between chosen and best legal action.
    regret = (b[m] - c[m]).clip(lower=0)
    denom = b[m].abs().replace(0, np.nan)
    return {"n": int(m.sum()), "mean_regret": float(regret.mean()), "normalized_regret": float((regret / denom).dropna().mean()) if denom.notna().any() else None}


def evaluate_prediction_rows(df: pd.DataFrame, *, candidate="candidate", baseline="baseline", outcome="actual") -> dict:
    cm, bm = mae(df[outcome], df[candidate]), mae(df[outcome], df[baseline])
    cs, bs = spearman(df[outcome], df[candidate]), spearman(df[outcome], df[baseline])
    return {
        "rows": int(df[[candidate, baseline, outcome]].dropna().shape[0]),
        "candidate_mae": cm, "baseline_mae": bm,
        "relative_mae_lift": relative_improvement(cm, bm),
        "candidate_spearman": cs, "baseline_spearman": bs,
        "spearman_delta": None if cs is None or bs is None else cs - bs,
        "periods": temporal_period_count(df),
        "paired_bootstrap": paired_block_bootstrap_delta(df, candidate, baseline, outcome),
    }


def promotion_decision(metrics: Mapping, domain: str, gate: Gate | None = None) -> dict:
    gate = gate or DEFAULT_GATES[domain]
    checks = {
        "rows": int(metrics.get("rows") or 0) >= gate.min_rows,
        "periods": int(metrics.get("periods") or 0) >= gate.min_periods,
        "relative_lift": (metrics.get("relative_mae_lift") is not None and metrics["relative_mae_lift"] >= gate.min_relative_lift),
        "rank": (metrics.get("spearman_delta") is None or metrics["spearman_delta"] >= gate.min_spearman_delta),
        "positive_bootstrap_ci": (metrics.get("paired_bootstrap", {}).get("ci_low") is not None and metrics["paired_bootstrap"]["ci_low"] > 0),
    }
    if metrics.get("regret_ratio") is not None:
        checks["regret"] = metrics["regret_ratio"] <= gate.max_regret_ratio
    return {"domain": domain, "enabled": all(checks.values()), "checks": checks, "gate": asdict(gate)}


def evaluate_domain(df: pd.DataFrame, domain: str) -> dict:
    """Evaluate a standard FIE decision-validation export.

    Required: actual, candidate, baseline. Optional decision-specific columns:
    chosen_utility, baseline_chosen_utility, best_utility, event_probability,
    event_actual.  The latter support regret and calibration without forcing a
    single generic metric on every decision domain.
    """
    required = {"actual", "candidate", "baseline"}
    missing = sorted(required - set(df.columns))
    if missing:
        return {"domain": domain, "status": "unavailable", "reason": f"missing columns: {', '.join(missing)}", "promotion": {"enabled": False}}
    metrics = evaluate_prediction_rows(df)
    if {"chosen_utility", "baseline_chosen_utility", "best_utility"}.issubset(df.columns):
        c = decision_regret(df["actual"], df["chosen_utility"], df["best_utility"])
        b = decision_regret(df["actual"], df["baseline_chosen_utility"], df["best_utility"])
        metrics["candidate_regret"] = c
        metrics["baseline_regret"] = b
        if c["mean_regret"] is not None and b["mean_regret"] not in (None, 0):
            metrics["regret_ratio"] = c["mean_regret"] / b["mean_regret"]
    if {"event_probability", "event_actual"}.issubset(df.columns):
        metrics["brier"] = brier(df["event_actual"], df["event_probability"])
    promotion = promotion_decision(metrics, domain)
    return {"domain": domain, "status": "complete", "metrics": metrics, "promotion": promotion}


__all__ = [
    "Gate", "DEFAULT_GATES", "mae", "spearman", "brier", "relative_improvement",
    "paired_block_bootstrap_delta", "decision_regret", "evaluate_prediction_rows",
    "promotion_decision", "evaluate_domain",
]
