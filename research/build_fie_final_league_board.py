#!/usr/bin/env python3
"""Build one canonical per-league FIE research board.

The board does not implement ranking, scarcity or replacement logic.  For offense
it feeds the canonical M9 season board back through the *existing*
``fie_strategy_stack.build_league_value_board`` function, so the exact same
league-specific replacement/VORP/market semantics used by the strategy stack are
preserved.  V9.7 shadow output is joined only as challenger evidence.

D/ST and K remain owned by their dedicated current engines.  Their rows are
included for report display with an explicit ``WEEKLY_CURRENT`` projection scope;
no season-long VORP or market rank is fabricated for special teams.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from fie_research_pipeline_contract import (
    FINAL_BOARD_SCHEMA, OFFENSE, current_path, league_root, load_json, load_profile,
    pipeline_dir, strategy_dir, write_json,
)
from fie_strategy_stack import build_league_value_board
from current_snapshot_storage import load_current_snapshot


def finite(v: Any) -> float | None:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def norm_id(v: Any) -> str:
    if v is None:
        return ""
    try:
        if pd.isna(v):
            return ""
    except Exception:
        pass
    s = str(v).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return "" if s.lower() in {"", "nan", "none", "<na>"} else s


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if value is pd.NA:
        return None
    try:
        if bool(pd.isna(value)):
            return None
    except Exception:
        pass
    return value


def _join_key(row: dict) -> str:
    cid = norm_id(row.get("canonical_player_id"))
    sid = norm_id(row.get("sleeper_id"))
    return f"c:{cid}" if cid else (f"s:{sid}" if sid else "")


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, low_memory=False) if path.is_file() else pd.DataFrame()


def _canonical_offense_value_board(league_id: str, season: int, profile: dict, current: dict) -> tuple[pd.DataFrame, dict]:
    root = league_root(league_id)
    sdir = strategy_dir(league_id, season)
    m9 = _read_csv(root / "performance" / str(season) / "season_board.csv")
    if m9.empty:
        raise RuntimeError("canonical M9 season_board.csv is required")
    movement = _read_csv(sdir / "market_movement.csv")
    curves = _read_csv(sdir / "adp_outcome_curves.csv")
    # Critical invariant: use existing production-oriented M9 board, not V9.7 shadow.
    canonical, meta = build_league_value_board(m9, profile, movement, curves, current=current)
    return canonical, meta


def _challenger_map(strategy_value: pd.DataFrame) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if strategy_value.empty:
        return out
    for row in strategy_value.to_dict("records"):
        key = _join_key(row)
        if not key:
            continue
        out[key] = {
            "research_challenger_model": (
                "V9.7.2" if bool(row.get("v972_shadow_applied")) else None
            ),
            "research_challenger_projection": finite(row.get("strategy_projection")) if bool(row.get("v972_shadow_applied")) else None,
            "research_challenger_delta": finite(row.get("projection_delta_vs_m9")) if bool(row.get("v972_shadow_applied")) else None,
            "research_challenger_status": row.get("v972_shadow_status"),
            "v972_validation_mean_improvement": finite(row.get("v972_validation_mean_improvement")),
            "v972_validation_ci95_low": finite(row.get("v972_validation_ci95_low")),
            "v972_validation_ci95_high": finite(row.get("v972_validation_ci95_high")),
            "v972_validation_positive_folds": finite(row.get("v972_validation_positive_folds")),
            "v972_validation_folds": finite(row.get("v972_validation_folds")),
        }
    return out


def _offense_rows(league_id: str, season: int, canonical: pd.DataFrame, readiness: dict, challenger: dict[str, dict]) -> list[dict]:
    rows: list[dict] = []
    for src in canonical.to_dict("records"):
        pos = str(src.get("position_model") or "").upper()
        if pos not in OFFENSE:
            continue
        if not bool(src.get("current_relevant_player")):
            continue
        pmeta = (readiness.get("positions") or {}).get(pos) or {}
        key = _join_key(src)
        ch = challenger.get(key, {})
        projection = finite(src.get("fie_value_projection"))
        ppg = finite(src.get("fie_ppg"))
        row = {
            "schema": FINAL_BOARD_SCHEMA,
            "league_id": str(league_id),
            "season": int(season),
            "player_id": norm_id(src.get("canonical_player_id")) or norm_id(src.get("sleeper_id")),
            "canonical_player_id": norm_id(src.get("canonical_player_id")) or None,
            "sleeper_id": norm_id(src.get("sleeper_id")) or None,
            "name": src.get("full_name"),
            "team": src.get("current_team") or src.get("team"),
            "position": pos,
            "projection_scope": "SEASON",
            "model_selected": pmeta.get("selected_production_model") or "M9",
            "model_status": pmeta.get("decision"),
            "projection_source": src.get("m9_projection_source") or src.get("projection_source") or "FIE_M9",
            "projection_points": projection,
            "projection_ppg": ppg,
            "p10": finite(src.get("p10")),
            "p25": finite(src.get("p25")),
            "p50": finite(src.get("p50")),
            "p75": finite(src.get("p75")),
            "p90": finite(src.get("p90")),
            "position_rank": finite(src.get("fie_value_position_rank")),
            "overall_rank": None,
            "replacement_points": finite(src.get("replacement_points")),
            "vorp": finite(src.get("fie_vorp")),
            "adp": finite(src.get("market_adp")),
            "adp_key": src.get("market_adp_key") or (readiness.get("market") or {}).get("adp_key"),
            "market_position_rank": finite(src.get("market_position_rank")),
            "market_overall_rank": None,
            "rank_edge_position": finite(src.get("rank_edge")),
            "rank_edge_overall": None,
            "value_label": src.get("value_label"),
            "actionable_signal": bool(src.get("actionable_draft_signal")),
            "confidence": finite(src.get("confidence") or src.get("diagnostic_confidence")),
            "current_player_match": bool(src.get("current_player_match")),
            "current_active": bool(src.get("current_active")),
            "injury_status": src.get("injury_status"),
            "draft_relevant": bool(src.get("draft_relevant")),
            "within_draft_horizon": bool(src.get("within_draft_horizon")),
            "within_watchlist_horizon": bool(src.get("within_watchlist_horizon")),
            "adp_change_from_open": finite(src.get("adp_change_from_open")),
            "adp_change_7d": finite(src.get("adp_change_7d")),
            "adp_change_21d": finite(src.get("adp_change_21d")),
            "reason_codes": [],
            **ch,
        }
        if row["vorp"] is not None:
            row["reason_codes"].append("LEAGUE_SPECIFIC_VORP")
        if row["rank_edge_position"] is not None:
            row["reason_codes"].append("RELEVANT_UNIVERSE_RANK_EDGE")
        row["reason_codes"].append("M9_PRODUCTION_MODEL")
        if row["current_player_match"]:
            row["reason_codes"].append("CURRENT_PLAYER_MATCH")
        rows.append(row)

    # Overall rank and market overall rank are report fields derived from already
    # selected canonical league value / ADP.  They do not feed any app decision.
    comparable = [r for r in rows if r["projection_points"] is not None]
    for i, r in enumerate(sorted(comparable, key=lambda x: (-float(x["projection_points"]), str(x["name"]))), 1):
        r["overall_rank"] = i
    market = [r for r in rows if r["adp"] is not None]
    for i, r in enumerate(sorted(market, key=lambda x: (float(x["adp"]), str(x["name"]))), 1):
        r["market_overall_rank"] = i
    for r in rows:
        if r["overall_rank"] is not None and r["market_overall_rank"] is not None:
            r["rank_edge_overall"] = r["market_overall_rank"] - r["overall_rank"]
    return rows


def _first_value(row: dict, names: tuple[str, ...]) -> float | None:
    for name in names:
        x = finite(row.get(name))
        if x is not None:
            return x
    return None


def _special_rows(league_id: str, season: int, current: dict, readiness: dict) -> list[dict]:
    rows: list[dict] = []
    for src in current.get("players") or []:
        raw = str(src.get("position_model") or src.get("position") or "").upper()
        pos = "DST" if raw in {"DEF", "DST", "D/ST"} else ("K" if raw in {"K", "K/P"} else "")
        if not pos:
            continue
        pmeta = (readiness.get("positions") or {}).get(pos) or {}
        if pmeta.get("decision") == "NOT_APPLICABLE":
            continue
        projection = _first_value(src, ("decision_weekly_projection", "fie_weekly_projection", "sleeper_weekly_projection"))
        if projection is None:
            continue
        sid = norm_id(src.get("sleeper_id"))
        cid = norm_id(src.get("canonical_player_id"))
        name = src.get("full_name") or src.get("name") or (src.get("team") if pos == "DST" else None)
        if not name:
            continue
        rows.append({
            "schema": FINAL_BOARD_SCHEMA,
            "league_id": str(league_id), "season": int(season),
            "player_id": cid or sid or str(src.get("team") or name),
            "canonical_player_id": cid or None, "sleeper_id": sid or None,
            "name": name, "team": src.get("team"), "position": pos,
            "projection_scope": "WEEKLY_CURRENT",
            "model_selected": pmeta.get("selected_production_model"),
            "model_status": pmeta.get("decision"),
            "projection_source": "CURRENT_DEDICATED_SPECIALIST_ENGINE",
            "projection_points": projection,
            "projection_ppg": projection,
            "p10": _first_value(src, ("decision_weekly_p10", "weekly_p10", "p10")),
            "p25": _first_value(src, ("decision_weekly_p25", "weekly_p25", "p25")),
            "p50": _first_value(src, ("decision_weekly_p50", "weekly_p50", "p50")),
            "p75": _first_value(src, ("decision_weekly_p75", "weekly_p75", "p75")),
            "p90": _first_value(src, ("decision_weekly_p90", "weekly_p90", "p90")),
            "position_rank": None, "overall_rank": None,
            "replacement_points": None, "vorp": None,
            "adp": None, "adp_key": None, "market_position_rank": None,
            "market_overall_rank": None, "rank_edge_position": None, "rank_edge_overall": None,
            "value_label": "CURRENT_SPECIALIST", "actionable_signal": False,
            "confidence": _first_value(src, ("confidence", "decision_confidence")),
            "current_player_match": True, "current_active": bool(src.get("active", True)),
            "injury_status": src.get("injury_status"), "draft_relevant": False,
            "within_draft_horizon": False, "within_watchlist_horizon": False,
            "adp_change_from_open": None, "adp_change_7d": None, "adp_change_21d": None,
            "reason_codes": ["DEDICATED_SPECIAL_TEAMS_ENGINE", "EXACT_LEAGUE_SCORING"],
            "research_challenger_model": None, "research_challenger_projection": None,
            "research_challenger_delta": None, "research_challenger_status": None,
        })
    # Display order only; explicitly not a canonical cross-position/draft rank.
    for pos in ("DST", "K"):
        subset = [r for r in rows if r["position"] == pos]
        for rank, r in enumerate(sorted(subset, key=lambda x: (-float(x["projection_points"]), str(x["name"]))), 1):
            r["position_rank"] = rank
    return rows


def build_board(league_id: str, season: int, readiness: dict) -> tuple[pd.DataFrame, dict]:
    profile = load_profile(league_id)
    current = load_current_snapshot(current_path(league_id)) if current_path(league_id).is_file() else {}
    canonical, canonical_meta = _canonical_offense_value_board(league_id, season, profile, current)
    shadow = _read_csv(strategy_dir(league_id, season) / "league_value_board.csv")
    rows = _offense_rows(league_id, season, canonical, readiness, _challenger_map(shadow))
    rows.extend(_special_rows(league_id, season, current, readiness))
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values(["position", "position_rank", "name"], na_position="last").reset_index(drop=True)
    meta = {
        "schema": FINAL_BOARD_SCHEMA,
        "league_id": str(league_id),
        "season": int(season),
        "row_count": int(len(df)),
        "canonical_offense_value_source": "existing_fie_strategy_stack.build_league_value_board_on_M9",
        "challenger_source": "existing_strategy_shadow_join_only",
        "special_teams_scope": "weekly_current_existing_dedicated_engines",
        "adp_in_football_model": False,
        "automatic_promotion": False,
        "canonical_value_meta": json_safe(canonical_meta),
    }
    return df, meta


def compact_rankings(df: pd.DataFrame, meta: dict) -> dict:
    cols = [
        "player_id", "sleeper_id", "name", "team", "position", "projection_scope",
        "model_selected", "model_status", "projection_points", "projection_ppg",
        "p10", "p50", "p90", "position_rank", "overall_rank", "replacement_points",
        "vorp", "adp", "market_position_rank", "market_overall_rank",
        "rank_edge_position", "rank_edge_overall", "value_label", "confidence",
        "draft_relevant", "within_watchlist_horizon", "reason_codes",
        "research_challenger_model", "research_challenger_projection",
        "research_challenger_delta", "research_challenger_status",
    ]
    players = []
    for row in df.to_dict("records"):
        players.append(json_safe({k: row.get(k) for k in cols}))
    return {
        "schema": "fie-final-league-rankings-v1",
        "league_id": meta["league_id"], "season": meta["season"],
        "canonical_rank_source": meta["canonical_offense_value_source"],
        "automatic_promotion": False,
        "players": players,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league-id", required=True)
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--readiness", default="")
    ap.add_argument("--output-dir", default="")
    a = ap.parse_args(argv)
    out = Path(a.output_dir) if a.output_dir else pipeline_dir(a.league_id, a.season)
    readiness_path = Path(a.readiness) if a.readiness else out / "readiness.json"
    readiness = load_json(readiness_path, {})
    if not readiness:
        raise SystemExit(f"readiness required: {readiness_path}")
    df, meta = build_board(a.league_id, a.season, readiness)
    out.mkdir(parents=True, exist_ok=True)
    df.to_csv(out / "final_player_board.csv", index=False)
    write_json(out / "board-meta.json", meta)
    write_json(out / "rankings.json", compact_rankings(df, meta), pretty=False)
    print(json.dumps({"league_id": a.league_id, "rows": len(df), "positions": df.position.value_counts().to_dict() if not df.empty else {}}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
